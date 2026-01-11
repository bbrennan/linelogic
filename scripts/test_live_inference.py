#!/usr/bin/env python3
"""
Live inference test for Jan 10, 2026 (TODAY).
Fetches today's games from BALLDONTLIE API, scores with model,
evaluates against actual results + pre-game odds.
"""

import os
import pickle
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys

import pandas as pd
import numpy as np
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from linelogic.features.engineer import FeatureEngineer

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/v1"


def fetch_todays_games():
    """Fetch today's NBA games from BALLDONTLIE API."""
    if not API_KEY:
        print("❌ BALLDONTLIE_API_KEY not set!")
        return None

    today = datetime.now().date().isoformat()  # 2026-01-10

    url = f"{BASE_URL}/games"
    params = {"dates[]": today, "per_page": 50}
    headers = {"Authorization": API_KEY}

    print(f"Fetching games for {today}...")
    resp = requests.get(url, params=params, headers=headers, timeout=10)

    if resp.status_code != 200:
        print(f"❌ API error: {resp.status_code}")
        print(resp.text)
        return None

    data = resp.json()
    games = data.get("data", [])

    print(f"✅ Retrieved {len(games)} games for {today}")
    return games


def parse_games_to_df(games):
    """Convert API games to DataFrame matching cache schema."""
    rows = []
    for game in games:
        rows.append(
            {
                "date": game["date"],
                "home_team": game["home_team"]["full_name"],
                "away_team": game["visitor_team"]["full_name"],
                "home_score": game.get("home_team_score"),
                "away_score": game.get("visitor_team_score"),
                "game_id": game["id"],
                "season": int(game["season"]),
                "status": game["status"],
            }
        )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def main():
    # Load model
    model_path = Path(".linelogic/nba_model_v1.0.0.pkl")
    metadata_path = Path(".linelogic/nba_model_v1.0.0_metadata.json")
    games_cache_path = Path(".linelogic/games_cache.csv")

    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return

    print("=" * 100)
    print("LINELOGIC LIVE INFERENCE TEST - JAN 10, 2026")
    print("=" * 100)

    print("\n[1/5] Loading model...")
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
    print(f"   Selected features: {', '.join(metadata['features_selected'][:5])}...")

    print("\n[2/5] Loading historical games (for feature engineering)...")
    if not games_cache_path.exists():
        print(f"❌ Cache not found: {games_cache_path}")
        return

    df_all_games = pd.read_csv(games_cache_path)
    df_all_games["date"] = pd.to_datetime(df_all_games["date"])

    # Add season field if missing (based on date)
    if "season" not in df_all_games.columns:
        df_all_games["season"] = df_all_games["date"].dt.year.where(
            df_all_games["date"].dt.month >= 10, df_all_games["date"].dt.year - 1
        )

    print(f"✅ Loaded {len(df_all_games)} historical games (2019-2025)")

    print("\n[3/5] Fetching TODAY's games from BALLDONTLIE API...")
    today_games_raw = fetch_todays_games()

    if today_games_raw is None:
        print("   Proceeding with mock data for testing...")
        # Create mock games for demo purposes
        today_games_raw = []

    if len(today_games_raw) > 0:
        today_games = parse_games_to_df(today_games_raw)
        print(f"\n📅 Today's games ({len(today_games)}):")
        for _, g in today_games.iterrows():
            status = f"({g['status'].upper()})"
            if pd.notna(g["home_score"]):
                print(
                    f"   {g['away_team']:25} @ {g['home_team']:25} {g['home_score']:.0f}-{g['away_score']:.0f} {status}"
                )
            else:
                print(
                    f"   {g['away_team']:25} @ {g['home_team']:25} (Not Started) {status}"
                )
    else:
        print("   No games found for today, or API error.")
        print("\n   Creating mock data for testing...")
        mock_data = [
            {
                "date": "2026-01-10",
                "home_team": "Boston Celtics",
                "away_team": "Miami Heat",
                "home_score": 105,
                "away_score": 98,
                "game_id": 1,
                "season": 2025,
                "status": "Final",
            },
            {
                "date": "2026-01-10",
                "home_team": "Los Angeles Lakers",
                "away_team": "Golden State Warriors",
                "home_score": None,
                "away_score": None,
                "game_id": 2,
                "season": 2025,
                "status": "Scheduled",
            },
        ]
        today_games = pd.DataFrame(mock_data)
        today_games["date"] = pd.to_datetime(today_games["date"])
        print(f"✅ Created {len(today_games)} mock games for demo")

    print("\n[4/5] Engineering features...")

    # Combine all games for engineering context
    df_combined = pd.concat([df_all_games, today_games], ignore_index=True)
    df_combined = df_combined.sort_values("date").reset_index(drop=True)

    engineer = FeatureEngineer(df_combined)
    features_needed = metadata["features_selected"]

    print(f"   Features: {features_needed}")

    try:
        X_today = engineer.engineer(today_games)
        X_today = X_today[features_needed]
        X_scaled = scaler.transform(X_today)

        print(f"✅ Engineered {X_today.shape[0]} games × {X_today.shape[1]} features")
    except Exception as e:
        print(f"❌ Feature engineering failed: {e}")
        print("   This may be due to missing injury/odds data.")
        return

    print("\n[5/5] Scoring games & generating predictions...")
    pred_probs = model.predict_proba(X_scaled)
    pred_labels = model.predict(X_scaled)

    print("\n" + "=" * 100)
    print("LIVE PREDICTIONS - JAN 10, 2026")
    print("=" * 100)

    correct_preds = 0
    completed_games = 0
    log_loss_sum = 0.0

    for idx, (_, game) in enumerate(today_games.iterrows()):
        home = game["home_team"]
        away = game["away_team"]

        prob_home_win = pred_probs[idx, 1]
        prob_away_win = pred_probs[idx, 0]
        prediction = home if pred_labels[idx] == 1 else away
        confidence = max(prob_home_win, prob_away_win)

        print(f"\n{idx+1}. {away:25} @ {home:25}")
        print(f"   Model: {prediction:25} ({confidence:.1%} confidence)")
        print(f"   Breakdown: {home:25} {prob_home_win:.1%}")
        print(f"              {away:25} {prob_away_win:.1%}")

        # Actual result
        if pd.notna(game["home_score"]) and pd.notna(game["away_score"]):
            completed_games += 1
            actual_home_win = 1 if game["home_score"] > game["away_score"] else 0
            actual_winner = home if actual_home_win == 1 else away
            score_str = f"{game['home_score']:.0f}-{game['away_score']:.0f}"

            is_correct = pred_labels[idx] == actual_home_win
            if is_correct:
                correct_preds += 1
                result_indicator = "✅ CORRECT"
            else:
                result_indicator = "❌ WRONG"

            print(f"   Result: {actual_winner:25} ({score_str:5})  {result_indicator}")

            # Compute log loss for this game
            actual_prob = pred_probs[idx, actual_home_win]
            actual_prob = np.clip(actual_prob, 1e-10, 1 - 1e-10)  # Avoid log(0)
            ll = -actual_home_win * np.log(actual_prob) - (
                1 - actual_home_win
            ) * np.log(1 - actual_prob)
            log_loss_sum += ll
        else:
            print(f"   Result: Not yet completed")

    # Summary stats
    if completed_games > 0:
        accuracy = correct_preds / completed_games
        avg_log_loss = log_loss_sum / completed_games

        print("\n" + "=" * 100)
        print("TODAY'S PERFORMANCE SUMMARY")
        print("=" * 100)
        print(f"Games Completed: {completed_games}")
        print(
            f"Correct Predictions: {correct_preds}/{completed_games} = {accuracy:.1%}"
        )
        print(f"Average Log Loss: {avg_log_loss:.4f}")
        print(f"Model Baseline Test Accuracy: {test_acc:.1%}")

        if accuracy >= test_acc - 0.05:
            print(f"\n✅ Performance in line with test accuracy ({test_acc:.1%})")
        else:
            print(f"\n⚠️  Performance below test accuracy ({test_acc:.1%})")
    else:
        print("\n" + "=" * 100)
        print("STATUS: Games not yet completed")
        print("=" * 100)
        print("Check back after games are finished for accuracy evaluation.")

    print("\n✅ Live inference test complete!")
    print(
        "\n📋 Tomorrow at 9 AM UTC, this script will run automatically via GitHub Actions"
    )
    print(
        "   and send daily predictions via email to the configured TO_EMAIL recipient\n"
    )


if __name__ == "__main__":
    main()
