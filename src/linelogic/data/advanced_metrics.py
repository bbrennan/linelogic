"""
Advanced Team Metrics Loader

Loads player-level advanced metrics (e.g., PER, BPM, WS/48, minutes) from a CSV
and aggregates to team-season level using minutes-weighted averages.

CSV expected columns:
  - season (int, e.g., 2023)
  - team (str, must match BALLDONTLIE full_name in games data)
  - player (str)
  - minutes (float)
  - PER (float)
  - BPM (float)
  - WS48 (float)

Output columns:
  - season
  - team
  - team_weighted_PER
  - team_weighted_BPM
  - team_weighted_WS48
  - team_minutes_total

If the CSV is missing or malformed, returns an empty DataFrame and logs a warning.
"""

from pathlib import Path
from typing import Optional
import logging
import pandas as pd


logger = logging.getLogger(__name__)


def load_team_advanced_metrics(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Load and aggregate player advanced metrics to team-season level.

    Args:
        csv_path: Optional path to CSV. Defaults to .linelogic/players_advanced_metrics.csv

    Returns:
        DataFrame with columns [season, team, team_weighted_PER, team_weighted_BPM,
        team_weighted_WS48, team_minutes_total]
    """
    default_path = Path(".linelogic/players_advanced_metrics.csv")
    path = Path(csv_path) if csv_path else default_path

    if not path.exists():
        logger.warning(
            f"Advanced metrics CSV not found at {path}. Skipping player-derived features."
        )
        return pd.DataFrame(
            columns=[
                "season",
                "team",
                "team_weighted_PER",
                "team_weighted_BPM",
                "team_weighted_WS48",
                "team_minutes_total",
            ]
        )

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.warning(f"Failed to read advanced metrics CSV at {path}: {e}. Skipping.")
        return pd.DataFrame(
            columns=[
                "season",
                "team",
                "team_weighted_PER",
                "team_weighted_BPM",
                "team_weighted_WS48",
                "team_minutes_total",
            ]
        )

    required_cols = {"season", "team", "player", "minutes", "PER", "BPM", "WS48"}
    missing = required_cols - set(df.columns)
    if missing:
        logger.warning(
            f"Advanced metrics CSV missing columns: {missing}. Skipping player-derived features."
        )
        return pd.DataFrame(
            columns=[
                "season",
                "team",
                "team_weighted_PER",
                "team_weighted_BPM",
                "team_weighted_WS48",
                "team_minutes_total",
            ]
        )

    # Clean types
    df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce").fillna(0.0)
    df["PER"] = pd.to_numeric(df["PER"], errors="coerce").fillna(0.0)
    df["BPM"] = pd.to_numeric(df["BPM"], errors="coerce").fillna(0.0)
    df["WS48"] = pd.to_numeric(df["WS48"], errors="coerce").fillna(0.0)

    # Aggregate to team-season
    grouped = df.groupby(["season", "team"], as_index=False).apply(
        _aggregate_team_metrics
    )
    # "apply" with as_index=False returns indices in the index; reset
    if isinstance(grouped.index, pd.MultiIndex) or grouped.index.name is not None:
        grouped = grouped.reset_index(drop=True)

    logger.info(
        f"Loaded advanced metrics for {grouped['team'].nunique()} teams across {grouped['season'].nunique()} seasons."
    )
    return grouped


def _aggregate_team_metrics(g: pd.DataFrame) -> pd.Series:
    total_minutes = g["minutes"].sum()
    if total_minutes <= 0:
        return pd.Series(
            {
                "season": g["season"].iloc[0],
                "team": g["team"].iloc[0],
                "team_weighted_PER": 0.0,
                "team_weighted_BPM": 0.0,
                "team_weighted_WS48": 0.0,
                "team_minutes_total": 0.0,
            }
        )

    weighted_PER = (g["PER"] * g["minutes"]).sum() / total_minutes
    weighted_BPM = (g["BPM"] * g["minutes"]).sum() / total_minutes
    weighted_WS48 = (g["WS48"] * g["minutes"]).sum() / total_minutes

    return pd.Series(
        {
            "season": g["season"].iloc[0],
            "team": g["team"].iloc[0],
            "team_weighted_PER": float(weighted_PER),
            "team_weighted_BPM": float(weighted_BPM),
            "team_weighted_WS48": float(weighted_WS48),
            "team_minutes_total": float(total_minutes),
        }
    )
