#!/usr/bin/env python3
"""
Generate synthetic NBA games data for model training.

Creates realistic historical game data for 2022-2024 seasons
to test the full training pipeline when BALLDONTLIE API is unavailable.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_synthetic_games(
    start_date="2022-10-18", end_date="2024-12-31", n_teams=30
):
    """
    Generate synthetic NBA game data.

    Args:
        start_date: Start of season (str, YYYY-MM-DD)
        end_date: End of season (str, YYYY-MM-DD)
        n_teams: Number of NBA teams

    Returns:
        DataFrame with columns: date, home_team, away_team, home_score, away_score, home_win
    """
    np.random.seed(42)

    # NBA team names
    teams = [
        "Atlanta Hawks",
        "Boston Celtics",
        "Brooklyn Nets",
        "Charlotte Hornets",
        "Chicago Bulls",
        "Cleveland Cavaliers",
        "Dallas Mavericks",
        "Denver Nuggets",
        "Detroit Pistons",
        "Golden State Warriors",
        "Houston Rockets",
        "Indiana Pacers",
        "Los Angeles Clippers",
        "Los Angeles Lakers",
        "Memphis Grizzlies",
        "Miami Heat",
        "Milwaukee Bucks",
        "Minnesota Timberwolves",
        "New Orleans Pelicans",
        "New York Knicks",
        "Oklahoma City Thunder",
        "Orlando Magic",
        "Philadelphia 76ers",
        "Phoenix Suns",
        "Portland Trail Blazers",
        "Sacramento Kings",
        "San Antonio Spurs",
        "Toronto Raptors",
        "Utah Jazz",
        "Washington Wizards",
    ][:n_teams]

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    games = []
    current_date = start

    # Generate ~82 games per team per season (~1,230 games total)
    games_per_day_range = 8  # 8-12 games per day

    while current_date <= end:
        # Skip offseason (July, August, September)
        if current_date.month in [7, 8, 9]:
            current_date += timedelta(days=1)
            continue

        # Skip All-Star break (early February)
        if current_date.month == 2 and 7 <= current_date.day <= 14:
            current_date += timedelta(days=1)
            continue

        # Generate 8-12 games for this day
        n_games_today = np.random.randint(5, games_per_day_range)

        # Randomly sample teams for games
        available_teams = teams.copy()

        for _ in range(n_games_today):
            if len(available_teams) < 2:
                available_teams = teams.copy()

            # Pick two teams
            home_idx = np.random.randint(0, len(available_teams))
            home_team = available_teams.pop(home_idx)

            away_idx = np.random.randint(0, len(available_teams))
            away_team = available_teams.pop(away_idx)

            # Generate scores (realistic NBA scoring)
            # Home court advantage: ~3 point advantage
            home_base = np.random.normal(105, 8)  # Mean 105, std 8
            away_base = np.random.normal(103, 8)  # Mean 103, std 8

            home_score = int(max(80, home_base + np.random.normal(0, 2)))
            away_score = int(max(80, away_base + np.random.normal(0, 2)))

            home_win = 1 if home_score > away_score else 0

            games.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_score": home_score,
                    "away_score": away_score,
                    "home_win": home_win,
                }
            )

        current_date += timedelta(days=1)

    df = pd.DataFrame(games)
    df["date"] = pd.to_datetime(df["date"])

    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    print(f"✅ Generated {len(df)} synthetic games")
    print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"   Home win rate: {df['home_win'].mean():.2%}")

    return df


if __name__ == "__main__":
    df = generate_synthetic_games()
    print(f"\nSample games:")
    print(df.head(10).to_string(index=False))
