# POC Deployment Checklist - Jan 11, 2026

**Status:** 🟢 Ready to Launch

---

## PRE-LAUNCH (Jan 10, Evening)

### Verify Environment
- [ ] Python 3.11 installed: `python --version`
- [ ] `.venv` directory exists: `ls -la .venv`
- [ ] Required packages installed: `pip list | grep scikit-learn pandas numpy`

### Verify Model
- [ ] Model file exists: `ls -la .linelogic/nba_model_v1.0.0.pkl`
- [ ] Metadata file exists: `ls -la .linelogic/nba_model_v1.0.0_metadata.json`
- [ ] Model loads without error:
  ```bash
  python -c "import pickle; pickle.load(open('.linelogic/nba_model_v1.0.0.pkl', 'rb'))"
  # Should output nothing if successful
  ```

### Verify Scripts
- [ ] `scripts/infer_daily.py` exists and is executable
- [ ] `scripts/validate_predictions.py` exists and is executable
- [ ] Test import: `python scripts/infer_daily.py --help`

### Verify Documentation
- [ ] Read [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) ✓
- [ ] Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) ✓
- [ ] Printed or bookmarked QUICK_REFERENCE.md ✓

### Verify Data & Cache
- [ ] Games cache exists: `ls -la .linelogic/games_cache.csv`
- [ ] Team stats exist: `ls -la .linelogic/team_season_avgs.csv`
- [ ] Predictions log created: `ls -la docs/status/predictions_log.csv`

### Verify API Key
- [ ] BALLDONTLIE_API_KEY is set: `echo $BALLDONTLIE_API_KEY`
  - If empty, set it: `export BALLDONTLIE_API_KEY=your_key_here`
- [ ] Add to `.env` for persistence: `echo "BALLDONTLIE_API_KEY=..." >> .env`

### Final Test Run (Evening of Jan 10)
```bash
# Dry run of prediction script
python scripts/infer_daily.py --verbose --output test_predictions.csv

# Expected: 0-2 games (depends on date)
# Check output: head -5 test_predictions.csv
# Confirm columns present:
#   - date, home_team, away_team
#   - pred_home_win_prob, confidence_tier
#   - recommendation
```

- [ ] Test run successful
- [ ] Output format correct
- [ ] No errors

---

## LAUNCH DAY (Jan 11, 2026)

### 8:00 AM - Morning Kickoff

**Step 1: Setup**
```bash
cd /Users/bbrennan/Desktop/LineLogic
source .venv/bin/activate
```
- [ ] Confirm shell prompt shows `(.venv)`

**Step 2: Verify Date**
```bash
date
# Should show: Sat Jan 11 08:00:00 PST 2026
```
- [ ] Date is correct

**Step 3: Generate Predictions**
```bash
python scripts/infer_daily.py --verbose --output docs/status/daily/predictions_2026-01-11.csv
```
- [ ] Command runs without errors
- [ ] Output includes predictions count
- [ ] CSV file created: `ls -la docs/status/daily/predictions_2026-01-11.csv`

**Step 4: Review Predictions**
```bash
# Show prediction summary
cat docs/status/daily/predictions_2026-01-11.csv
```
- [ ] 4-8 games shown (typical for Saturday)
- [ ] Confidence tiers assigned (TIER 1, 2, 3, or 4)
- [ ] Probability values look reasonable (0.35-0.65 range mostly)

**Step 5: Log First Predictions**
```bash
# Append to tracking log
tail -n +2 docs/status/daily/predictions_2026-01-11.csv >> docs/status/predictions_log.csv
# (skip header row with tail -n +2)
```
- [ ] Predictions appended to `docs/status/predictions_log.csv`
- [ ] Verify: `tail -5 docs/status/predictions_log.csv`

**Step 6: Document in Spreadsheet/Notes**
Create entry for today:
```
Date: 2026-01-11
Games Scored: [count from output]
TIER 1 Games: [count]
TIER 4 Games: [count]
Status: ✓ Launched successfully
Notes: [any issues]
```
- [ ] Entry created
- [ ] Shared with team

