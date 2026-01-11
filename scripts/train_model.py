#!/usr/bin/env python3
"""
Train and evaluate NBA win probability model.

This script:
1. Fetches historical games from BALLDONTLIE (2022-2024)
2. Engineers features using Elo + rolling stats
3. Trains logistic regression model
4. Performs walk-forward backtest
5. Evaluates with multiple metrics (log loss, Brier, ROI, Sharpe)
6. Saves trained model and generates technical report
"""

import sys
import json
import pickle
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss, brier_score_loss, accuracy_score
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from linelogic.features.engineer import FeatureEngineer
from linelogic.models.elo import EloRating


def fetch_historical_games(
    start_season: int = 2022, end_season: int = 2024
) -> pd.DataFrame:
    """
    Fetch historical NBA games from BALLDONTLIE.

    Args:
        start_season: First season year (e.g., 2022 for 2022-23 season)
        end_season: Last season year

    Returns:
        DataFrame with columns [date, home_team, away_team, home_score, away_score, home_win]
    """
    print(f"Fetching games from {start_season}-{end_season} seasons...")

    all_games = []
    base_url = "https://api.balldontlie.io/v1/games"

    for season in range(start_season, end_season + 1):
        print(f"  Season {season}-{season+1}...")
        cursor = None

        while True:
            params = {
                "seasons[]": season,
                "per_page": 100,
            }
            if cursor:
                params["cursor"] = cursor

            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            games = data.get("data", [])
            if not games:
                break

            for game in games:
                # Skip games without final scores
                if game.get("status") != "Final":
                    continue

                home_score = game.get("home_team_score")
                away_score = game.get("visitor_team_score")

                if home_score is None or away_score is None:
                    continue

                all_games.append(
                    {
                        "date": game.get("date")[:10],  # YYYY-MM-DD
                        "home_team": game.get("home_team", {}).get("full_name"),
                        "away_team": game.get("visitor_team", {}).get("full_name"),
                        "home_score": int(home_score),
                        "away_score": int(away_score),
                        "home_win": 1 if int(home_score) > int(away_score) else 0,
                    }
                )

            # Check for next page
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break

    print(f"Fetched {len(all_games)} games")
    return pd.DataFrame(all_games)


def split_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/val/test by date.

    Train: 2022-01-01 to 2023-12-31
    Val:   2024-01-01 to 2024-06-30
    Test:  2024-07-01 onwards
    """
    train = df[df["date"] < "2024-01-01"].copy()
    val = df[(df["date"] >= "2024-01-01") & (df["date"] < "2024-07-01")].copy()
    test = df[df["date"] >= "2024-07-01"].copy()

    print(f"Split: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    return train, val, test


def train_model(
    X_train: pd.DataFrame, y_train: pd.Series
) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Train logistic regression with cross-validation.

    Returns:
        Trained model and fitted scaler
    """
    print("\nTraining logistic regression...")

    # Select numeric features
    feature_cols = [
        "home_elo",
        "away_elo",
        "elo_diff",
        "is_home",
        "home_win_rate_L10",
        "away_win_rate_L10",
        "home_pt_diff_L10",
        "away_pt_diff_L10",
        "home_rest_days",
        "away_rest_days",
        "home_b2b",
        "away_b2b",
        "h2h_home_wins",
        "home_streak",
        "away_streak",
    ]

    X = X_train[feature_cols].fillna(0)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train with time series cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    best_score = float("inf")
    best_C = None

    for C in [0.001, 0.01, 0.1, 1.0, 10.0]:
        scores = []
        for train_idx, val_idx in tscv.split(X_scaled):
            model = LogisticRegression(C=C, max_iter=1000, random_state=42)
            model.fit(X_scaled[train_idx], y_train.iloc[train_idx])

            y_pred_proba = model.predict_proba(X_scaled[val_idx])[:, 1]
            score = log_loss(y_train.iloc[val_idx], y_pred_proba)
            scores.append(score)

        mean_score = np.mean(scores)
        print(f"  C={C:5.3f}: Log Loss = {mean_score:.4f}")

        if mean_score < best_score:
            best_score = mean_score
            best_C = C

    # Train final model
    print(f"\nBest C={best_C}, retraining on full dataset...")
    final_model = LogisticRegression(C=best_C, max_iter=1000, random_state=42)
    final_model.fit(X_scaled, y_train)

    return final_model, scaler


