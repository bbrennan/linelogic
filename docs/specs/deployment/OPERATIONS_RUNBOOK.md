# LineLogic POC Operations Runbook

**Effective:** Jan 11, 2026  
**Model Version:** v1.0.0  
**Deployment Environment:** Daily POC predictions on 2024-2025 NBA regular season games

---

## Quick Start

### Before You Begin
- [ ] Ensure `.venv` is activated: `source .venv/bin/activate`
- [ ] Verify BALLDONTLIE_API_KEY is set: `echo $BALLDONTLIE_API_KEY`
- [ ] Verify ODDS_API_KEY is set (if ingesting odds): `echo $ODDS_API_KEY`
- [ ] Check model file exists: `ls -la .linelogic/nba_model_v1.0.0.pkl`

### Daily Prediction Run (5 minutes)

```bash
# Day-of prediction (automatic date detection)
python scripts/infer_daily.py --verbose --output predictions_$(date +%Y-%m-%d).csv

# Or specify a specific date
python scripts/infer_daily.py --date 2026-01-11 --output predictions_2026-01-11.csv
```

**Output:** CSV with columns:
- `date`, `home_team`, `away_team`
- `pred_home_win_prob`, `pred_away_win_prob` (model output)
- `home_team_rest_days`, `away_team_rest_days` (estimated)
- `confidence_tier` (TIER 1/2/3/4)
- `recommendation` (USE MODEL / USE WITH VALIDATION / CROSS-CHECK)

### Expected Output Example
```
date,home_team,away_team,pred_home_win_prob,pred_away_win_prob,home_team_rest_days,away_team_rest_days,confidence_tier,recommendation
2026-01-11,BOS,LAL,0.6234,0.3766,2,3,TIER 1 (HIGH CONFIDENCE),USE MODEL
2026-01-11,MIA,CLE,0.4891,0.5109,1,2,TIER 4 (CAUTION),CROSS-CHECK EXTERNALLY
```

---

## Understanding Predictions

### Confidence Tiers

| Tier | Scenario | Action | Expected Accuracy |
|------|----------|--------|-------------------|
| **TIER 1** | 2024-2025 regular season, 2-3+ days rest | Use predictions directly | 70%+ |
| **TIER 2** | 2025 regular season, 2-3 days rest | Use with external validation | 68-70% |
| **TIER 3** | Other regular season scenarios | Use as tiebreaker | 65-68% |
| **TIER 4** | 1-day rest (back-to-back) | Cross-check; don't rely solely | <50% |

### Decision Framework

**If TIER 1 (HIGH CONFIDENCE):**
- Prediction probability ≥ 0.55 → **USE MODEL** (high home-team edge)
- Prediction probability 0.45-0.55 → **SLIGHT AWAY EDGE** (close game; use model cautiously)
- Prediction probability < 0.45 → **AWAY TEAM FAVORED** (strong away signal)

**If TIER 2 (MEDIUM-HIGH):**
- Check external factors (injury reports, team news, trading deadline proximity)
- If no red flags → use model output as primary signal
- If uncertainty → default to baseline (54% home win rate)

**If TIER 3 (MEDIUM):**
- Use model as tiebreaker only
- Always cross-check with other signals

**If TIER 4 (CAUTION):**
- Model weakness in back-to-back games
- DO NOT bet solely on model prediction
- Cross-check with: team fatigue reports, injury status, road/home performance history

### Example Decision Trees

```
GAME: BOS (home, 3d rest) vs LAL (away, 2d rest)
↓
Tier: TIER 1 (HIGH CONFIDENCE)
↓
Model Output: 0.62 (BOS 62% to win)
↓
Decision: USE MODEL → BOS is favored
```

```
GAME: WSH (home, 1d rest) vs PHI (away, 2d rest)
↓
Tier: TIER 4 (CAUTION)
↓
Model Output: 0.48 (PHI slight edge)
↓
Decision: CROSS-CHECK EXTERNALLY
   → Check WSH/PHI recent form
   → Check injury reports
   → Use model as secondary signal only
```

---

## Operational Procedures

### Daily Workflow

