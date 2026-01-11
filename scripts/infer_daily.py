#!/usr/bin/env python3
"""
Daily inference script for POC deployment (Jan 11, 2026+).
Scores upcoming NBA games and outputs predictions with confidence tiers.

Usage:
  python scripts/infer_daily.py [--date YYYY-MM-DD] [--output OUTPUT.csv] [--verbose]

Example:
  python scripts/infer_daily.py --date 2026-01-11 --output predictions_2026-01-11.csv
"""

import argparse
import json
import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from linelogic.data.odds_cache import load_odds_cache
from linelogic.data.player_injuries_cache import load_player_injuries_cache
from linelogic.features.engineer import FeatureEngineer
from linelogic.data.providers.balldontlie import BalldontlieProvider

# Team abbreviation to full name mapping (API uses abbr, cache uses full names)
TEAM_ABBR_TO_FULL = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "LA Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards",
}


class DailyInferenceEngine:
    """Loads model, scores games, outputs with confidence tiers."""

    def __init__(self, model_version="v1.0.0", verbose=False):
        self.verbose = verbose
        self.model_path = Path(".linelogic") / f"nba_model_{model_version}.pkl"
        self.metadata_path = (
            Path(".linelogic") / f"nba_model_{model_version}_metadata.json"
        )

        # Load model and metadata
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        with open(self.model_path, "rb") as f:
            self.model_obj = pickle.load(f)
            self.model = self.model_obj["model"]
            self.scaler = self.model_obj["scaler"]

        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)

        self.feature_names = self.metadata["features_selected"]
        self.training_date_min = self.metadata.get("data_min_date", "2024-01-01")

        if self.verbose:
            print(f"✓ Loaded model: {self.model_path}")
            print(f"✓ Features: {len(self.feature_names)} selected")
            print(f"✓ Training data window: {self.training_date_min} onward")

    def assign_confidence_tier(self, row):
        """
        Assign confidence tier based on season, rest, and team.

        TIER 1 (HIGH CONFIDENCE):
          - 2024 2-3 days rest
          - 2024 4+ days rest
          - 2025 4+ days rest

        TIER 2 (MEDIUM-HIGH):
          - 2025 2-3 days rest

        TIER 4 (LOW):
          - Any 1-day rest

        TIER 3 (MEDIUM): everything else
        """
        season = row.get("season", 2025)
        rest_bucket = row.get("rest_bucket", "2-3 days")

        if rest_bucket == "1-day":
            return "TIER 4 (CAUTION)"
        elif season == 2024 and rest_bucket == "2-3 days":
            return "TIER 1 (HIGH CONFIDENCE)"
        elif season == 2024 and rest_bucket == "4+ days":
            return "TIER 1 (HIGH CONFIDENCE)"
        elif season == 2025 and rest_bucket == "4+ days":
            return "TIER 1 (HIGH CONFIDENCE)"
        elif season == 2025 and rest_bucket == "2-3 days":
            return "TIER 2 (MEDIUM-HIGH)"
        else:
            return "TIER 3 (MEDIUM)"

    def estimate_rest_days(self, date, home_team, team_game_dates):
        """Estimate rest days for home team."""
        team_dates = team_game_dates.get(home_team, [])
        if not team_dates:
            return 3  # Default to 3 days

        last_game_date = max([d for d in team_dates if d < date], default=None)
        if last_game_date is None:
            return 3

        rest_days = (date - last_game_date).days
        return rest_days

    def bucket_rest(self, days):
        """Bucket rest days."""
        if days <= 0:
            return "B2B"
        if days == 1:
            return "1-day"
        if days <= 3:
            return "2-3 days"
        return "4+ days"

    def score_games(self, games_df, engineer):
        """Score a dataframe of games."""
        if games_df.empty:
            return pd.DataFrame()

        try:
            # For inference, we extract features one game at a time WITHOUT updating state
            # (state updates require actual results which we don't have for upcoming games)
            predictions = []

            for idx, row in games_df.iterrows():
                try:
                    # Extract features for this single game (no state update)
                    features = engineer._extract_game_features(row)

                    # Extract features in correct order
                    X = np.array(
                        [features.get(f, 0) for f in self.feature_names]
                    ).reshape(1, -1)

                    # Scale
                    X_scaled = self.scaler.transform(X)

                    # Predict
                    pred_prob = self.model.predict_proba(X_scaled)[0, 1]  # P(home_win)

                    # Assign confidence tier
                    tier = self.assign_confidence_tier(row)

                    # Recommendation
                    if "TIER 1" in tier:
                        recommendation = (
                            "USE MODEL"
                            if pred_prob >= 0.55
                            else "USE MODEL (slight away edge)"
                        )
                    elif "TIER 2" in tier:
                        recommendation = "USE WITH VALIDATION"
                    else:
                        recommendation = "CROSS-CHECK EXTERNALLY"

                    predictions.append(
                        {
                            "date": row["date"],
                            "home_team": row["home_team"],
                            "away_team": row["away_team"],
                            "pred_home_win_prob": round(pred_prob, 4),
                            "pred_away_win_prob": round(1 - pred_prob, 4),
                            "home_team_rest_days": row.get("home_rest_days", 0),
                            "away_team_rest_days": row.get("away_rest_days", 0),
                            "confidence_tier": tier,
                            "recommendation": recommendation,
                        }
                    )
                except Exception as e:
                    if self.verbose:
                        print(
                            f"Warning: Could not score {row['home_team']} vs {row['away_team']}: {e}"
                        )
                    predictions.append(
                        {
                            "date": row["date"],
                            "home_team": row["home_team"],
                            "away_team": row["away_team"],
                            "pred_home_win_prob": np.nan,
                            "pred_away_win_prob": np.nan,
                            "home_team_rest_days": row.get("home_rest_days", 0),
                            "away_team_rest_days": row.get("away_rest_days", 0),
                            "confidence_tier": "ERROR",
                            "recommendation": "SKIP - Feature Error",
                        }
                    )

            return pd.DataFrame(predictions)

        except Exception as e:
            if self.verbose:
                print(f"Error scoring games: {e}")
                import traceback

                traceback.print_exc()
            return pd.DataFrame()

    def run(self, date=None, output_csv=None):
        """
        Main inference pipeline.

        Args:
            date (str or datetime): Date to fetch games for (default: today)
            output_csv (str): Path to save predictions CSV

        Returns:
            DataFrame of predictions
        """
        # Parse date
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")

        if self.verbose:
            print(f"\n{'='*80}")
            print(f"DAILY INFERENCE - {date.date()}")
            print(f"{'='*80}\n")

        # Load cache for team game dates (rest estimation)
        cache_path = Path(".linelogic/games_cache.csv")
        if cache_path.exists():
            cache_df = pd.read_csv(cache_path)
            cache_df["date"] = pd.to_datetime(cache_df["date"])

            # Build team game dates for rest estimation
            team_game_dates = {}
            for team in pd.concat(
                [cache_df["home_team"], cache_df["away_team"]]
            ).unique():
                team_game_dates[team] = sorted(
                    cache_df[cache_df["home_team"] == team]["date"].tolist()
                    + cache_df[cache_df["away_team"] == team]["date"].tolist()
                )
        else:
            team_game_dates = {}

        # Load injuries and odds (currently empty, but framework ready)
        injuries_df = load_player_injuries_cache()
        odds_df = load_odds_cache()

        # Load team stats caches for feature engineering
        team_avgs_path = Path(".linelogic/team_season_avgs.csv")
        adv_metrics_path = Path(".linelogic/players_advanced_metrics.csv")
        player_stats_path = Path(".linelogic/player_stats_cache.csv")

        team_avgs_df = (
            pd.read_csv(team_avgs_path) if team_avgs_path.exists() else pd.DataFrame()
        )
        adv_metrics_df = (
            pd.read_csv(adv_metrics_path)
            if adv_metrics_path.exists()
            else pd.DataFrame()
        )
        player_stats_df = (
            pd.read_csv(player_stats_path)
            if player_stats_path.exists()
            else pd.DataFrame()
        )

        if self.verbose and not team_avgs_df.empty:
            print(f"Loaded team avgs: {len(team_avgs_df)} rows")
            print(f"Loaded advanced metrics: {len(adv_metrics_df)} rows")
            print(f"Loaded player stats: {len(player_stats_df)} rows")

        # Initialize feature engineer with all cached data
        engineer = FeatureEngineer(
            advanced_metrics_df=adv_metrics_df,
            player_stats_df=player_stats_df,
            team_avgs_df=team_avgs_df,
            injuries_df=injuries_df,
            odds_df=odds_df,
        )

        # Fetch games for this date from BALLDONTLIE
        if self.verbose:
            print("Fetching games from BALLDONTLIE API...")

        api = BalldontlieProvider()
        try:
            # Convert datetime to string format YYYY-MM-DD for API
            date_str = date.strftime("%Y-%m-%d")
            games = api.get_games(date_str)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not fetch from API: {e}")
            games = []

        if not games:
            if self.verbose:
                print(f"No games found for {date.date()}")
            return pd.DataFrame()

        # Convert to dataframe - extract team abbreviations from nested dicts
        games_data = []
        for game in games:
            games_data.append(
                {
                    "id": game["id"],
                    "date": game["date"],
                    "home_team": game["home_team"]["abbreviation"],
                    "away_team": game["away_team"]["abbreviation"],
                    "status": game["status"],
                    # Add dummy values for feature engineering (not yet played)
                    "home_score": None,
                    "away_score": None,
                    "home_win": None,
                }
            )

        games_df = pd.DataFrame(games_data)
        games_df["date"] = pd.to_datetime(games_df["date"])

        # Convert abbreviations to full names for feature engineering lookups
        games_df["home_team"] = games_df["home_team"].map(
            lambda x: TEAM_ABBR_TO_FULL.get(x, x)
        )
        games_df["away_team"] = games_df["away_team"].map(
            lambda x: TEAM_ABBR_TO_FULL.get(x, x)
        )

        # Add rest estimation
        games_df["home_rest_days"] = games_df.apply(
            lambda r: self.estimate_rest_days(
                r["date"], r["home_team"], team_game_dates
            ),
            axis=1,
        )
        games_df["away_rest_days"] = games_df.apply(
            lambda r: self.estimate_rest_days(
                r["date"], r["away_team"], team_game_dates
            ),
            axis=1,
        )
        games_df["rest_bucket"] = games_df["home_rest_days"].apply(self.bucket_rest)
        games_df["season"] = games_df["date"].dt.year

        if self.verbose:
            print(f"Found {len(games_df)} games")
            print(
                f"\n{games_df[['date', 'home_team', 'away_team', 'home_rest_days', 'away_rest_days']].to_string(index=False)}\n"
            )

        # Score games
        predictions_df = self.score_games(games_df, engineer)

        # Save if requested
        if output_csv:
            output_path = Path(output_csv)
            predictions_df.to_csv(output_path, index=False)
            if self.verbose:
                print(f"\n✓ Predictions saved to {output_path}")

        # Display predictions
        if self.verbose:
            print("\n" + "=" * 80)
            print("PREDICTIONS")
            print("=" * 80 + "\n")

            for _, pred in predictions_df.iterrows():
                print(
                    f"{pred['home_team']:>3} vs {pred['away_team']:<3} | "
                    f"Home Prob: {pred['pred_home_win_prob']:.1%} | "
                    f"Rest: {pred['home_team_rest_days']}d | "
                    f"{pred['confidence_tier']} | "
                    f"{pred['recommendation']}"
                )

            print(f"\n{'-'*80}")
            print(f"Total: {len(predictions_df)} games scored")
            tier_counts = predictions_df["confidence_tier"].value_counts()
            for tier, count in tier_counts.items():
                print(f"  {tier}: {count}")

        return predictions_df


def main():
    parser = argparse.ArgumentParser(
        description="Daily inference for NBA home-win predictions"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date to predict for (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: no save)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    try:
        engine = DailyInferenceEngine(verbose=args.verbose)
        predictions = engine.run(date=args.date, output_csv=args.output)

        if predictions.empty:
            print("No predictions generated.")
            sys.exit(1)
        else:
            print(f"\n✓ Successfully scored {len(predictions)} game(s)")
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