### 8:30 AM - Team Notification

Send team message:
```
✓ POC Deployment Launched - Jan 11, 2026

First predictions generated for today's games.
Confidence tiers assigned per QUICK_REFERENCE.md.

Track your predictions throughout the day.
Merge results tomorrow morning into docs/status/predictions_log.csv.

Questions? See OPERATIONS_RUNBOOK.md or QUICK_REFERENCE.md
```
- [ ] Message sent

---

## EVENING (After 11 PM, Jan 11)

### Log Game Outcomes

**Step 1: Collect Results**
- [ ] Gather final scores for all predicted games

**Step 2: Update Predictions**
Add `actual_home_win` column to `predictions_2026-01-11.csv`:
```bash
# Edit file manually or use Python:
python << 'EOF'
import pandas as pd
df = pd.read_csv('docs/status/daily/predictions_2026-01-11.csv')
# Add actual_home_win column with TRUE/FALSE values
df['actual_home_win'] = [True, False, True, ...]  # Fill with actual results
df.to_csv('docs/status/daily/predictions_2026-01-11.csv', index=False)
print("✓ Updated predictions with actual results")
EOF
```
- [ ] `actual_home_win` column added
- [ ] All values filled (TRUE/FALSE)

**Step 3: Append to Log**
```bash
tail -n +2 docs/status/daily/predictions_2026-01-11.csv >> docs/status/predictions_log.csv
```
- [ ] Results appended to `docs/status/predictions_log.csv`

**Step 4: Quick Review**
```bash
tail -n +2 docs/status/predictions_log.csv | wc -l
# Should show: 1 (if first day)
```
- [ ] Results saved

---

## DAY 2-7 (Jan 12-17)

### Daily Routine

**Every Morning (8 AM):**
```bash
python scripts/infer_daily.py --verbose --output docs/status/daily/predictions_$(date +%Y-%m-%d).csv
```
- [ ] Jan 12 predictions ✓
- [ ] Jan 13 predictions ✓
- [ ] Jan 14 predictions ✓
- [ ] Jan 15 predictions ✓
- [ ] Jan 16 predictions ✓
- [ ] Jan 17 predictions ✓

**Every Evening (After 11 PM):**
- [ ] Log results
- [ ] Append to `docs/status/predictions_log.csv`

---

## WEEK 1 REVIEW (Monday, Jan 13)

### Run Validation Report

```bash
python scripts/validate_predictions.py \
  --predictions docs/status/predictions_log.csv \
  --by-tier --by-team --by-bucket
```
- [ ] Report runs without errors
- [ ] Output shows:
  - Total predictions scored
  - Overall accuracy
  - Accuracy by tier (TIER 1, 2, 3, 4)
  - Any high-confidence errors flagged

### Analyze Results

- [ ] TIER 1 accuracy ≥ 70% ✓ (or 🚨 if < 70%)
- [ ] No unexpected high-confidence errors
- [ ] Sample sizes reasonable (n ≥ 5 per tier)

### Document Findings

Create entry in `docs/status/reports/validation_log.md`:
```
## Week of Jan 11-17

**Overall Accuracy:** 68%
**TIER 1 Accuracy:** 71% ✓
**TIER 2 Accuracy:** 67%
**TIER 4 Accuracy:** 50% (expected)

**Findings:**
- Model performing as expected
- TIER 1 calibrated well
- Continue operations

**Next Review:** Jan 20
```
- [ ] Findings documented
- [ ] Shared with team

---

## MONTHLY RETRAINING (First Mon, Feb 3)

### Retrain Model

```bash
export BALLDONTLIE_API_KEY=<key>
python scripts/train_offline.py --no-synthetic --stratified
```
- [ ] Command runs (takes ~10 min)
- [ ] New model generated: `.linelogic/nba_model_v1.0.0.pkl`
- [ ] Metadata updated: `.linelogic/nba_model_v1.0.0_metadata.json`
- [ ] Accuracy metrics reported

### Validate Retrained Model

```bash
# Quick test
python scripts/infer_daily.py --verbose
```
- [ ] New model loads
- [ ] Predictions generate (may differ slightly from v1.0.0)
- [ ] No errors

