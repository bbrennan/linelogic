# Model Training Guide

**Status**: Training infrastructure ready for execution  
**Last Updated**: 2026-01-10

---

## Quick Start

### Option 1: Jupyter Notebook (Recommended for Development)

Interactive cell-by-cell execution with visualizations and detailed documentation.

```bash
# Navigate to project root
cd /Users/bbrennan/Desktop/LineLogic

# Launch Jupyter
jupyter notebook notebooks/train_nba_model_offline.ipynb
```

**Timeline**: ~5-10 minutes (API rate limits)

**Output**:
- `.linelogic/nba_model_v1.0.0.pkl` - Trained model
- `.linelogic/nba_model_v1.0.0_metadata.json` - Metadata
- `.linelogic/nba_model_v1.0.0_report.txt` - Technical report

---

### Option 2: CLI Script (Production)

Automated training from command line with caching support.

```bash
# First run: fetch data from API + train
python scripts/train_offline.py

# Subsequent runs: use cached data
python scripts/train_offline.py --cache-only

# Custom parameters
python scripts/train_offline.py \
    --start-season 2022 \
    --end-season 2024 \
    --output-dir .linelogic
```

**Features**:
- Automatic data caching to `.linelogic/games_cache.parquet`
- Reuse cached data without API calls
- Hyperparameter search (C = [0.001, 0.01, 0.1, 1.0, 10.0])
- Full evaluation metrics

---

## Training Process

### Step 1: Data Fetching

**Source**: BALLDONTLIE API (free tier)  
**Seasons**: 2022-2023, 2023-2024, 2024-2025 (partial)  
**Games**: ~2,500 completed games  
**Rate Limit**: 5 requests/minute (free tier)  
**Time**: ~2-3 minutes

```
2022 season: 1,082 games
2023 season: 1,082 games
2024 season: ~600 games (partial)
```

### Step 2: Feature Engineering

Transforms raw game data into 15 ML features using the `FeatureEngineer` class.

**Features**:
- **Elo Ratings** (3): home_elo, away_elo, elo_diff
- **Team Stats** (4): win_rate_L10, point_diff_L10 (both teams)
- **Schedule** (4): rest_days, back-to-back (both teams)
- **Matchup** (3): h2h_wins, streaks (both teams)
- **Context** (1): is_home

**Processing**:
- Chronological order (no look-ahead bias)
- Elo ratings updated after each game
- Rolling statistics computed from game history
- Missing values filled with 0

### Step 3: Data Split

**Time-based splits** (prevent look-ahead bias):

| Split | Date Range | Games | % | Purpose |
|-------|-----------|-------|---|---------|
| **Train** | 2022-01-01 to 2023-12-31 | ~1,600 | 64% | Model training |
| **Validation** | 2024-01-01 to 2024-06-30 | ~400 | 16% | Hyperparameter tuning |
| **Test** | 2024-07-01+ | ~500 | 20% | Final evaluation |

### Step 4: Model Training

**Algorithm**: Logistic Regression (scikit-learn)

**Hyperparameter Search**:
- Parameter: `C` (inverse regularization strength)
- Values: [0.001, 0.01, 0.1, 1.0, 10.0]
- Metric: Log loss on validation set
- Solver: lbfgs
- Max iterations: 1000

**Loss Function**:
```
Log Loss = -1/N * Σ[y*log(ŷ) + (1-y)*log(1-ŷ)]

Lower is better. Target: <0.60
```

### Step 5: Evaluation

**Metrics** (all three splits):

1. **Log Loss** (target: <0.60)
   - Penalizes confident wrong predictions
   - Range: [0, ∞)
   - Useful for probability calibration

2. **Brier Score** (target: <0.20)
   - Mean squared error of predicted probabilities
   - Range: [0, 1]
   - Directly interpretable

3. **Accuracy** (target: >55%)
   - Fraction of correct binary predictions
   - Binary classification accuracy
   - Easy to interpret

---

## Expected Results

Based on initial data analysis:

| Metric | Target | Expected |
|--------|--------|----------|
| Test Log Loss | <0.60 | 0.55-0.58 |
| Test Brier Score | <0.20 | 0.18-0.21 |
| Test Accuracy | >55% | 55-58% |
| Train/Val Gap | Small | <0.05 (well-generalized) |

---

## Output Files

After training, three files are created in `.linelogic/`:

### 1. `nba_model_v1.0.0.pkl` (Model)
```python
# Usage:
import pickle
with open('.linelogic/nba_model_v1.0.0.pkl', 'rb') as f:
    data = pickle.load(f)
    model = data['model']
    scaler = data['scaler']

# Predict
proba = model.predict_proba(X_scaled)[:, 1]  # [0, 1] = probability of home win
```

**Size**: ~50 KB (LogisticRegression coefficients)

