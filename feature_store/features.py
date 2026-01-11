"""
Feast feature definitions for NBA win prediction.

This module defines feature views for team season stats used in model inference.
Features are versioned and tracked for reproducibility.
"""

from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int32, String


# Entity definitions
team = Entity(
    name="team",
    join_keys=["team_id"],
    description="NBA team entity",
)

# Data source - team season stats from CSV/parquet
team_season_stats_source = FileSource(
    path="../.linelogic/features/team_season_stats.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# Feature view - team season performance stats
team_season_stats_fv = FeatureView(
    name="team_season_stats",
    entities=[team],
    ttl=timedelta(days=1),  # Features expire after 1 day (refresh daily)
    schema=[
        Field(name="games_played", dtype=Int32),
        Field(name="wins", dtype=Int32),
        Field(name="losses", dtype=Int32),
        Field(name="win_pct", dtype=Float64),
        Field(name="pts_per_game", dtype=Float64),
        Field(name="opp_pts_per_game", dtype=Float64),
        Field(name="net_rating", dtype=Float64),
        Field(name="pace", dtype=Float64),
        Field(name="off_3pa_rate", dtype=Float64),
        Field(name="def_opp_3pa_rate", dtype=Float64),
    ],
    source=team_season_stats_source,
    tags={"team": "linelogic", "version": "v1.0"},
)
