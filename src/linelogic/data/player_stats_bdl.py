"""
BALLDONTLIE Player Stats Loader (Cache-first)

Loads player game logs from a local CSV cache to support lineup continuity and
key player availability features. The cache file is expected at
`.linelogic/player_stats_cache.csv` with the following columns:

  - date (YYYY-MM-DD)
  - team (BALLDONTLIE team full_name)
  - player (str)
  - starter (bool or {0,1})
  - minutes (float or mm:ss string convertible)
  - season (int)  # season label (e.g., 2023 for 2023-24)

If the cache is missing, returns an empty DataFrame and logs an info message.
Future work can implement API fetch via BALLDONTLIE `/v1/stats` and append to
the cache with rate limit adherence.
"""

from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def load_player_stats_cache(csv_path: str | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else Path(".linelogic/player_stats_cache.csv")

    if not path.exists():
        logger.info(
            f"Player stats cache not found at {path}. Proceeding without lineup features."
        )
        return pd.DataFrame(
            columns=["date", "team", "player", "starter", "minutes", "season"]
        )

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.warning(f"Failed to read player stats cache at {path}: {e}. Ignoring.")
        return pd.DataFrame(
            columns=["date", "team", "player", "starter", "minutes", "season"]
        )

    # Normalize types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["starter"] = df["starter"].astype(int).clip(0, 1)

    # Convert minutes like '32:15' to float minutes
    def _to_minutes(x):
        try:
            if isinstance(x, (int, float)):
                return float(x)
            if isinstance(x, str) and ":" in x:
                mm, ss = x.split(":")
                return float(mm) + float(ss) / 60.0
            return float(x)
        except Exception:
            return 0.0

    df["minutes"] = df["minutes"].apply(_to_minutes)

    # Ensure season exists; if missing, infer from date (Aug-Dec -> year, Jan-Jul -> year-1)
    if "season" not in df.columns or df["season"].isna().any():

        def _infer_season(d: pd.Timestamp) -> int:
            m = int(d.month)
            y = int(d.year)
            return y if m >= 8 else y - 1

        df["season"] = df["date"].apply(_infer_season)

    logger.info(f"Loaded player stats cache: {len(df):,} rows.")
    return df
