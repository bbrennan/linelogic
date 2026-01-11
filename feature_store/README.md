# Feast Feature Store

This directory contains the Feast feature store configuration for LineLogic NBA predictions.

## Overview

Feast provides:
- **Feature consistency** between training and inference
- **Point-in-time correct** feature retrieval (no data leakage)
- **Feature versioning** with metadata tracking
- **Online/offline store** separation for performance

## Directory Structure

```
feature_store/
├── feature_store.yaml   # Feast configuration (registry, stores)
├── features.py          # Feature view definitions
├── data/                # Feast registry and online store (auto-created)
│   ├── registry.db      # Feature metadata registry (SQLite)
│   └── online_store.db  # Online feature cache (SQLite)
└── README.md           # This file
```

## Setup

1. **Initialize feature store** (first time only):
   ```bash
   cd feature_store
   feast apply
   ```

2. **Materialize features** (load offline → online store):
   ```bash
   feast materialize-incremental $(date +%Y-%m-%d)
   ```

## Feature Views

### `team_season_stats`
Current season performance stats for NBA teams.

**Entity**: `team` (team_id)  
**TTL**: 1 day (refresh daily)  
**Fields**:
- `games_played`, `wins`, `losses`, `win_pct`
- `pts_per_game`, `opp_pts_per_game`
- `net_rating`, `pace`
- `off_3pa_rate`, `def_opp_3pa_rate`

**Source**: `.linelogic/features/team_season_stats.parquet`  
**Update**: Daily via `scripts/infer_daily.py`

## Usage in Training

```python
from feast import FeatureStore
import pandas as pd

store = FeatureStore(repo_path="feature_store")

# Historical features for training (point-in-time correct)
entity_df = pd.DataFrame({
    "team_id": [1, 2, 3],
    "event_timestamp": ["2024-01-10", "2024-01-10", "2024-01-10"],
})

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["team_season_stats:win_pct", "team_season_stats:net_rating"],
).to_df()
```

## Usage in Inference

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_store")

# Online features for low-latency inference
features = store.get_online_features(
    entity_rows=[{"team_id": 1}, {"team_id": 2}],
    features=["team_season_stats:win_pct", "team_season_stats:net_rating"],
).to_dict()
```

## Maintenance

- **Daily**: `feast materialize-incremental` after team stats update
- **Weekly**: Review feature freshness with `feast feature-views list`
- **Monthly**: Archive old registry versions for audit trail

## References

- [Feast Documentation](https://docs.feast.dev/)
- [Point-in-Time Joins](https://docs.feast.dev/getting-started/concepts/point-in-time-joins)
- [Feature Views](https://docs.feast.dev/getting-started/concepts/feature-view)
