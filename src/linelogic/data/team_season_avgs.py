"""
Team Season Averages Loader (BALLDONTLIE, GOAT tier)

Fetches and caches team season averages for multiple categories/types, then
combines into a single table keyed by (season, team full_name).

Primary outputs (per team-season):
- net_rating, pace, off_rating, def_rating (general/advanced)
- off_3pa_rate (fg3a/fga from general/base)
- def_opp_3pa_rate (opponent fg3a/fga from general/opponent)
- win_pct (general/base w_pct)

Caches to .linelogic/team_season_avgs.csv by default.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.balldontlie.io/nba/v1/team_season_averages"


def _fetch_category(
    season: int,
    category: str,
    stat_type: Optional[str],
    api_key: str,
    season_type: str = "regular",
) -> List[Dict]:
    """Fetch a single category/type for a season with pagination."""
    headers = {"Authorization": api_key} if api_key else {}
    params = {
        "season": season,
        "season_type": season_type,
        "per_page": 100,
    }
    if stat_type:
        params["type"] = stat_type

    cursor = None
    results: List[Dict] = []
    req_count = 0
    while True:
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(
            f"{BASE_URL}/{category}", params=params, headers=headers, timeout=15
        )
        req_count += 1
        if resp.status_code == 429:
            logger.warning("Rate limited on team_season_averages; aborting fetch.")
            break
        try:
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed fetching {category}/{stat_type} {season}: {e}")
            break
        data = resp.json()
        rows = data.get("data", [])
        if not rows:
            break
        results.extend(rows)
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break
    logger.info(
        f"Season {season} {category}/{stat_type or 'none'}: {len(results)} rows via {req_count} reqs"
    )
    return results


def fetch_team_season_avgs(
    seasons: List[int], api_key: str, season_type: str = "regular"
) -> pd.DataFrame:
    """Fetch team season averages across seasons and combine key stats."""
    base_rows: Dict[tuple, Dict] = {}
    opp_rows: Dict[tuple, Dict] = {}
    adv_rows: Dict[tuple, Dict] = {}

    for season in seasons:
        # General/base for offensive shot profile and win pct
        base_data = _fetch_category(season, "general", "base", api_key, season_type)
        for row in base_data:
            team = row.get("team", {})
            key = (season, team.get("full_name"))
            base_rows[key] = row.get("stats", {}) | {"team": team}

        # General/opponent for defensive shot profile allowed
        opp_data = _fetch_category(season, "general", "opponent", api_key, season_type)
        for row in opp_data:
            team = row.get("team", {})
            key = (season, team.get("full_name"))
            opp_rows[key] = row.get("stats", {}) | {"team": team}

        # General/advanced for net/pace
        adv_data = _fetch_category(season, "general", "advanced", api_key, season_type)
        for row in adv_data:
            team = row.get("team", {})
            key = (season, team.get("full_name"))
            adv_rows[key] = row.get("stats", {}) | {"team": team}

    records: List[Dict] = []
    all_keys = set(base_rows.keys()) | set(opp_rows.keys()) | set(adv_rows.keys())
    for key in sorted(all_keys):
        season, _ = key
        base = base_rows.get(key, {})
        opp = opp_rows.get(key, {})
        adv = adv_rows.get(key, {})
        team = (base.get("team") or opp.get("team") or adv.get("team") or {}).get(
            "full_name", ""
        )
        fga = float(base.get("fga", 0) or 0)
        fg3a = float(base.get("fg3a", 0) or 0)
        off_3pa_rate = fg3a / fga if fga > 0 else 0.0

        opp_fga = float(opp.get("fga", 0) or 0)
        opp_fg3a = float(opp.get("fg3a", 0) or 0)
        def_opp_3pa_rate = opp_fg3a / opp_fga if opp_fga > 0 else 0.0

        record = {
            "season": season,
            "team": team,
            "win_pct": float(base.get("w_pct", 0) or 0),
            "net_rating": float(adv.get("net_rating", 0) or 0),
            "pace": float(adv.get("pace", 0) or 0),
            "off_rating": float(adv.get("off_rating", 0) or 0),
            "def_rating": float(adv.get("def_rating", 0) or 0),
            "off_3pa_rate": off_3pa_rate,
            "def_opp_3pa_rate": def_opp_3pa_rate,
        }
        records.append(record)

    df = pd.DataFrame(records)
    logger.info(
        f"Built team season averages: {len(df)} rows across {df['season'].nunique() if not df.empty else 0} seasons"
    )
    return df


def load_team_season_avgs(
    csv_path: Optional[str] = None,
    api_key: Optional[str] = None,
    seasons: Optional[List[int]] = None,
    season_type: str = "regular",
) -> pd.DataFrame:
    """Load from cache or fetch if missing and API key provided."""
    path = Path(csv_path) if csv_path else Path(".linelogic/team_season_avgs.csv")
    if path.exists():
        try:
            df = pd.read_csv(path)
            logger.info(
                f"Loaded team season averages cache: {len(df)} rows from {path}"
            )
            return df
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}. Will refetch if possible.")

    if api_key and seasons:
        df = fetch_team_season_avgs(seasons, api_key, season_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"Saved team season averages cache to {path}")
        return df

    logger.warning("Team season averages cache missing and no API key provided.")
    return pd.DataFrame(
        columns=[
            "season",
            "team",
            "win_pct",
            "net_rating",
            "pace",
            "off_rating",
            "def_rating",
            "off_3pa_rate",
            "def_opp_3pa_rate",
        ]
    )