### 2. `nba_model_v1.0.0_metadata.json` (Metadata)
```json
{
  "version": "v1.0.0_20260110",
  "created_at": "2026-01-10T...",
  "features": [...],
  "train_metrics": {"log_loss": 0.567, ...},
  "val_metrics": {...},
  "test_metrics": {...},
  "hyperparameters": {"C": 1.0, "max_iter": 1000}
}
```

### 3. `nba_model_v1.0.0_report.txt` (Technical Report)
Comprehensive report with:
- Dataset summary
- Model architecture
- Hyperparameter tuning results
- Performance metrics
- Feature importances
- Interpretation guidance

---

## Deployment

After training completes successfully:

### 1. Review Model Performance

Check `.linelogic/nba_model_v1.0.0_report.txt` for:
- ✅ Test accuracy >55%
- ✅ Test log loss <0.60
- ✅ Low train/val gap (good generalization)

### 2. Clear Stub Data

```bash
python scripts/clear_stub_data.py
```

This deletes all 52% stub predictions before deploying the real model.

### 3. Update recommend-daily Command

Edit `src/linelogic/cli/recommend.py`:
- Update `model_version` to `"v1.0.0_20260110"`
- Update `predict()` function to load `.linelogic/nba_model_v1.0.0.pkl`
- Replace stub 52% with actual model predictions

### 4. Test Integration

```bash
# Run recommend-daily with new model
python -m linelogic recommend-daily

# Check .linelogic/linelogic.db
sqlite3 .linelogic/linelogic.db "SELECT COUNT(*), model_prob FROM recommendations WHERE model_version = 'v1.0.0_20260110' GROUP BY model_prob"
```

### 5. Run Live

Model is now deployed! Next steps:
- [ ] Run daily picks with new model
- [ ] Monitor dashboard for results
- [ ] Compare live performance vs backtest
- [ ] Document findings in technical report

---

## Troubleshooting

### "API Rate Limit Exceeded"
- BALLDONTLIE free tier: 5 req/min
- Solution: Wait 1 minute, retry
- Or: Get API key from balldontlie.io for higher limits

### "Feature engineer_features() takes 1 positional argument"
- Ensure `features/engineer.py` is up to date
- Run: `git pull origin main`

### "Log loss >0.70 (too high)"
- Model may be poorly calibrated
- Check for data quality issues
- Try C=0.01 or C=0.001 (more regularization)

### "Accuracy <53% (below target)"
- Features may not be predictive
- Check for data leakage
- Verify feature engineering is correct
- Consider additional features (home/away splits, coach, injuries, etc.)

---

## Hyperparameter Tuning Guide

### Adjusting C (Regularization Strength)

- **C=0.001** (High regularization)
  - Pros: Reduces overfitting
  - Cons: May underfit if model is not complex
  - Use: If train/val gap is large

- **C=0.01** (Medium-high)
  - Pros: Good default
  - Cons: May still overfit

- **C=0.1** (Medium)
  - Pros: Balanced
  - Cons: Depends on data

- **C=1.0** (Low regularization)
  - Pros: Allows model to fit data closely
  - Cons: Higher risk of overfitting

- **C=10.0** (Very low)
  - Pros: Maximum flexibility
  - Cons: High overfitting risk
  - Use: Only if validation loss continues to improve

**Strategy**:
1. Start with default C=1.0
2. If validation loss is high, try C=[0.001, 0.01, 0.1]
3. If test accuracy <53%, try C=10.0
4. Pick the C value that minimizes validation log loss

---

## Advanced: Custom Training

### Change Feature Set

Edit `scripts/train_offline.py`:

```python
feature_cols = [
    "home_elo",
    "away_elo",
    # Add more features
    "home_win_rate_L10",
    # etc
]
```

### Change Data Split

Edit split dates:

```python
train_cutoff = pd.Timestamp('2024-01-01')
val_cutoff = pd.Timestamp('2024-07-01')
```

### Train on Different Seasons

```bash
python scripts/train_offline.py --start-season 2021 --end-season 2024
```

---

## Next Steps (Post-Training)

1. **Run Backtest** (TODO)
   - Walk-forward backtest on 2024 data
   - Compute ROI, Sharpe ratio, max drawdown
   - Document results

2. **Deploy Model** (TODO)
   - Update `recommend.py` to load v1.0.0
   - Clear stub data
   - Run `recommend-daily` command

3. **Monitor Performance** (TODO)
   - Track live metrics on Streamlit dashboard
   - Compare live vs backtest performance
   - Iterate if needed

4. **Continuous Learning** (TODO)
   - Retrain monthly with new data
   - Track model drift
   - Implement retraining schedule

---

## Contact & Support

Questions? Check:
- `docs/13_modeling_strategy.md` - Strategy & approach
- `src/linelogic/features/engineer.py` - Feature definitions
- `src/linelogic/models/elo.py` - Elo implementation
- `tests/test_elo.py` - Unit tests
