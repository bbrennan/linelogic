# Player Features and Data Sources

**Status**: POC implemented; expanding to live data

## Overview
This document specifies our model’s features and the corresponding data/API sources. It clarifies computation, provenance, and compliance constraints to ensure reproducible, lawful usage.

## Feature Catalog
- **Elo Ratings**
  - **home_elo, away_elo, elo_diff**: Team strength via `EloRating` updates after each game.
  - **Source**: Engineered from historical game results (BALLDONTLIE `/v1/games`).

- **Team Form (Last 10 Games)**
  - **home_win_rate_L10, away_win_rate_L10**: Rolling win percentage.
  - **home_pt_diff_L10, away_pt_diff_L10**: Rolling average point differential.
  - **Source**: Engineered from game results; chronological, no look-ahead.

- **Schedule & Rest**
  - **home_rest_days, away_rest_days**: Days since last game (capped at 7).
  - **home_b2b, away_b2b**: Back-to-back indicator (rest_days == 0).
  - **Source**: Engineered from game dates.

- **Matchup History & Streaks**
  - **h2h_home_wins**: Home team wins vs away team in current season.
  - **home_streak, away_streak**: Current win/loss streak (signed integer).
  - **Source**: Engineered from same-season game history.

- **Context**
  - **is_home**: Home court indicator.
  - **Source**: From game record.

- **Player-Derived Team Advanced Metrics (Minutes-Weighted)**
  - **home_weighted_PER, away_weighted_PER**
  - **home_weighted_BPM, away_weighted_BPM**
  - **home_weighted_WS48, away_weighted_WS48**
  - **per_diff, bpm_diff, ws48_diff**: Home − Away differences
  - **Computation**: Aggregate player advanced metrics to team-season using minutes-weighted averages.
  - **Source**: CSV data at `.linelogic/players_advanced_metrics.csv` (see schema below). Provided via open-access datasets (e.g., Basketball-Reference exports). No paywalled sources.

## Data Sources
- **BALLDONTLIE API**
  - **Endpoint**: `https://api.balldontlie.io/v1/games` (historical games)
  - **Auth**: Header `Authorization: <API_KEY>`
  - **Pagination**: Cursor-based (`meta.next_cursor`), `per_page=100`
  - **Rate Limit**: 5 req/min (free tier); we enforce ~12s between requests
  - **Usage**: Training set construction
  - **Note**: `/v1/stats` endpoint (player box scores) may require All-Star tier ($5/mo) or higher. Free tier access to player stats is currently restricted.

- **Advanced Metrics CSV**
  - **Path**: `.linelogic/players_advanced_metrics.csv`
  - **Schema**:
    - `season:int`, `team:str`, `player:str`, `minutes:float`, `PER:float`, `BPM:float`, `WS48:float`
  - **Aggregation**: Minutes-weighted team-season averages
  - **Provenance**: Use public, open-access sources (e.g., Basketball-Reference). Do not scrape or redistribute paywalled datasets.

## Implementation References
- Feature engineering: [src/linelogic/features/engineer.py](../src/linelogic/features/engineer.py)
- Advanced metrics loader: [src/linelogic/data/advanced_metrics.py](../src/linelogic/data/advanced_metrics.py)
- Training script: [scripts/train_offline.py](../scripts/train_offline.py)

## Runtime Flags (Training)
- `--train-cutoff YYYY-MM-DD` and `--val-cutoff YYYY-MM-DD`: Time-based splits
- `--stratified`: Class-balanced split for POC (ignores time)
- `--cache-only`: Train from cached games at `.linelogic/games_cache.csv`

## Compliance Notes
- Do not use paywalled sources (e.g., ESPN Insider Hollinger Index) in code or artifacts.
- Prefer official/public APIs (BALLDONTLIE) and user-provided CSVs from open-access sites.
- Document provenance for any imported dataset; store raw CSVs under `.linelogic/` with schema.

## Next Steps
- Integrate player availability and lineup continuity using BALLDONTLIE player box scores:
  - Flags for top-N player out
  - Recent minutes load (fatigue)
  - Starting lineup stability over N games

## Building Player Stats Cache
Use the helper to fetch player box scores and build the cache for lineup features.

- Path: `scripts/build_player_stats_cache.py`
- Output: `.linelogic/player_stats_cache.csv`

Commands:

```bash
export BALLDONTLIE_API_KEY=your_key_here
/Users/bbrennan/Desktop/LineLogic/.venv/bin/python scripts/build_player_stats_cache.py
```

Then run training with lineup features:

```bash
/Users/bbrennan/Desktop/LineLogic/.venv/bin/python scripts/train_offline.py --train-cutoff 2024-01-01 --val-cutoff 2024-07-01
```

- Re-run time-based training on 2019–2024 (excluding 2020–2021) with real data and evaluate.