**8:00 AM** – Check Upcoming Games
```bash
# Generate predictions for today
python scripts/infer_daily.py --verbose --output predictions_$(date +%Y-%m-%d).csv

# Review output
head -20 predictions_*.csv
```

**8:15 AM** – Validate Predictions
- [ ] Check TIER 1 predictions (should be ~4-6 games per day)
- [ ] Verify rest days match expected (e.g., no team has >4 consecutive days without game)
- [ ] Flag any TIER 4 games; cross-check with external sources

**8:30 AM** – Decision Log
- [ ] Document which TIER 1 predictions will be tracked
- [ ] Note any unusual matchups (injury issues, team changes)
- [ ] Flag games to skip (playoffs, special circumstances)

**After Games** – Log Outcomes
```bash
# Track predictions vs actual for validation
# Expected format: game_id, pred_prob, actual_home_win, tier, date
# See "Validation & Monitoring" section
```

### Weekly Review

**Every Monday:**

1. **Accuracy by Tier:**
   ```bash
   python scripts/analyze_tier_accuracy.py --week $(date +%Y-W%V)
   ```
   Expected output:
   - TIER 1: 70%+ accuracy
   - TIER 2: 68-70% accuracy
   - TIER 3: 65-68% accuracy
   - TIER 4: <50% (expected; flag if >50%)

2. **False Positive Rate:**
   - Track predictions with >0.65 prob that lost
   - Should be <5% of high-confidence predictions

3. **Team Performance Outliers:**
   - Track teams with actual win rate >20% away from model prediction
   - Investigate changes (trades, injuries, system changes)

### Monthly Retraining

**First Monday of Month:**

```bash
# Fetch latest data from BALLDONTLIE
export BALLDONTLIE_API_KEY=<key>
python scripts/train_offline.py --no-synthetic --stratified

# This will:
# 1. Fetch all 2024-2025 games since last run
# 2. Retrain model with new data
# 3. Generate new .pkl and metadata
# 4. Test on holdout set
# 5. Print accuracy metrics
```

If accuracy degrades >1%:
- [ ] Check data quality (zero-score games, corrupted rows)
- [ ] Verify rest day estimation logic
- [ ] Look for structural changes (playoff approach, system changes)
- [ ] Consider feature adjustments or hyperparameter tuning

---

## Troubleshooting

### "Model not found" Error

```
Error: Model not found: .linelogic/nba_model_v1.0.0.pkl
```

**Solution:**
1. Verify model file: `ls -la .linelogic/nba_model_*.pkl`
2. If missing, retrain: `python scripts/train_offline.py --cache-only`
3. If still missing, full retrain: `python scripts/train_offline.py --no-synthetic --stratified`

### "No games found for [date]"

**Possible causes:**
1. BALLDONTLIE API rate limit hit
   - Wait 1 minute, retry
   - Check: `echo $BALLDONTLIE_API_KEY` (verify key is set)

2. Date is in off-season (June 23 - Oct 24)
   - This is expected; no games scheduled

3. API connection issue
   - Check internet: `ping api.balldontlie.io`
   - Verify VPN if needed

**Solution:**
```bash
# Retry with cache-only mode (uses historical data)
python scripts/infer_daily.py --date 2026-01-11 --verbose
# If API fails, will fall back to cache
```

### Accuracy Suddenly Drops

**If test accuracy < 65%:**

1. Check for data quality issues:
   ```bash
   python scripts/analyze_segmentation.py | head -50
   # Look for: baseline home_win rate, test set size
   ```

2. Verify no major structural changes:
   - Look at recent trades/injuries (external research)
   - Check if date is near season milestone (all-star break, trade deadline)

3. Retrain with fresh data:
   ```bash
   python scripts/train_offline.py --no-synthetic --stratified
   ```

4. If still low, investigate:
   - Email model maintainer
   - Consider feature engineering changes
   - Evaluate switching to ensemble or different model

### Confidence Tier Assignment Seems Wrong

**Example:** Game marked TIER 4 but looks like TIER 1

1. Check the assignment logic in `scripts/infer_daily.py`:
   - Line ~100: `assign_confidence_tier()` method
   - Verify season and rest days are estimated correctly

