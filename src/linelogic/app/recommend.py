"""
Recommendation engine: generates recommendations for a given date using available data.
"""

import datetime

from linelogic.config.settings import settings
from linelogic.data.providers.balldontlie import BalldontlieProvider
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

        recommendations = []
        total_stake = 0.0
        total_edge = 0.0

        conn = get_connection(settings.database_path)
        cursor = conn.cursor()

        print(f"[DEBUG] Fetched {len(games)} games for {date_str}")

        for game in games:
            game_id = game.get("id")
            home_team = game.get("home_team", {}).get("name", "Unknown")
            away_team = game.get("away_team", {}).get("name", "Unknown")

            # Stub: use fair odds (50/50)
            home_implied = 0.50
            away_implied = 0.50
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
                result = calculate_stake_with_caps(
                    prob_win=model_home,
                    odds_decimal=2.0,  # stub: even odds
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
                }
                recommendations_for_game.append(rec)

            if away_edge > 0.01:
                result = calculate_stake_with_caps(
                    prob_win=model_away,
                    odds_decimal=2.0,
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
                        f"POC stub model; mode={settings.mode}",
                        "0.1.0-stub",
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
