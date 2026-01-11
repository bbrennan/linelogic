"""
Player Injuries Cache Loader

Loads injury records aggregated per team-date. Expected columns:
  - date (YYYY-MM-DD)
  - team (full_name)
  - injured_count (int)
  - injured_minutes_lost (float, estimated rotation minutes removed)

If missing, returns empty DataFrame and logs info.
"""

from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def load_player_injuries_cache(csv_path: str | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else Path(".linelogic/player_injuries_cache.csv")
    if not path.exists():
        logger.info(
            f"Player injuries cache not found at {path}. Injuries features will be neutral."
        )
        return pd.DataFrame(
            columns=["date", "team", "injured_count", "injured_minutes_lost"]
        )

    try:
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["injured_count"] = (
            pd.to_numeric(df.get("injured_count", 0), errors="coerce")
            .fillna(0)
            .astype(int)
        )
        df["injured_minutes_lost"] = pd.to_numeric(
            df.get("injured_minutes_lost", 0), errors="coerce"
        ).fillna(0.0)
        logger.info(f"Loaded player injuries cache: {len(df)} rows.")
        return df
    except Exception as e:
        logger.warning(
            f"Failed to read injuries cache at {path}: {e}; injuries neutral."
        )
        return pd.DataFrame(
            columns=["date", "team", "injured_count", "injured_minutes_lost"]
        )