2. Manual override:
   - Confidence tiers are guidelines, not laws
   - For TIER 3-4 games, use your judgment
   - Log any manual overrides in decision log

3. Report anomalies:
   - If consistently wrong, flag for model retraining
   - Provide example: date, teams, tier, reason why wrong

---

## Validation & Monitoring

### Prediction Tracking Template

Create file: `docs/status/predictions_log.csv`

```csv
date,home_team,away_team,pred_prob,confidence_tier,actual_home_win,tracked_yn,notes
2026-01-11,BOS,LAL,0.62,TIER 1,TRUE,Y,As expected
2026-01-11,MIA,CLE,0.49,TIER 4,FALSE,N,Skipped (back-to-back)
```

**Fields:**
- `date`: Game date (YYYY-MM-DD)
- `home_team`: Home team code (3-letter)
- `away_team`: Away team code (3-letter)
- `pred_prob`: Model's predicted home win probability (0.0-1.0)
- `confidence_tier`: TIER 1/2/3/4
- `actual_home_win`: TRUE if home team won, FALSE if away team won
- `tracked_yn`: Y/N (did you track this prediction?)
- `notes`: Any special observations

### Weekly Accuracy Report

```bash
# Generate accuracy by tier
python -c "
import pandas as pd
df = pd.read_csv('docs/status/predictions_log.csv')
df['pred_correct'] = ((df['pred_prob'] >= 0.5) & (df['actual_home_win'])) | ((df['pred_prob'] < 0.5) & (~df['actual_home_win']))
print('\n=== ACCURACY BY TIER ===')
for tier in ['TIER 1', 'TIER 2', 'TIER 3', 'TIER 4']:
    tier_df = df[df['confidence_tier'] == tier]
    if len(tier_df) > 0:
        acc = tier_df['pred_correct'].mean()
        print(f'{tier}: {acc:.1%} ({len(tier_df)} games)')
"
```

### Success Metrics (30-Day POC)

Track and report these metrics:

| Metric | Target | Action if Missed |
|--------|--------|------------------|
| TIER 1 accuracy | ≥70% | Review feature engineering |
| Overall accuracy | ≥68% | Retrain with new data |
| False positive rate (TIER 1) | <5% | Lower confidence threshold |
| Predictions generated | ≥90% success rate | Debug API/feature issues |
| Monthly retraining | 1x per month | Update model monthly |

---

## Escalation & Support

### When to Escalate

1. **Accuracy drops >2%** → Retrain or investigate features
2. **API consistently fails** → Check BALLDONTLIE status page; verify key
3. **Unusual tier assignments** → Review confidence tier logic
4. **Feature data missing** → Verify cache files (.linelogic/ directory)

### Contacts

**Model Development:**
- See [TRAIN_QUICK_START.md](../training/TRAIN_QUICK_START.md) for retraining guide
- See [src/linelogic/](src/linelogic/) for feature engineering code

**Data Issues:**
- BALLDONTLIE API docs: https://balldontlie.io/api/v1/docs.html
- Cache location: `.linelogic/games_cache.csv`
- Team stats: `.linelogic/team_season_avgs.csv`

**Deployment Questions:**
- See [DEPLOYMENT_READY.md](DEPLOYMENT_READY.md) for overview
- See [ENHANCED_MODEL_SUMMARY.md](../model/ENHANCED_MODEL_SUMMARY.md) for technical details

---

## Appendix: Command Reference

```bash
# Daily predictions
python scripts/infer_daily.py --verbose --output predictions_$(date +%Y-%m-%d).csv

# Retrain model (monthly)
python scripts/train_offline.py --no-synthetic --stratified

# Segmentation analysis (validate trustworthiness)
python scripts/analyze_segmentation.py | head -100

# Cache-only prediction (no API fetch)
python scripts/train_offline.py --cache-only --stratified

# Check Python version
python --version

# Verify environment
pip list | grep -E "scikit-learn|pandas|numpy"
```

---

**Last Updated:** Jan 10, 2026  
**Model Version:** v1.0.0  
**Deployment Status:** 🟢 Ready for POC
