# LineLogic POC - Quick Reference Card

*Print this and post it on your desk*

---

## 🚀 DAILY WORKFLOW (5 minutes)

### **8:00 AM - Generate Predictions**
```bash
python scripts/infer_daily.py --verbose --output docs/status/daily/predictions_$(date +%Y-%m-%d).csv
```
- ✓ Check for 4-8 games
- ✓ Note any TIER 1 predictions (high confidence)
- ✓ Flag TIER 4 games (back-to-back - use caution)

### **After 11 PM - Log Results**
- Add actual outcomes to `docs/status/predictions_log.csv`
- One line per game
- Mark `actual_home_win` as TRUE/FALSE

### **Every Monday - Validation Report**
```bash
python scripts/validate_predictions.py --predictions docs/status/predictions_log.csv \
  --by-tier --by-team --by-bucket
```
- Check TIER 1 accuracy ≥70%
- Flag any high-confidence errors
- Email report to team

---

## 📊 CONFIDENCE TIER GUIDE

| Tier | Trust Level | Action |
|------|-------------|--------|
| **TIER 1** | 🟢 HIGH | Use predictions directly |
| **TIER 2** | 🟡 MEDIUM-HIGH | Use with external validation |
| **TIER 3** | 🟡 MEDIUM | Use as tiebreaker |
| **TIER 4** | 🔴 LOW | Cross-check externally |

---

## 🎯 DECISION TREE

```
TIER 1 + Pred ≥55% → HOME FAVORED (use model)
TIER 1 + Pred 45-55% → CLOSE GAME (use model cautiously)
TIER 1 + Pred <45% → AWAY FAVORED (use model)

TIER 2 → Check injury reports, verify decision

TIER 4 → DO NOT rely on model alone
```

---

## 📋 EXAMPLE PREDICTIONS

```
BOS (home, 3d rest) vs LAL
→ TIER 1 | Pred 62% | USE MODEL → BOS favored

WSH (home, 1d rest) vs PHI
→ TIER 4 | Pred 48% | CROSS-CHECK → Don't rely on model
```

---

## ⚠️ RED FLAGS

| Issue | Action |
|-------|--------|
| TIER 1 accuracy < 70% | Check data quality; retrain |
| Multiple high-conf errors (>65%) | Investigate features |
| API error (no games) | Check BALLDONTLIE_API_KEY |
| Same team wrong repeatedly | Manual override; note in log |

---

## 📞 NEED HELP?

| Problem | See File |
|---------|----------|
| Daily workflow confused | [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) |
| Validation question | [VALIDATION_FRAMEWORK.md](VALIDATION_FRAMEWORK.md) |
| Retraining | [TRAIN_QUICK_START.md](../training/TRAIN_QUICK_START.md) |
| Model details | [ENHANCED_MODEL_SUMMARY.md](../model/ENHANCED_MODEL_SUMMARY.md) |

---

## 🔧 TROUBLESHOOTING

```bash
# Verify model loaded
ls .linelogic/nba_model_v1.0.0.pkl

# Check API key
echo $BALLDONTLIE_API_KEY

# Test predictions
python scripts/infer_daily.py --verbose

# Validate performance
python scripts/validate_predictions.py --predictions docs/status/predictions_log.csv
```

---

## 📅 MONTHLY CALENDAR

| Day | Task | Command |
|-----|------|---------|
| Mon (wk 1) | Weekly validation | `validate_predictions.py` |
| Mon (wk 2) | Weekly validation | `validate_predictions.py` |
| Mon (wk 3) | Weekly validation | `validate_predictions.py` |
| Mon (wk 4) | **Retrain model** | `train_offline.py --no-synthetic --stratified` |
| Every day | Generate predictions | `infer_daily.py` |
| Every night | Log results | Manual |

---

## ✅ LAUNCH CHECKLIST (Jan 11)

- [ ] `.venv` activated
- [ ] Model file exists
- [ ] First predictions run successful
- [ ] Read [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
- [ ] Ready to track outcomes

---

**Model Accuracy:** 68.98%  
**TIER 1 Target:** ≥70%  
**Data Window:** 2024-2025 regular season  
**Status:** 🟢 READY FOR DEPLOYMENT

---

*Quick Reference v1.0 | Jan 10, 2026*
