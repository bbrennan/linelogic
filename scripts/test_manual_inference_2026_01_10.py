#!/usr/bin/env python3
"""
Manual test of inference + evaluation for Jan 10, 2026.
Loads cache data, scores games, compares to actuals + odds.
"""

import pickle
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys

import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from linelogic.features.engineer import FeatureEngineer


def main():
    # Load model
    model_path = Path(".linelogic/nba_model_v1.0.0.pkl")
    metadata_path = Path(".linelogic/nba_model_v1.0.0_metadata.json")

    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return

    print("Loading model...")
    with open(model_path, "rb") as f:
        model_obj = pickle.load(f)
        model = model_obj["model"]
        scaler = model_obj["scaler"]

    with open(metadata_path) as f:
        metadata = json.load(f)

    test_acc = metadata["test_metrics"]["accuracy"]
    num_feats = len(metadata["features_selected"])
    print(f"✅ Model loaded: {metadata['model_type']} v{metadata['version']}")
    print(f"   Test Accuracy: {test_acc:.2%} | Features selected: {num_feats}")

    # Load games cache
    games_cache = Path(".linelogic/games_cache.csv")
    if not games_cache.exists():
        print(f"❌ Games cache not found: {games_cache}")
        return

    print(f"\nLoading games cache...")
    df_games = pd.read_csv(games_cache)
    df_games["date"] = pd.to_datetime(df_games["date"])

    # Filter for Jan 10, 2026 (today)
    target_date = pd.Timestamp("2026-01-10")
    today_games = df_games[df_games["date"].dt.date == target_date.date()]

    print(f"✅ Found {len(today_games)} games in cache for {target_date.date()}")

    if len(today_games) == 0:
        print("\n⚠️  No games found for today in cache.")
        print(
            "   Cache dates range:",
            df_games["date"].min(),
            "to",
            df_games["date"].max(),
        )
        print("\n   (Note: Cache may only contain historical training data)")
        print("   Showing recent cached games for reference:")
        recent = df_games.tail(10)[
            ["date", "home_team", "away_team", "home_score", "away_score"]
        ]
        print(recent.to_string(index=False))
        return

    print("\nGames for today:")
    print(
        today_games[
            ["date", "home_team", "away_team", "home_score", "away_score"]
        ].to_string(index=False)
    )

    # Engineer features
    print("\nEngineering features...")
    engineer = FeatureEngineer(df_games)

    # Get features for today's games
    features_needed = metadata["features_selected"]
    print(f"   Features needed: {features_needed}")

    X_today = engineer.engineer(today_games)
    print(f"✅ Features engineered: shape {X_today.shape}")

    # Select only features that the model expects
    X_today = X_today[features_needed]

    # Scale
    X_scaled = scaler.transform(X_today)

    # Predict
    pred_probs = model.predict_proba(X_scaled)
    pred_labels = model.predict(X_scaled)

    print("\n" + "=" * 100)
    print("PREDICTIONS FOR TODAY (Jan 10, 2026)")
    print("=" * 100)

    results = []
    for idx, (_, game) in enumerate(today_games.iterrows()):
        home = game["home_team"]
        away = game["away_team"]

        prob_home_win = pred_probs[idx, 1]
        prob_away_win = pred_probs[idx, 0]
        prediction = home if pred_labels[idx] == 1 else away

        # Actual result
        if pd.notna(game["home_score"]) and pd.notna(game["away_score"]):
            actual_home_win = 1 if game["home_score"] > game["away_score"] else 0
            actual_winner = home if actual_home_win == 1 else away
            correct = (
                "✅ CORRECT" if (pred_labels[idx] == actual_home_win) else "❌ WRONG"
            )
            score_str = f"{game['home_score']:.0f}-{game['away_score']:.0f}"
        else:
            actual_winner = "TBD"
            correct = "(game not completed)"
            score_str = "TBD"

        results.append(
            {
                "matchup": f"{away:3} @ {home:3}",
                "prediction": f"{prediction} ({prob_home_win:.1%})",
                "actual": f"{actual_winner} ({score_str})",
                "result": correct,
            }
        )

        print(f"\n{idx+1}. {away:3} @ {home:3}")
        print(f"   Model predicts: {prediction} ({prob_home_win:.1%} home win)")
        print(f"   vs Away: {prob_away_win:.1%}")
        if pd.notna(game["home_score"]) and pd.notna(game["away_score"]):
            print(
                f"   Actual result: {home} {game['home_score']:.0f}, {away} {game['away_score']:.0f}"
            )
            print(f"   {correct}")
        else:
            print(f"   Status: {correct}")

    # Summary stats if we have results
    if len(today_games) > 0 and pd.notna(today_games.iloc[0]["home_score"]):
        actual_winners = []
        correct_preds = 0

        for idx, (_, game) in enumerate(today_games.iterrows()):
            if pd.notna(game["home_score"]) and pd.notna(game["away_score"]):
                actual_home_win = 1 if game["home_score"] > game["away_score"] else 0
                actual_winners.append(actual_home_win)
                if pred_labels[idx] == actual_home_win:
                    correct_preds += 1

        if len(actual_winners) > 0:
            accuracy = correct_preds / len(actual_winners)
            print("\n" + "=" * 100)
            print(f"ACCURACY: {correct_preds}/{len(actual_winners)} = {accuracy:.1%}")
            print("=" * 100)

    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
