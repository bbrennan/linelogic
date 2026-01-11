# MLOps Quick Reference

Quick commands for daily MLOps workflows.

## MLflow Experiment Tracking

### Train Model (Auto-logs to MLflow)
```bash
python scripts/train_offline.py --output-dir models/
```

### View Experiments in Browser
```bash
mlflow ui --port 5000
# Open: http://localhost:5000
```

### Load Model by Stage
```python
import mlflow
model = mlflow.sklearn.load_model("models:/nba_win_predictor/production")
```

### Load Model by Run ID
```python
model = mlflow.sklearn.load_model("runs:/abc123def456/model")
```

### Promote Model to Production
```python
from mlflow.tracking import MlflowClient
client = MlflowClient()
client.transition_model_version_stage(
    name="nba_win_predictor",
    version=2,
    stage="Production"
)
```

## Feast Feature Store

### Initialize (First Time Only)
```bash
cd feature_store
feast apply
```

### Materialize Features (Daily)
```bash
feast materialize-incremental $(date +%Y-%m-%d)
```

### Get Historical Features (Training)
```python
from feast import FeatureStore
store = FeatureStore(repo_path="feature_store")
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["team_season_stats:win_pct", "team_season_stats:net_rating"]
).to_df()
```

### Get Online Features (Inference)
```python
features = store.get_online_features(
    entity_rows=[{"team_id": 1}, {"team_id": 2}],
    features=["team_season_stats:win_pct"]
).to_dict()
```

## A/B Testing

### Initialize Router
```python
from linelogic.inference import ABTestRouter
router = ABTestRouter(staging_percentage=10.0)
```

### Route Request
```python
stage = router.route(user_id="game_123_home")  # "staging" or "production"
model = mlflow.sklearn.load_model(f"models:/nba_win_predictor/{stage}")
```

### Log Outcome
```python
router.log_outcome(user_id="game_123_home", prediction=0.65, actual=True)
```

### Compare Variants
```python
print(router.compare_variants())
# Shows staging vs production metrics, recommends winner
```

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suite
```bash
pytest tests/test_ab_router.py -v
pytest tests/test_contracts.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src/linelogic --cov-report=html
```

## Data Ingestion

### Validate Ingest Pipeline
```bash
python scripts/validate_ingest.py
```

### View Ingest Manifests
```bash
ls -lh .linelogic/manifests/
```

## Monitoring (Evidently - Coming Soon)

### Check Data Drift
```bash
python scripts/monitor_drift.py --date $(date +%Y-%m-%d)
```

### View Drift Dashboard
```bash
python scripts/generate_drift_dashboard.py
```

## Git Workflow

### Start New Feature
```bash
git checkout develop
git pull
git checkout -feature/mlflow-integration
```

### Merge to Develop
```bash
git checkout develop
git merge feature/mlflow-integration
git push origin develop
```

### Create PR to Main
```bash
# On GitHub: develop → main
# CI validates data contracts + runs tests
```

## Troubleshooting

### MLflow: No experiments found
```bash
mlflow experiments list
# If empty, train once to create experiment
```

### Feast: Registry not found
```bash
cd feature_store
feast apply  # Recreates registry
```

### A/B Router: No outcomes logged
```bash
ls .linelogic/ab_logs/
# Check JSONL files exist
```

### Training: API rate limit
```bash
# Upgrade to paid tier ($20/month)
# Or reduce data range in train_offline.py
```

## File Locations

- **MLflow**: `mlruns/` (auto-created)
- **Feast Registry**: `feature_store/data/registry.db`
- **Feast Online Store**: `feature_store/data/online_store.db`
- **A/B Logs**: `.linelogic/ab_logs/outcomes_*.jsonl`
- **Ingest Manifests**: `.linelogic/manifests/*.json`
- **Models**: `models/nba_model_v1.0.0.pkl`

## Daily Workflow

1. **Morning**: Check drift report from yesterday
2. **Ingest**: Fetch today's games, validate, save manifest
3. **Features**: Update team stats, materialize to Feast
4. **Predict**: Load model via A/B router, generate picks
5. **Monitor**: Check A/B metrics, staging vs production
6. **Weekly**: Retrain model if performance degraded

## Documentation

- **MLflow**: [docs/17_mlflow_tracking.md](docs/17_mlflow_tracking.md)
- **Architecture**: [docs/19_mlops_architecture.md](docs/19_mlops_architecture.md)
- **Feast**: [feature_store/README.md](feature_store/README.md)
- **Implementation**: [MLOPS_IMPLEMENTATION.md](MLOPS_IMPLEMENTATION.md)
