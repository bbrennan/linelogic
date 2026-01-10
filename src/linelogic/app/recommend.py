"""
Recommendation engine: generates recommendations for a given date using available data.
"""

import datetime
import json

from linelogic.config.settings import settings
from linelogic.data.providers.balldontlie import BalldontlieProvider
from linelogic.data.providers.odds import TheOddsAPIProvider
from linelogic.odds.math import american_to_implied_prob
from linelogic.portfolio.bankroll import calculate_stake_with_caps
from linelogic.storage.sqlite import get_connection, init_db


class RecommendationEngine:
    """
    Generate recommendations for a given date.

    Fetches games, market odds, generates model probabilities, computes edge/stake,
    writes to SQLite for paper trading or audit.
    """

    def __init__(self):
        """Initialize engine with providers and DB."""
        self.balldontlie = BalldontlieProvider()
        self.odds_api = TheOddsAPIProvider()
        init_db(settings.database_path)

    def stub_model_probability(
        self, _home_team: str, _away_team: str, **_context: dict
    ) -> float:
        """
        Stub model: return 52% (small edge for testing).

        In v2+, replace with trained GLM/XGBoost using features logged here.

        Args:
            _home_team: Home team name
            _away_team: Away team name
            **_context: Extra context (unused for now)

        Returns:
            Probability (0.0 to 1.0)
        """
        # Placeholder: 52% (2% edge vs fair 50% odds) to generate some picks for testing
        return 0.52

    def fetch_real_moneyline_odds(self, date_str: str) -> dict:
        """
        Fetch real opening moneyline odds from TheOddsAPI.

        Matches games by date (commence_time) and team names.

        Args:
            date_str: Date in YYYY-MM-DD format (to match games)

        Returns:
            Dict mapping {home_team_name -> home_odds, away_team_name -> away_odds}
            Falls back to stub 50/50 if API errors.
        """
        try:
            odds_data = self.odds_api.get_game_odds(
                sport="basketball_nba",
                markets="h2h",  # head-to-head (moneyline)
                oddsFormat="american",
            )

            odds_map = {}

            # Build a lookup map: (home_short_name, away_short_name) -> odds
            for event in odds_data:
                commence_time = event.get("commence_time", "")
                # Check if game is on target date (e.g., 2026-01-11)
                if not commence_time.startswith(date_str):
                    continue

                bookmakers = event.get("bookmakers", [])

                # Use first sportsbook's opening odds (usually most accurate)
                if bookmakers:
                    markets = bookmakers[0].get("markets", [])
                    for market in markets:
                        if market.get("key") == "h2h":
                            outcomes = market.get("outcomes", [])
                            for outcome in outcomes:
                                team = outcome.get("name")
                                odds = outcome.get("price")

                                if team and odds:
                                    try:
                                        implied_prob = american_to_implied_prob(odds)
                                        odds_map[team] = {
                                            "implied_prob": implied_prob,
                                            "american_odds": odds,
                                            "source": "TheOddsAPI",
                                            "sportsbook": bookmakers[0].get(
                                                "title", "Unknown"
                                            ),
                                        }
                                    except Exception:  # noqa: BLE001
                                        pass

            return odds_map

        except Exception:  # noqa: BLE001
            # Fall back to stub 50/50 if TheOddsAPI fails
            return {}

    def recommend_date(self, date_str: str) -> dict:
        """
        Generate recommendations for a date (paper-only if mode=paper).

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Dict with keys: count, total_staked, avg_edge, recommendations (list)

        Raises:
            ValueError: If mode is 'live' (not supported in v1)
        """
        if settings.mode != "paper":
            raise ValueError(f"Mode '{settings.mode}' not supported; use mode=paper")

        # Fetch games for the date
        games = self.balldontlie.get_games(date_str)

        if not games:
            return {
                "date": date_str,
                "count": 0,
                "total_staked": 0.0,
                "avg_edge": 0.0,
                "recommendations": [],
            }

        # Fetch real opening odds from TheOddsAPI
        odds_map = self.fetch_real_moneyline_odds(date_str)

        recommendations = []
        total_stake = 0.0
        total_edge = 0.0

        conn = get_connection(settings.database_path)
        cursor = conn.cursor()

        print(f"[DEBUG] Fetched {len(games)} games for {date_str}")
        print(f"[DEBUG] Found odds for {len(odds_map)} teams from TheOddsAPI")

        for game in games:
            game_id = game.get("id")
            home_team = game.get("home_team", {}).get("name", "Unknown")
            away_team = game.get("away_team", {}).get("name", "Unknown")

            # Get real odds or fall back to stub 50/50
            home_odds = odds_map.get(home_team, {})
            # Try fuzzy match if exact match fails (e.g., "Magic" vs "Orlando Magic")
            if not home_odds:
                for odds_team, odds_data in odds_map.items():
                    if home_team.lower() in odds_team.lower():
                        home_odds = odds_data
                        break

            away_odds = odds_map.get(away_team, {})
            if not away_odds:
                for odds_team, odds_data in odds_map.items():
                    if away_team.lower() in odds_team.lower():
                        away_odds = odds_data
                        break

            home_implied = home_odds.get("implied_prob", 0.50)
            away_implied = away_odds.get("implied_prob", 0.50)

            # Normalize if odds don't sum to 1 (overround adjustment)
            total_implied = home_implied + away_implied
            if total_implied > 0:
                home_fair = home_implied / total_implied
                away_fair = away_implied / total_implied
            else:
                home_fair = 0.50
                away_fair = 0.50

            # Generate model probabilities (stub)
            model_home = self.stub_model_probability(home_team, away_team)
            model_away = 1 - model_home

            # Compute edge
            home_edge = model_home - home_fair
            away_edge = model_away - away_fair

            # Only recommend if edge > 1%
            recommendations_for_game = []

            if home_edge > 0.01:
                # Use real decimal odds or estimate from implied probability
                if home_odds:
                    american = home_odds.get("american_odds", -110)
                    try:
                        decimal_odds = (
                            (american / 100.0) + 1
                            if american > 0
                            else (100 / abs(american)) + 1
                        )
                    except Exception:  # noqa: BLE001
                        decimal_odds = 2.0
                else:
                    decimal_odds = 2.0  # stub even odds

                result = calculate_stake_with_caps(
                    prob_win=model_home,
                    odds_decimal=decimal_odds,
                    bankroll=1000.0,
                    kelly_fraction_value=0.25,
                )
                stake = result["stake_dollars"]
                total_stake += stake
                total_edge += home_edge

                rec = {
                    "game_id": game_id,
                    "selection": f"{home_team} (Home)",
                    "model_prob": model_home,
                    "market_prob": home_implied,
                    "edge": home_edge,
                    "stake": stake,
                    "odds": home_odds,
                }
                recommendations_for_game.append(rec)

            if away_edge > 0.01:
                if away_odds:
                    american = away_odds.get("american_odds", -110)
                    try:
                        decimal_odds = (
                            (american / 100.0) + 1
                            if american > 0
                            else (100 / abs(american)) + 1
                        )
                    except Exception:  # noqa: BLE001
                        decimal_odds = 2.0
                else:
                    decimal_odds = 2.0

                result = calculate_stake_with_caps(
                    prob_win=model_away,
                    odds_decimal=decimal_odds,
                    bankroll=1000.0,
                    kelly_fraction_value=0.25,
                )
                stake = result["stake_dollars"]
                total_stake += stake
                total_edge += away_edge

                rec = {
                    "game_id": game_id,
                    "selection": f"{away_team} (Away)",
                    "model_prob": model_away,
                    "market_prob": away_implied,
                    "edge": away_edge,
                    "stake": stake,
                    "odds": away_odds,
                }
                recommendations_for_game.append(rec)

            # Write to DB
            for rec in recommendations_for_game:
                cursor.execute(
                    """
                    INSERT INTO recommendations
                    (created_at, sport, game_id, market, selection, model_prob,
                     market_prob, edge, stake_suggested, kelly_fraction, bankroll_at_time, notes, model_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.datetime.now().isoformat(),
                        "nba",
                        rec["game_id"],
                        "moneyline",
                        rec["selection"],
                        rec["model_prob"],
                        rec["market_prob"],
                        rec["edge"],
                        rec["stake"],
                        0.25,
                        1000.0,
                        f"POC stub model; mode={settings.mode}; source={rec['odds'].get('source', 'stub')}",
                        "0.1.0-stub",
                    ),
                )

                # Store odds snapshot if available
                if rec["odds"]:
                    rec_id = cursor.lastrowid
                    cursor.execute(
                        """
                        INSERT INTO odds_snapshots
                        (recommendation_id, source, captured_at, line, odds_american, odds_decimal, raw_payload_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rec_id,
                            rec["odds"].get("source", "TheOddsAPI"),
                            datetime.datetime.now().isoformat(),
                            rec["market_prob"],
                            rec["odds"].get("american_odds", -110),
                            (
                                (rec["odds"].get("american_odds", -110) / 100.0) + 1
                                if rec["odds"].get("american_odds", -110) > 0
                                else (100 / abs(rec["odds"].get("american_odds", -110)))
                                + 1
                            ),
                            json.dumps(rec["odds"]),
                        ),
                    )

            recommendations.extend(recommendations_for_game)

        conn.commit()
        conn.close()

        avg_edge = (total_edge / len(recommendations)) if recommendations else 0.0

        return {
            "date": date_str,
            "count": len(recommendations),
            "total_staked": total_stake,
            "avg_edge": avg_edge,
            "recommendations": recommendations,
        }
