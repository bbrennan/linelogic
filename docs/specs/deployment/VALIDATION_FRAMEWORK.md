# A/B Testing & Prediction Validation Framework

**Purpose:** Track model predictions vs actual outcomes to validate confidence tier calibration and identify improvement areas.

---

## Quick Start: Daily Tracking

### 1. Generate Daily Predictions (8 AM)

```bash
python scripts/infer_daily.py --verbose --output predictions_$(date +%Y-%m-%d).csv
```

**Output:** CSV with these columns:
```
date,home_team,away_team,pred_home_win_prob,pred_away_win_prob,
home_team_rest_days,away_team_rest_days,confidence_tier,recommendation
```

### 2. Fill in Actual Results (After 11 PM)

Manually add column `actual_home_win` (TRUE/FALSE) to the CSV:

```bash
# Template: append this column to predictions_YYYY-MM-DD.csv
actual_home_win
TRUE
FALSE
TRUE
```

### 3. Consolidate Weekly (Every Monday)

```bash
# Merge week's predictions into one log
cat predictions_2026-01-*.csv > predictions_log_week_01.csv
```

---

## Weekly Validation Report

### Generate Report

```bash
python scripts/validate_predictions.py \
  --predictions predictions_log_week_01.csv \
  --by-tier --by-team --by-bucket
```

### Expected Output

```
================================================================================
MODEL VALIDATION REPORT
================================================================================

OVERALL METRICS (35 games):
  Accuracy:                68.57%
  Log Loss:                0.6120
  Brier Score:             0.2095
  Baseline Home Win Rate:  54.29%

--------------------------------------------------------------------------------
ACCURACY BY CONFIDENCE TIER:
--------------------------------------------------------------------------------
✓ TIER 1              | Accuracy:  71.43% | n= 21 | Avg Pred:  54.82% | Actual Win Rate: 57.14%
✓ TIER 2              | Accuracy:  66.67% | n=  9 | Avg Pred:  56.39% | Actual Win Rate: 55.56%
⚠ TIER 4 (CAUTION)   | Accuracy:  50.00% | n=  5 | Avg Pred:  48.20% | Actual Win Rate: 40.00%
```

### Key Metrics to Track

| Metric | Target | Action if Missed |
|--------|--------|------------------|
| **TIER 1 Accuracy** | ≥70% | Model performing as expected |
| **TIER 2 Accuracy** | 68-70% | Monitor; may need validation rules |
| **TIER 4 Accuracy** | <50% | Expected; do not use for direct bets |
| **False Positive Rate (TIER 1, >65% confidence)** | <5% | Retrain or lower confidence threshold |
| **Calibration Error (avg pred vs actual)** | <5% | Model well-calibrated |

---

## Prediction Log Template

Create file: `docs/status/predictions_log.csv`

```csv
date,home_team,away_team,pred_home_win_prob,confidence_tier,home_team_rest_days,actual_home_win,tracked_yn,notes
2026-01-11,BOS,LAL,0.6234,TIER 1 (HIGH CONFIDENCE),3,TRUE,Y,Model correct; strong home edge
2026-01-11,MIA,CLE,0.4891,TIER 4 (CAUTION),1,FALSE,N,Skipped; back-to-back weakness
2026-01-12,PHI,WAS,0.5520,TIER 1 (HIGH CONFIDENCE),2,TRUE,Y,As expected
2026-01-12,GSW,DEN,0.4750,TIER 2 (MEDIUM-HIGH),3,FALSE,Y,Model underestimated DEN; investigate
```

**Columns:**
- `date` (YYYY-MM-DD)
- `home_team` (3-letter code)
- `away_team` (3-letter code)
- `pred_home_win_prob` (0.0-1.0)
- `confidence_tier` (TIER 1-4)
- `home_team_rest_days` (1-4+)
- `actual_home_win` (TRUE/FALSE)
- `tracked_yn` (Y/N – did you track this game?)
- `notes` (any observations)

---

## Validation Scenarios

### Scenario 1: All TIER 1 games score 70%+

✅ **Action:** Continue normal operations. Model is well-calibrated.

### Scenario 2: TIER 1 accuracy drops to 65%

⚠️ **Actions:**
1. Check for data quality issues in last week's games
2. Retrain model with fresh BALLDONTLIE data
3. Investigate if structural changes (trades, injuries, system changes) affected performance
4. Review feature engineering logic

### Scenario 3: TIER 4 (1-day rest) accuracy improves to 55%

📊 **Actions:**
1. This suggests model may be improving on back-to-back weakness
2. Track for 2-4 weeks to see if trend continues
3. If consistent, update confidence tier assignments
4. Consider retraining with updated rest buckets

### Scenario 4: High-confidence errors cluster in one team

🚨 **Actions:**
1. Investigate team (trades, coaching changes, injury wave)
2. Manually override model for that team until resolved
3. Add team-specific notes to tracking log
4. Plan feature engineering fix (e.g., add injury flags)

---

## Monthly Validation Checklist

**Every First Monday of Month:**

- [ ] Consolidate all weekly logs into monthly_predictions_YYYY-MM.csv
- [ ] Run full validation report:
  ```bash
  python scripts/validate_predictions.py \
    --predictions monthly_predictions_2026-01.csv \
    --by-tier --by-team --by-bucket \
    --export-json validation_report_2026-01.json
  ```

