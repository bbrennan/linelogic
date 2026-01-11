"""
Odds Cache Loader

Loads market odds cache from CSV (expected columns):
  - date (YYYY-MM-DD)
  - home_team (full_name)
  - away_team (full_name)
  - implied_home_prob (float in [0,1])
  - spread_home (float, points from home perspective; negative = favored)
  - total (float, game total)

If missing, returns empty DataFrame and logs info.
"""

from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def load_odds_cache(csv_path: str | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else Path(".linelogic/odds_cache.csv")
    if not path.exists():
        logger.info(f"Odds cache not found at {path}; odds features neutral.")
        return pd.DataFrame(
            columns=[
                "date",
                "home_team",
                "away_team",
                "implied_home_prob",
                "spread_home",
                "total",
            ]
        )
    try:
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["implied_home_prob"] = pd.to_numeric(
            df.get("implied_home_prob", 0), errors="coerce"
        ).fillna(0.0)
        df["spread_home"] = pd.to_numeric(
            df.get("spread_home", 0), errors="coerce"
        ).fillna(0.0)
        df["total"] = pd.to_numeric(df.get("total", 0), errors="coerce").fillna(0.0)
        logger.info(f"Loaded odds cache: {len(df)} rows.")
        return df
    except Exception as e:
        logger.warning(f"Failed to read odds cache at {path}: {e}; odds neutral.")
        return pd.DataFrame(
            columns=[
                "date",
                "home_team",
                "away_team",
                "implied_home_prob",
                "spread_home",
                "total",
            ]
        )
