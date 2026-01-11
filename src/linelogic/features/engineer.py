"""
Feature Engineering Pipeline for NBA Win Probability Model

Transforms raw BALLDONTLIE game data into ML-ready features including:
- Elo ratings
- Rolling win rates
- Point differentials
- Rest days
- Home/away indicators
- Head-to-head records
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from linelogic.models.elo import EloRating
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature engineering pipeline for NBA games.

    Processes historical games chronologically to extract features
    without look-ahead bias.
    """

    def __init__(
        self,
        advanced_metrics_df: Optional[pd.DataFrame] = None,
        player_stats_df: Optional[pd.DataFrame] = None,
        team_avgs_df: Optional[pd.DataFrame] = None,
        injuries_df: Optional[pd.DataFrame] = None,
        odds_df: Optional[pd.DataFrame] = None,
    ):
        self.elo = EloRating()
        self.team_game_history: Dict[str, List[Dict]] = defaultdict(list)
        # Precompute lookup for team-season advanced metrics if provided
        self.advanced_lookup = {}
        if advanced_metrics_df is not None and not advanced_metrics_df.empty:
            for _, row in advanced_metrics_df.iterrows():
                key = (int(row["season"]), str(row["team"]))
                self.advanced_lookup[key] = {
                    "PER": float(row.get("team_weighted_PER", 0.0)),
                    "BPM": float(row.get("team_weighted_BPM", 0.0)),
                    "WS48": float(row.get("team_weighted_WS48", 0.0)),
                }
            logger.info(
                f"FeatureEngineer: Loaded advanced metrics for {len(self.advanced_lookup)} team-season entries."
            )

        # Team season averages lookup (net rating, pace, shot profile)
        self.team_avgs_lookup = {}
        if team_avgs_df is not None and not team_avgs_df.empty:
            for _, row in team_avgs_df.iterrows():
                key = (int(row["season"]), str(row["team"]))
                self.team_avgs_lookup[key] = {
                    "net_rating": float(row.get("net_rating", 0.0)),
                    "pace": float(row.get("pace", 0.0)),
                    "off_rating": float(row.get("off_rating", 0.0)),
                    "def_rating": float(row.get("def_rating", 0.0)),
                    "off_3pa_rate": float(row.get("off_3pa_rate", 0.0)),
                    "def_opp_3pa_rate": float(row.get("def_opp_3pa_rate", 0.0)),
                }
            logger.info(
                f"FeatureEngineer: Loaded team season averages for {len(self.team_avgs_lookup)} team-season entries."
            )

        # Player stats lookups: lineups per game and expected top players per team-season
        self.lineup_lookup: Dict[Tuple[pd.Timestamp, str], List[str]] = {}
        self.expected_top_players: Dict[Tuple[int, str], List[str]] = {}
        self.prev_lineup: Dict[str, List[str]] = {}
        if player_stats_df is not None and not player_stats_df.empty:
            starters = player_stats_df[player_stats_df["starter"] == 1]
            for (dt, team), gdf in starters.groupby(["date", "team"]):
                self.lineup_lookup[(pd.to_datetime(dt), str(team))] = list(
                    gdf["player"].astype(str)
                )

            agg = player_stats_df.groupby(["season", "team", "player"], as_index=False)[
                "minutes"
            ].sum()
            for (season, team), gdf in agg.groupby(["season", "team"]):
                top = (
                    gdf.sort_values("minutes", ascending=False)["player"]
                    .astype(str)
                    .tolist()
                )
                self.expected_top_players[(int(season), str(team))] = top[:3]
            logger.info(
                f"FeatureEngineer: Loaded lineups for {len(self.lineup_lookup)} team-game entries and expected top players for {len(self.expected_top_players)} team-seasons."
            )

        # Injuries lookup
        self.injuries_lookup: Dict[Tuple[pd.Timestamp, str], Dict[str, float]] = {}
        if injuries_df is not None and not injuries_df.empty:
            injuries_df = injuries_df.dropna(subset=["date", "team"])
            for _, row in injuries_df.iterrows():
                key = (pd.to_datetime(row["date"]), str(row["team"]))
                self.injuries_lookup[key] = {
                    "injured_count": float(row.get("injured_count", 0) or 0),
                    "injured_minutes_lost": float(
                        row.get("injured_minutes_lost", 0) or 0.0
                    ),
                }
            logger.info(
                f"FeatureEngineer: Loaded injuries for {len(self.injuries_lookup)} team-date entries."
            )

        # Odds lookup (by date + matchup)
        self.odds_lookup: Dict[Tuple[pd.Timestamp, str, str], Dict[str, float]] = {}
        if odds_df is not None and not odds_df.empty:
            odds_df = odds_df.dropna(subset=["date", "home_team", "away_team"])
            for _, row in odds_df.iterrows():
                key = (
                    pd.to_datetime(row["date"]),
                    str(row["home_team"]),
                    str(row["away_team"]),
                )
                self.odds_lookup[key] = {
                    "implied_home_prob": float(
                        row.get("implied_home_prob", 0.0) or 0.0
                    ),
                    "spread_home": float(row.get("spread_home", 0.0) or 0.0),
                    "total": float(row.get("total", 0.0) or 0.0),
                }
            logger.info(
                f"FeatureEngineer: Loaded odds for {len(self.odds_lookup)} matchups."
            )

    def engineer_features(
        self,
        games_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Transform raw game data into feature matrix.

        Args:
            games_df: DataFrame with columns [date, home_team, away_team,
                     home_score, away_score, home_win]

        Returns:
            DataFrame with engineered features for each game
        """
        # Sort by date to avoid look-ahead bias
        games_df = games_df.sort_values("date").reset_index(drop=True)

        features_list = []

        for idx, game in games_df.iterrows():
            # Extract features BEFORE updating state
            features = self._extract_game_features(game)
            features_list.append(features)

            # Update state AFTER feature extraction
            self._update_state(game)

        return pd.DataFrame(features_list)

    def _extract_game_features(self, game: pd.Series) -> Dict:
        """Extract features for a single game."""
        home_team = game["home_team"]
        away_team = game["away_team"]
        game_date = pd.to_datetime(game["date"])
        season = self._season_from_date(game_date)

        # For future predictions, use most recent season available in our data
        # (e.g., for 2026 predictions, use 2024 stats if that's the latest)
        if self.team_avgs_lookup:
            available_seasons = set(k[0] for k in self.team_avgs_lookup.keys())
            if available_seasons:
                most_recent = max(available_seasons)
                fallback_season = most_recent if season > most_recent else season
            else:
                fallback_season = season
        else:
            fallback_season = season

        # Advanced metrics lookups with fallback
        home_adv = self.advanced_lookup.get(
            (season, home_team),
            self.advanced_lookup.get(
                (fallback_season, home_team), {"PER": 0.0, "BPM": 0.0, "WS48": 0.0}
            ),
        )
        away_adv = self.advanced_lookup.get(
            (season, away_team),
            self.advanced_lookup.get(
                (fallback_season, away_team), {"PER": 0.0, "BPM": 0.0, "WS48": 0.0}
            ),
        )

        # Team season averages (net rating, pace, shot profile) with fallback
        default_avgs = {
            "net_rating": 0.0,
            "pace": 0.0,
            "off_rating": 0.0,
            "def_rating": 0.0,
            "off_3pa_rate": 0.0,
            "def_opp_3pa_rate": 0.0,
        }
        home_avgs = self.team_avgs_lookup.get(
            (season, home_team),
            self.team_avgs_lookup.get((fallback_season, home_team), default_avgs),
        )
        away_avgs = self.team_avgs_lookup.get(
            (season, away_team),
            self.team_avgs_lookup.get((fallback_season, away_team), default_avgs),
        )

        # Injuries
        home_inj = self._get_injury_features(game_date, home_team)
        away_inj = self._get_injury_features(game_date, away_team)

        # Odds
        odds = self._get_odds_features(game_date, home_team, away_team)

        # Lineup continuity and key player availability
        home_lineup = self.lineup_lookup.get((game_date, home_team), [])
        away_lineup = self.lineup_lookup.get((game_date, away_team), [])
        prev_home = set(self.prev_lineup.get(home_team, []))
        prev_away = set(self.prev_lineup.get(away_team, []))
        cont_home = len(prev_home.intersection(set(home_lineup))) if prev_home else 0
        cont_away = len(prev_away.intersection(set(away_lineup))) if prev_away else 0

        exp_home = set(self.expected_top_players.get((season, home_team), []))
        exp_away = set(self.expected_top_players.get((season, away_team), []))
        home_key_out = max(0, len(exp_home - set(home_lineup))) if home_lineup else 0
        away_key_out = max(0, len(exp_away - set(away_lineup))) if away_lineup else 0

        features = {
            # Identifiers
            "date": game["date"],
            "home_team": home_team,
            "away_team": away_team,
            # Target
            "home_win": game["home_win"],
            # Elo features
            "home_elo": self.elo.get_rating(home_team),
            "away_elo": self.elo.get_rating(away_team),
            "elo_diff": self.elo.get_rating(home_team) - self.elo.get_rating(away_team),
            # Home court
            "is_home": 1,
            # Win rates
            "home_win_rate_L10": self._get_win_rate(home_team, 10),
            "away_win_rate_L10": self._get_win_rate(away_team, 10),
            # Point differentials
            "home_pt_diff_L10": self._get_point_diff(home_team, 10),
            "away_pt_diff_L10": self._get_point_diff(away_team, 10),
            # Rest days
            "home_rest_days": self._get_rest_days(home_team, game_date),
            "away_rest_days": self._get_rest_days(away_team, game_date),
            # Back-to-back
            "home_b2b": 1 if self._get_rest_days(home_team, game_date) == 0 else 0,
            "away_b2b": 1 if self._get_rest_days(away_team, game_date) == 0 else 0,
            # Head-to-head
            "h2h_home_wins": self._get_h2h_wins(home_team, away_team),
            # Recent form (streak)
            "home_streak": self._get_streak(home_team),
            "away_streak": self._get_streak(away_team),
            # Lineup continuity (overlap count vs previous starters, 0-5)
            "home_lineup_cont_overlap": cont_home,
            "away_lineup_cont_overlap": cont_away,
            # Key player availability (count of expected top-3 missing)
            "home_key_out_count": home_key_out,
            "away_key_out_count": away_key_out,
            # Injuries
            "home_injured_count": home_inj["injured_count"],
            "away_injured_count": away_inj["injured_count"],
            "home_injured_minutes_lost": home_inj["injured_minutes_lost"],
            "away_injured_minutes_lost": away_inj["injured_minutes_lost"],
            # Player-derived team advanced metrics (minutes-weighted season aggregates)
            "home_weighted_PER": home_adv["PER"],
            "away_weighted_PER": away_adv["PER"],
            "home_weighted_BPM": home_adv["BPM"],
            "away_weighted_BPM": away_adv["BPM"],
            "home_weighted_WS48": home_adv["WS48"],
            "away_weighted_WS48": away_adv["WS48"],
            # Differences
            "per_diff": home_adv["PER"] - away_adv["PER"],
            "bpm_diff": home_adv["BPM"] - away_adv["BPM"],
            "ws48_diff": home_adv["WS48"] - away_adv["WS48"],
            # Team season averages (net rating, pace, shot profile)
            "home_net_rating": home_avgs["net_rating"],
            "away_net_rating": away_avgs["net_rating"],
            "net_rating_diff": home_avgs["net_rating"] - away_avgs["net_rating"],
            "home_pace": home_avgs["pace"],
            "away_pace": away_avgs["pace"],
            "pace_diff": home_avgs["pace"] - away_avgs["pace"],
            "home_off_3pa_rate": home_avgs["off_3pa_rate"],
            "away_off_3pa_rate": away_avgs["off_3pa_rate"],
            "off_3pa_rate_diff": home_avgs["off_3pa_rate"] - away_avgs["off_3pa_rate"],
            "home_def_opp_3pa_rate": home_avgs["def_opp_3pa_rate"],
            "away_def_opp_3pa_rate": away_avgs["def_opp_3pa_rate"],
            "def_opp_3pa_rate_diff": home_avgs["def_opp_3pa_rate"]
            - away_avgs["def_opp_3pa_rate"],
            # Odds (market priors)
            "implied_home_prob": odds["implied_home_prob"],
            "spread_home": odds["spread_home"],
            "total": odds["total"],
        }

        return features

    def _update_state(self, game: pd.Series) -> None:
        """Update internal state after processing a game."""
        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_score"]
        away_score = game["away_score"]
        game_date = game["date"]

        # Update Elo
        self.elo.update_ratings(home_team, away_team, home_score, away_score)

        # Store game in history
        game_record = {
            "date": game_date,
            "opponent": away_team,
            "score": home_score,
            "opp_score": away_score,
            "win": home_score > away_score,
            "home": True,
        }
        self.team_game_history[home_team].append(game_record)

        away_record = {
            "date": game_date,
            "opponent": home_team,
            "score": away_score,
            "opp_score": home_score,
            "win": away_score > home_score,
            "home": False,
        }
        self.team_game_history[away_team].append(away_record)

        # Update previous lineup trackers
        dt = pd.to_datetime(game_date)
        if (dt, home_team) in self.lineup_lookup:
            self.prev_lineup[home_team] = self.lineup_lookup[(dt, home_team)]
        if (dt, away_team) in self.lineup_lookup:
            self.prev_lineup[away_team] = self.lineup_lookup[(dt, away_team)]

    def _get_win_rate(self, team: str, n_games: int) -> float:
        """Get win rate over last N games."""
        history = self.team_game_history.get(team, [])
        if len(history) == 0:
            return 0.5  # Prior for new teams

        recent = history[-n_games:]
        wins = sum(g["win"] for g in recent)
        return wins / len(recent)

    def _get_point_diff(self, team: str, n_games: int) -> float:
        """Get average point differential over last N games."""
        history = self.team_game_history.get(team, [])
        if len(history) == 0:
            return 0.0

        recent = history[-n_games:]
        diffs = [g["score"] - g["opp_score"] for g in recent]
        return np.mean(diffs)

    def _get_rest_days(self, team: str, game_date: datetime) -> int:
        """Get days since last game."""
        history = self.team_game_history.get(team, [])
        if len(history) == 0:
            return 3  # Assume fully rested

        last_game_date = pd.to_datetime(history[-1]["date"])
        delta = (pd.to_datetime(game_date) - last_game_date).days - 1
        return max(0, min(delta, 7))  # Cap at 7 days

    def _get_injury_features(self, date: pd.Timestamp, team: str) -> Dict[str, float]:
        inj = self.injuries_lookup.get((pd.to_datetime(date), team))
        if inj is None:
            return {
                "injured_count": 0.0,
                "injured_minutes_lost": 0.0,
            }
        return inj

    def _get_odds_features(
        self, date: pd.Timestamp, home_team: str, away_team: str
    ) -> Dict[str, float]:
        odds = self.odds_lookup.get((pd.to_datetime(date), home_team, away_team))
        if odds is None:
            return {
                "implied_home_prob": 0.0,
                "spread_home": 0.0,
                "total": 0.0,
            }
        return odds

    def _get_h2h_wins(self, home_team: str, away_team: str) -> int:
        """Get home team wins vs away team this season."""
        history = self.team_game_history.get(home_team, [])
        h2h_games = [g for g in history if g["opponent"] == away_team]
        return sum(g["win"] for g in h2h_games)

    def _get_streak(self, team: str) -> int:
        """
        Get current win/loss streak.
        Positive = win streak, negative = loss streak.
        """
        history = self.team_game_history.get(team, [])
        if len(history) == 0:
            return 0

        streak = 0
        last_result = history[-1]["win"]

        for game in reversed(history):
            if game["win"] == last_result:
                streak += 1 if last_result else -1
            else:
                break

        return streak

    @staticmethod
    def _season_from_date(d: pd.Timestamp) -> int:
        """Map game date to NBA season label (year of season start).

        Example: 2023-10 → 2023 season; 2024-03 → 2023 season.
        """
        month = int(d.month)
        year = int(d.year)
        # NBA seasons start around Oct; anything from Aug-Dec belongs to current year
        # Jan-Jul belongs to previous year's season label
        if month >= 8:  # Aug-Dec
            return year
        else:  # Jan-Jul
            return year - 1