- [ ] Check TIER 1 accuracy (target: ≥70%)
- [ ] Check calibration error (target: <5%)
- [ ] Review false positives (high-confidence errors, target: <5)
- [ ] Compare to prior month (track trend)
- [ ] Document findings in `docs/status/reports/validation_log.md`

**Decision Points:**

| Finding | Action |
|---------|--------|
| Accuracy ↑ 2%+ | Continue current approach |
| Accuracy ↓ 1-2% | Investigate; retrain if needed |
| Accuracy ↓ 3%+ | 🚨 Emergency retraining; review data quality |
| Calibration error > 10% | Retrain or adjust confidence thresholds |
| One team consistently wrong | Manual intervention or feature adjustment |

---

## Advanced Analysis: Segment Calibration

### 1. By Team Pairing

```python
import pandas as pd

log = pd.read_csv("docs/status/predictions_log.csv")

# Accuracy by specific matchups
matchup_accuracy = log.groupby(['home_team', 'away_team']).agg({
    'actual_home_win': ['count', 'mean']
})

print(matchup_accuracy)
```

### 2. By Rest Pattern

```python
# Accuracy by home team rest days
rest_accuracy = log.groupby('home_team_rest_days').agg({
    'actual_home_win': 'mean',
    'date': 'count'
})

print(rest_accuracy)
```

### 3. By Time Window

```python
# Accuracy by week or month
log['week'] = pd.to_datetime(log['date']).dt.strftime('%Y-W%W')
weekly_accuracy = log.groupby('week').agg({
    'actual_home_win': ['count', 'mean']
})

print(weekly_accuracy)
```

---

## Production Monitoring Dashboard

### Daily (Email Summary)

```
=== DAILY PREDICTION SUMMARY ===
Date: 2026-01-11
Games Scored: 8
TIER 1: 5 games
TIER 2: 2 games
TIER 4: 1 game

Outcomes (so far):
✓ TIER 1: 4/5 correct (80%)
✓ TIER 2: 1/2 correct (50%)
⚠ TIER 4: 0/1 correct (0% - expected)

Status: ✓ Running normally
Next: Weekly report Monday 1/13
```

### Weekly (Full Report)

```
=== WEEKLY VALIDATION REPORT ===
Week Ending: 2026-01-17
Total Predictions: 35
Overall Accuracy: 68.57%

BY TIER:
  TIER 1: 71.4% (21 games)
  TIER 2: 66.7% (9 games)
  TIER 4: 50.0% (5 games)

STATUS:
✓ All tiers within expected ranges
✓ No high-confidence errors (>65% confidence)
✓ Baseline calibrated to actual (54.3% pred vs 54.3% actual)

RECOMMENDATION: Continue normal operations
Next Review: 2026-01-24
```

---

## Exporting Reports

### JSON Export (Full Report)

```bash
python scripts/validate_predictions.py \
  --predictions docs/status/predictions_log.csv \
  --by-tier --by-team --by-bucket \
  --export-json validation_report.json
```

**Output:** JSON with all metrics, ready for dashboards or further analysis

### CSV Export (Tier Metrics)

```bash
python scripts/validate_predictions.py \
  --predictions docs/status/predictions_log.csv \
  --export-csv tier_metrics_weekly.csv
```

**Output:** CSV with one row per tier (for Excel tracking)

---

## Troubleshooting Validation

### "actual_home_win column not found"

**Solution:** Manually add column to predictions_YYYY-MM-DD.csv:
```csv
...,recommendation,actual_home_win
...,USE MODEL,TRUE
...,CROSS-CHECK,FALSE
```

### High variance in TIER 1 accuracy (week-to-week)

**Likely cause:** Small sample size (<20 games/week)
- Wait 2-4 weeks of data to smooth
- Use monthly reports instead of weekly
- Consider combining TIER 1 + TIER 2 for larger sample

### One team consistently mispredicted

**Actions:**
1. Filter predictions for that team: `log[log['home_team'] == 'BOS']`
2. Check if team changed (trades, coaching, system)
3. Add team-specific note to model metadata
4. Consider team-specific feature adjustments in retraining

---

## Success Criteria for POC (Jan 11 - Feb 10)

| Criterion | Target | Status |
|-----------|--------|--------|
| Generate daily predictions | 100% success rate | 🔄 Tracking |
| TIER 1 accuracy | ≥70% | 🔄 Tracking |
| False positive rate (TIER 1) | <5% | 🔄 Tracking |
| Weekly reports | On schedule | 🔄 Tracking |
| Data quality issues | <1 per week | 🔄 Tracking |
| User confidence | High | 🔄 Tracking |

---

## Files & Artifacts

```
docs/status/predictions_log.csv        # Main tracking log (append daily)
docs/status/daily/predictions_2026-01-11.csv   # Daily predictions (auto-generated)
monthly_predictions_2026-01.csv        # Monthly consolidated
validation_report_2026-01.json         # Full validation report (JSON)
tier_metrics_weekly.csv                # Tier-level metrics (CSV)

scripts/
├── scripts/infer_daily.py             # Generate predictions
├── scripts/validate_predictions.py    # Validation analysis
└── VALIDATION_FRAMEWORK.md            # This file
```

---

**Last Updated:** Jan 10, 2026  
**Framework Version:** 1.0  
**Status:** 🟢 Ready for POC
