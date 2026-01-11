#!/usr/bin/env python3
"""
Build Player Stats Cache from BALLDONTLIE `/v1/stats`

Outputs `.linelogic/player_stats_cache.csv` with columns:
  date, team, player, starter, minutes, season

Notes:
- Cursor-based pagination; respects free-tier rate limit (~12s/request).
- Excludes 2020 season (COVID bubble) by default.
- Starter heuristic: top-5 minutes per game-team flagged as starters.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def to_minutes(min_str):
    if min_str is None:
        return 0.0
    try:
        if isinstance(min_str, (int, float)):
            return float(min_str)
        s = str(min_str)
        if ":" in s:
            mm, ss = s.split(":")
            return float(mm) + float(ss) / 60.0
        return float(s)
    except Exception:
        return 0.0


def infer_season(dt: pd.Timestamp) -> int:
    m = int(dt.month)
    y = int(dt.year)
    return y if m >= 8 else y - 1


def fetch_stats_for_season(season: int, api_key: str) -> List[Dict]:
    base_url = "https://api.balldontlie.io/v1/stats"
    headers = {"Authorization": api_key} if api_key else {}
    cursor = None
    records: List[Dict] = []
    req_count = 0
    last_req = time.time()
    max_attempts = 500
    attempts = 0

    logger.info(f"Fetching player stats for season {season}-{season+1}...")

    while attempts < max_attempts:
        params = {"seasons[]": season, "per_page": 100}
        if cursor:
            params["cursor"] = cursor

        elapsed = time.time() - last_req
        if elapsed < 12:
            wait = 12 - elapsed
            logger.info(f"  Waiting for rate limit... ({wait:.1f}s)")
            time.sleep(wait)

        logger.info(
            f"  → API request #{req_count + 1} (attempt {attempts + 1}/{max_attempts})"
        )
        try:
            resp = requests.get(base_url, params=params, headers=headers, timeout=8)
            last_req = time.time()
            req_count += 1
            attempts += 1
            logger.info(f"  ✓ Response received (status {resp.status_code})")
            if resp.status_code == 429:
                logger.warning("Rate limited (429). Pausing 60s...")
                time.sleep(60)
                continue
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.Timeout:
            logger.warning("  Timeout; retrying next cursor page...")
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request error: {e}")
            break

        stats = data.get("data", [])
        if not stats:
            logger.info("  → No more stats pages")
            break

        logger.info(f"  ✓ Received {len(stats)} stat rows")

        for s in stats:
            game = s.get("game", {})
            team = s.get("team", {})
            player = s.get("player", {})
            date_str = game.get("date")
            try:
                dt = pd.to_datetime(date_str)
            except Exception:
                continue
            team_name = team.get("full_name") or team.get("name")
            player_name = (
                f"{player.get('first_name','')} {player.get('last_name','')}".strip()
            )
            minutes = to_minutes(s.get("min") or s.get("minutes"))
            season_label = infer_season(dt)
            game_id = game.get("id")

            records.append(
                {
                    "game_id": game_id,
                    "date": dt.date().isoformat(),
                    "team": team_name,
                    "player": player_name,
                    "minutes": minutes,
                    "season": season_label,
                }
            )

        meta = data.get("meta", {})
        cursor = meta.get("next_cursor")
        if not cursor:
            break

    logger.info(
        f"Season {season}: collected {len(records)} player stat rows via {req_count} requests"
    )
    return records


def assign_starters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["starter"] = 0
        return df
    starters = []
    for (gid, team), gdf in df.groupby(["game_id", "team"]):
        ranked = gdf.sort_values("minutes", ascending=False)
        top5 = set(ranked.head(5)["player"].tolist())
        starters.extend([1 if p in top5 else 0 for p in gdf["player"]])
    df = df.copy()
    df["starter"] = starters
    return df


def build_cache(
    start_season: int = 2019, end_season: int = 2024, api_key: str | None = None
) -> Path:
    seasons = [s for s in range(start_season, end_season + 1) if s != 2020]
    all_records: List[Dict] = []
    for s in seasons:
        all_records.extend(fetch_stats_for_season(s, api_key or ""))

    df = pd.DataFrame(all_records)
    if df.empty:
        logger.error("No player stats fetched; cache not created.")
        sys.exit(1)
    df = assign_starters(df)
    df = df[["date", "team", "player", "starter", "minutes", "season"]]

    out_path = Path(".linelogic/player_stats_cache.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info(
        f"Saved player stats cache to {out_path} ({out_path.stat().st_size/1024:.1f} KB)"
    )
    return out_path


def main():
    api_key = os.getenv("BALLDONTLIE_API_KEY", "")
    if not api_key:
        logger.warning("BALLDONTLIE_API_KEY not set; requests may be rejected.")
    build_cache(api_key=api_key)


if __name__ == "__main__":
    main()
