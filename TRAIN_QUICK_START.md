# Training Quick Start Card

## TL;DR - Run Training Now

### Option 1: Jupyter (Best for first run)
```bash
cd /Users/bbrennan/Desktop/LineLogic
jupyter notebook notebooks/train_nba_model_offline.ipynb
# Run all cells top-to-bottom
# Takes ~5-10 minutes
```

### Option 2: CLI (Best for repeated runs)
```bash
cd /Users/bbrennan/Desktop/LineLogic
python scripts/train_offline.py
# Takes ~5-10 minutes first time
# Use --cache-only for subsequent runs: python scripts/train_offline.py --cache-only
```

---

## What Gets Trained

**Input Data**: 2,500+ NBA games (2022-2024)  
**Features**: 15 (Elo ratings, rolling stats, rest days, matchups)  
**Model**: Logistic Regression  
**Output**: Win probability predictions (0-1 for home team)

---

## Results Location

After training, check:
```bash
.linelogic/
├── nba_model_v1.0.0.pkl                 ← Model ready for deployment
├── nba_model_v1.0.0_metadata.json       ← Metrics: accuracy, log loss, Brier
└── nba_model_v1.0.0_report.txt          ← Technical review document
```

---

## Success Criteria

✅ Test Accuracy > 55%  
✅ Test Log Loss < 0.60  
✅ Test Brier Score < 0.20  
✅ Low train/val overfitting gap

---

## Next Steps After Training

1. Review technical report in `.linelogic/nba_model_v1.0.0_report.txt`
2. If metrics look good:
   - Run backtest: `python -m linelogic backtest` (TBD)
   - Clear stub data: `python scripts/clear_stub_data.py`
   - Deploy: Update `src/linelogic/cli/recommend.py` to load trained model
   - Test: `python -m linelogic recommend-daily`

---

## Full Documentation

- [Model Training Guide](docs/14_model_training_guide.md) - Detailed walkthrough
- [Modeling Strategy](docs/13_modeling_strategy.md) - Overall approach & roadmap
- [Training Status](TRAINING_READY.md) - Complete TODO summary

---

## Troubleshooting

**"API Rate Limit"** → Free tier is 5 req/min. Wait 1 minute and retry.

**"Feature engineer error"** → Ensure `src/linelogic/features/engineer.py` is up to date.

**"Results too low"** → Check logs for data quality issues. Model targets 55% accuracy.

**"Can't run Jupyter"** → Use CLI instead: `python scripts/train_offline.py`

---

## Commands Cheat Sheet

```bash
# Train
python scripts/train_offline.py

# Train with cached data (faster)
python scripts/train_offline.py --cache-only

# Clear stub data before deployment
python scripts/clear_stub_data.py

# Test integration after deployment
python -m linelogic recommend-daily

# View technical report
cat .linelogic/nba_model_v1.0.0_report.txt

# Check model metadata
cat .linelogic/nba_model_v1.0.0_metadata.json | jq '.test_metrics'
```

---

**Status**: 🟢 Ready to train. All infrastructure in place.

**Estimated Time**: 5-10 minutes per training run.

**Questions?** See [TRAINING_READY.md](TRAINING_READY.md) for full documentation.
