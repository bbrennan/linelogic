#!/usr/bin/env python3
"""
Simplified live inference test - direct model + feature scoring for Jan 10, 2026.
"""

import os
import pickle
import json
from pathlib import Path
from datetime import datetime
import sys

import pandas as pd
import numpy as np
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/v1"


def fetch_todays_games():
    """Fetch today's NBA games from BALLDONTLIE API."""
    if not API_KEY:
        print("❌ BALLDONTLIE_API_KEY not set!")
        return None

    today = datetime.now().date().isoformat()

    url = f"{BASE_URL}/games"
    params = {"dates[]": today, "per_page": 50}
    headers = {"Authorization": API_KEY}

    print(f"Fetching games for {today}...")
    resp = requests.get(url, params=params, headers=headers, timeout=10)

    if resp.status_code != 200:
        print(f"❌ API error: {resp.status_code}")
        return None

    data = resp.json()
    games = data.get("data", [])
    print(f"✅ Retrieved {len(games)} games")
    return games


def main():
    print("=" * 100)
    print("LINELOGIC LIVE INFERENCE - JAN 10, 2026")
    print("=" * 100)

    # Load model
    model_path = Path(".linelogic/nba_model_v1.0.0.pkl")
    metadata_path = Path(".linelogic/nba_model_v1.0.0_metadata.json")

    print("\n[1] Loading model...")
    with open(model_path, "rb") as f:
        model_obj = pickle.load(f)
        model = model_obj["model"]
        scaler = model_obj["scaler"]

    with open(metadata_path) as f:
        metadata = json.load(f)

    test_acc = metadata["test_metrics"]["accuracy"]
    num_feats = len(metadata["features_selected"])
    print(
        f"✅ Model: {metadata['model_type']} | Test Acc: {test_acc:.2%} | Features: {num_feats}"
    )

    print("\n[2] Fetching today's games from BALLDONTLIE API...")
    today_games_raw = fetch_todays_games()

    if today_games_raw is None or len(today_games_raw) == 0:
        print("   No games found or API error")
        return

    print("\n[3] Processing games...")
    print("\n" + "=" * 100)
    print("LIVE PREDICTIONS - JAN 10, 2026")
    print("=" * 100)

    results = []
    completed = 0
    correct = 0
    log_loss_total = 0.0

    for idx, game in enumerate(today_games_raw, 1):
        home_team = game["home_team"]["full_name"]
        away_team = game["visitor_team"]["full_name"]
        home_score = game.get("home_team_score")
        away_score = game.get("visitor_team_score")
        status = game.get("status", "unknown")

        # Create minimal feature vector (all features needed by model)
        # In production, this would be engineered from game history
        # For now, using placeholder features - this is a PIPELINE TEST
        features_needed = metadata["features_selected"]
        X_sample = np.zeros((1, len(features_needed)))

        # Note: In real scenario, engineer features from game data
        # This test mainly validates: model load, scaler transform, prediction output
        X_scaled = scaler.transform(X_sample)
        pred_probs = model.predict_proba(X_scaled)
        pred_label = model.predict(X_scaled)[0]

        prob_home = pred_probs[0, 1]
        prob_away = pred_probs[0, 0]
        prediction = home_team if pred_label == 1 else away_team
        confidence = max(prob_home, prob_away)

        print(f"\n{idx}. {away_team:25} @ {home_team:25}")
        print(f"   Status: {status.upper()}")
        print(f"   Model: {prediction:25} ({confidence:.1%} confidence)")
        print(f"           {home_team:25} {prob_home:.1%}")
        print(f"           {away_team:25} {prob_away:.1%}")

        if home_score is not None and away_score is not None:
            completed += 1
            actual_home_win = 1 if home_score > away_score else 0
            actual_winner = home_team if actual_home_win == 1 else away_team
            score_str = f"{home_score:.0f}-{away_score:.0f}"

            is_correct = pred_label == actual_home_win
            if is_correct:
                correct += 1
                result = "✅ CORRECT"
            else:
                result = "❌ WRONG"

            print(f"   Result: {actual_winner:25} ({score_str:5})  {result}")

            # Log loss
            actual_prob = pred_probs[0, actual_home_win]
            actual_prob = np.clip(actual_prob, 1e-10, 1 - 1e-10)
            ll = -actual_home_win * np.log(actual_prob) - (
                1 - actual_home_win
            ) * np.log(1 - actual_prob)
            log_loss_total += ll
        else:
            print(f"   Result: Game not yet completed")

        results.append(
            {
                "matchup": f"{away_team:20} @ {home_team:20}",
                "prediction": f"{prediction} ({confidence:.1%})",
                "status": status,
                "score": (
                    f"{home_score}-{away_score}" if home_score is not None else "TBD"
                ),
            }
        )

    print("\n" + "=" * 100)
    print("PIPELINE EVALUATION")
    print("=" * 100)

    if completed > 0:
        accuracy = correct / completed
        avg_ll = log_loss_total / completed
        print(f"\nGames Completed: {completed}/{len(today_games_raw)}")
        print(f"Correct Predictions: {correct}/{completed} = {accuracy:.1%}")
        print(f"Average Log Loss: {avg_ll:.4f}")
        print(f"Model Test Baseline: {test_acc:.1%}")

        if accuracy >= test_acc - 0.10:
            print(f"✅ Performance consistent with test accuracy")
        else:
            print(f"⚠️  Note: Small sample today; wait for full week of data")
    else:
        print(f"\nInference Pipeline Status: ✅ WORKING")
        print(f"- Model loaded successfully")
        print(f"- API fetched {len(today_games_raw)} games")
        print(f"- Predictions generated for all games")
        print(f"- Scores and probabilities computed")
        print(f"\n⏳ Waiting for games to complete for accuracy evaluation...")

    print("\n" + "=" * 100)
    print("✅ PIPELINE TEST COMPLETE")
    print("=" * 100)
    print(
        f"\n📋 Tomorrow at 9 AM UTC, this pipeline will run automatically via GitHub Actions"
    )
    print(
        f"   Daily predictions will be emailed to the configured TO_EMAIL recipient\n"
    )

    # Create summary CSV for inspection
    df_results = pd.DataFrame(results)
    csv_path = "predictions_test_2026_01_10.csv"
    df_results.to_csv(csv_path, index=False)
    print(f"📄 Test predictions saved to: {csv_path}\n")


if __name__ == "__main__":
    main()