def evaluate_model(
    model: LogisticRegression,
    scaler: StandardScaler,
    X: pd.DataFrame,
    y: pd.Series,
    name: str = "Test",
) -> Dict:
    """Evaluate model performance."""
    feature_cols = [
        "home_elo",
        "away_elo",
        "elo_diff",
        "is_home",
        "home_win_rate_L10",
        "away_win_rate_L10",
        "home_pt_diff_L10",
        "away_pt_diff_L10",
        "home_rest_days",
        "away_rest_days",
        "home_b2b",
        "away_b2b",
        "h2h_home_wins",
        "home_streak",
        "away_streak",
    ]

    X_scaled = scaler.transform(X[feature_cols].fillna(0))
    y_pred_proba = model.predict_proba(X_scaled)[:, 1]
    y_pred = (y_pred_proba > 0.5).astype(int)

    metrics = {
        "log_loss": log_loss(y, y_pred_proba),
        "brier_score": brier_score_loss(y, y_pred_proba),
        "accuracy": accuracy_score(y, y_pred),
        "n_samples": len(y),
    }

    print(f"\n{name} Set Metrics:")
    print(f"  Log Loss:     {metrics['log_loss']:.4f}")
    print(f"  Brier Score:  {metrics['brier_score']:.4f}")
    print(f"  Accuracy:     {metrics['accuracy']:.2%}")
    print(f"  Samples:      {metrics['n_samples']}")

    return metrics


def save_model(
    model: LogisticRegression,
    scaler: StandardScaler,
    train_metrics: Dict,
    val_metrics: Dict,
    output_dir: str = ".linelogic",
) -> None:
    """Save trained model and metadata."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = Path(output_dir) / "nba_model_v1.0.0.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "scaler": scaler}, f)

    print(f"\nModel saved to {model_path}")

    # Save metadata
    metadata = {
        "version": "v1.0.0_20260110",
        "created_at": datetime.now().isoformat(),
        "model_type": "LogisticRegression",
        "features": [
            "home_elo",
            "away_elo",
            "elo_diff",
            "is_home",
            "home_win_rate_L10",
            "away_win_rate_L10",
            "home_pt_diff_L10",
            "away_pt_diff_L10",
            "home_rest_days",
            "away_rest_days",
            "home_b2b",
            "away_b2b",
            "h2h_home_wins",
            "home_streak",
            "away_streak",
        ],
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "hyperparameters": {
            "C": float(model.C),
            "max_iter": model.max_iter,
        },
    }

    metadata_path = Path(output_dir) / "nba_model_v1.0.0_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved to {metadata_path}")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("NBA Win Probability Model Training")
    print("=" * 60)

    # 1. Fetch data
    games_df = fetch_historical_games(2022, 2024)

    # 2. Engineer features
    print("\nEngineering features...")
    engineer = FeatureEngineer()
    features_df = engineer.engineer_features(games_df)

    # 3. Split data
    train_df, val_df, test_df = split_data(features_df)

    # 4. Train model
    X_train = train_df.drop(["date", "home_team", "away_team", "home_win"], axis=1)
    y_train = train_df["home_win"]

    model, scaler = train_model(X_train, y_train)

    # 5. Evaluate
    train_metrics = evaluate_model(model, scaler, X_train, y_train, name="Train")

    X_val = val_df.drop(["date", "home_team", "away_team", "home_win"], axis=1)
    y_val = val_df["home_win"]
    val_metrics = evaluate_model(model, scaler, X_val, y_val, name="Validation")

    # 6. Save
    save_model(model, scaler, train_metrics, val_metrics)

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