### Document Retraining

```
## Retraining - Feb 3, 2026

**Model:** v1.0.0 → v1.0.1 (notation optional)
**Data Added:** Jan 11 - Feb 3 (23 games)
**New Accuracy:** 69.2% (up from 68.98%)
**TIER 1 Accuracy:** 72% (up from 71%)

**Action:** Deploy v1.0.1
```
- [ ] Retraining results documented

---

## SUCCESS CRITERIA (30-Day POC)

### By End of Jan

- [ ] Daily predictions generated: 100% success rate (30/30 days)
- [ ] Game outcomes logged: ≥90% complete (27+/30 days)
- [ ] TIER 1 accuracy: ≥70% (cumulative)
- [ ] False positives: <5% of high-confidence predictions
- [ ] Weekly reports: All 4 weeks complete

### By End of Feb

- [ ] Continued daily predictions: 100%
- [ ] TIER 1 accuracy maintained: ≥70%
- [ ] Monthly retraining: Completed 1x
- [ ] New model deployed: ✓
- [ ] Team confidence: High
- [ ] Ready to scale to production

---

## 🚨 EMERGENCY PROCEDURES

### If Model Fails to Load

```bash
# Check file
ls -la .linelogic/nba_model_v1.0.0.pkl

# Try cache-only mode
python scripts/train_offline.py --cache-only --stratified

# This will retrain quickly and generate new model
```
- [ ] Fallback model created

### If API Fails

```bash
# Predictions will use cache instead
# Continue normally
python scripts/infer_daily.py --verbose
```
- [ ] Predictions still generated

### If No Games for Date

- This is normal (off-season or unusual schedule)
- Log: `date,no_games` to tracking
- Resume next day
- [ ] Documented in log

### If Accuracy Drops >2%

1. [ ] Check data quality (run `analyze_segmentation.py`)
2. [ ] Retrain immediately
3. [ ] Compare results
4. [ ] If still low, escalate to model team

---

## TEAM COMMUNICATION

### Day 1 Message

```
✅ LineLogic POC Launched - Jan 11, 2026

✓ Daily predictions now running
✓ 4-8 games scored daily
✓ Confidence tiers assigned

See QUICK_REFERENCE.md for decision guidance.
Validation report Monday.

Status: 🟢 Operating normally
```

### Weekly Message

```
📊 Weekly Validation - Week of Jan 11-17

✓ Accuracy: 68% (7 games)
✓ TIER 1: 71% (5 games)
✓ Status: On track

Next validation: Jan 20
```

### Monthly Message

```
🔄 Monthly Retraining - Feb 3

✓ Model retrained with Jan 11 - Feb 3 data
✓ New accuracy: 69.2% (up from 68.98%)
✓ TIER 1 accuracy: 72%

New model deployed. Operations continue.
Next retraining: Mar 3
```

- [ ] Day 1 sent
- [ ] Weekly sent (Mondays)
- [ ] Monthly sent (1st of month)

---

## DOCUMENTATION CHECKLIST

- [ ] `OPERATIONS_RUNBOOK.md` - Day-to-day procedures ✓
- [ ] `VALIDATION_FRAMEWORK.md` - A/B testing guide ✓
- [ ] `QUICK_REFERENCE.md` - Quick lookup ✓
- [ ] `DEPLOYMENT_READY.md` - Deployment overview ✓
- [ ] `POC_DEPLOYMENT_PACKAGE.md` - Package summary ✓
- [ ] `docs/status/predictions_log.csv` - Tracking log ✓
- [ ] `scripts/validate_predictions.py` - Validation script ✓
- [ ] `scripts/infer_daily.py` - Inference script ✓

---

## SIGN-OFF

**Deployment Lead:** ___________________________  
**Date:** ___________________________  
**Status:** ✅ Ready for Launch  

---

**POC Launch Date:** Jan 11, 2026  
**Expected Duration:** 30 days (Jan 11 - Feb 10)  
**Success Metric:** TIER 1 accuracy ≥70% maintained
