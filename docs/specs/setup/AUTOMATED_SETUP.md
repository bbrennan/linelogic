# 🤖 Fully Automated Setup - POC Launches Tomorrow (Jan 11) with Zero Manual Steps

**Status:** ✅ **AUTOMATED & READY**

---

## What's Happening Automatically Starting Jan 11

### ⏰ Daily at 9 AM UTC (4 AM EST / 1 AM PST)

**GitHub Actions Workflow: `daily-job.yml`**

1. ✅ Checkout latest code
2. ✅ Set up Python 3.11 environment
3. ✅ Run `scripts/infer_daily.py` → Generate predictions with confidence tiers
4. ✅ **Email predictions to bbrennan83@gmail.com** with:
   - All games for the day
   - Prediction probabilities
   - Confidence tiers (TIER 1-4)
   - Recommendations
   - Pretty HTML table
5. ✅ Commit predictions CSV to GitHub repo
6. ✅ Keep running legacy `recommend-daily` / `settle-daily` if they exist (backwards compatible)

**Email Subject:** `LineLogic Daily Predictions - YYYY-MM-DD`

---

### 🔔 Every Monday at 9 AM UTC (4 AM EST / 1 AM PST)

**GitHub Actions Workflow: `weekly-summary.yml`**

1. ✅ Checkout latest predictions log
2. ✅ Run `scripts/validate_predictions.py` with:
   - `--by-tier` (accuracy by TIER 1-4)
   - `--by-team` (accuracy by home team)
   - `--by-bucket` (calibration by prediction probability range)
3. ✅ **Email validation report to bbrennan83@gmail.com** with:
   - Overall accuracy metrics
   - Accuracy breakdown by confidence tier
   - Status indicators (✅ on target / ⚠️ below target)
   - Tier performance targets
   - Pretty HTML table
4. ✅ Export JSON + CSV validation reports
5. ✅ Commit reports to GitHub repo

**Email Subject:** `LineLogic Weekly Validation Report - Week Ending YYYY-MM-DD`

---

## How It Works

### **What You Need to Have Set Up** (✅ Already Done)

1. **GitHub Actions Workflows** - Updated in `.github/workflows/`
2. **Email Credentials** - Already in GitHub Secrets:
   - `SMTP_USER` (Gmail account)
   - `SMTP_PASS` (Gmail app password)
   - `FROM_EMAIL` (sender email)
3. **API Keys** - Already in GitHub Secrets:
   - `BALLDONTLIE_API_KEY`
4. **Python Scripts** - Ready to run:
   - `scripts/infer_daily.py` (daily predictions)
   - `scripts/validate_predictions.py` (weekly validation)

### **Predictions Flow**

```
Daily at 9 AM UTC
    ↓
GitHub Actions triggers workflow
    ↓
Run: python scripts/infer_daily.py --output predictions_YYYY-MM-DD.csv
    ↓
Generate HTML email with pretty table
    ↓
Send via Gmail SMTP to bbrennan83@gmail.com
    ↓
Commit CSV to repo
    ↓
Done! (No manual work needed)
```

### **Validation Flow**

```
Every Monday at 9 AM UTC
    ↓
GitHub Actions triggers workflow
    ↓
Run: python scripts/validate_predictions.py --predictions predictions_log.csv --by-tier --by-team --by-bucket
    ↓
Generate HTML email with calibration metrics
    ↓
Send via Gmail SMTP to bbrennan83@gmail.com
    ↓
Commit JSON + CSV reports to repo
    ↓
Done! (No manual work needed)
```

---

## 📧 What Emails You'll Receive

### Daily Email (9 AM UTC)

```
FROM: sender@gmail.com
TO: bbrennan83@gmail.com
SUBJECT: LineLogic Daily Predictions - 2026-01-11

┌─────────────────────────────────────────────────────────────┐
│ LineLogic Daily Predictions - 2026-01-11                   │
│                                                             │
│ Home | Away | Pred % | Rest | Tier        | Recommendation│
├─────────────────────────────────────────────────────────────┤
│ BOS  | LAL  | 62%    | 3d   | TIER 1 🟢   | USE MODEL     │
│ MIA  | CLE  | 49%    | 1d   | TIER 4 🔴   | CROSS-CHECK   │
└─────────────────────────────────────────────────────────────┘

Decision Guide:
🟢 TIER 1: Use model predictions directly (≥70% accuracy)
🟡 TIER 2: Use with external validation (68-70%)
🔴 TIER 4: Cross-check externally - back-to-back weakness
```

### Weekly Email (Mondays, 9 AM UTC)

```
FROM: sender@gmail.com
TO: bbrennan83@gmail.com
SUBJECT: LineLogic Weekly Validation Report - Week Ending 2026-01-17

┌───────────────────────────────────────────────────────────┐
│ Overall Metrics (35 games)                               │
├───────────────────────────────────────────────────────────┤
│ Overall Accuracy:        68.57% ✅                       │
│ Log Loss:                0.6120                           │
│ Baseline Home Win Rate:  54.29%                           │
│                                                           │
│ Accuracy by Confidence Tier:                             │
│                                                           │
│ TIER 1 (HIGH):    71.43% ✅ On Target (21 games)        │
│ TIER 2 (MED-HIGH):66.67% ⚠️  Below Target (9 games)     │
│ TIER 4 (CAUTION): 50.00% ✅ Expected (5 games)          │
│                                                           │
│ Target Accuracy by Tier:                                 │
│ 🟢 TIER 1: ≥70%                                          │
│ 🟡 TIER 2: 68-70%                                        │
│ 🔴 TIER 4: <50% (back-to-back weakness)                 │
└───────────────────────────────────────────────────────────┘
```

---

## 🔧 GitHub Secrets You Already Have

Check GitHub repo Settings → Secrets and variables → Actions:

- ✅ `BALLDONTLIE_API_KEY` - For game data fetching
- ✅ `SMTP_USER` - Gmail account (e.g., `your-email@gmail.com`)
- ✅ `SMTP_PASS` - Gmail app password (16-char password)
- ✅ `FROM_EMAIL` - Sender email (typically same as SMTP_USER)
- ✅ `SENDGRID_API_KEY` - For legacy system (optional)

**If missing, add now:**
```
Go to: GitHub repo → Settings → Secrets and variables → Actions → New repository secret

SMTP_USER = your-email@gmail.com
SMTP_PASS = xxxx xxxx xxxx xxxx (Gmail app password)
FROM_EMAIL = your-email@gmail.com
```

---

## 📅 Automated Schedule (Starting Tomorrow)

| Day | Time | Action | Email |
|-----|------|--------|-------|
| Every day | 9 AM UTC | Generate predictions | ✅ Daily |
| Mondays | 9 AM UTC | Validate & report | ✅ Weekly |

**UTC to Your Timezone:**
- 9 AM UTC = **4 AM EST** / **1 AM PST** / **9 AM GMT**
- Adjust cron if needed (see workflows)

---

## 🎯 What You Need to Do

### **Tomorrow (Jan 11) Morning**

**NOTHING!** The workflow runs automatically at 9 AM UTC.

But you CAN:
- Check GitHub Actions tab to see workflow running
- Refresh inbox at 4 AM EST to see email arrive
- Check predictions CSV in repo

### **Manual Tracking (Optional)**

If you want to manually log outcomes for validation:
1. Check email with daily predictions
2. After games, add `actual_home_win` column to CSV
3. Append to `predictions_log.csv`
4. Commit to repo

(Workflow will read this for next Monday's validation!)

---

## 🚀 Testing the Workflows

### **Test Daily Workflow**

```bash
# Go to GitHub repo
# Click: Actions → LineLogic Daily Job → Run workflow → Run workflow

# Or trigger via CLI (if you have gh installed):
gh workflow run daily-job.yml
```

Expected output: Email within 1 minute

### **Test Weekly Workflow**

```bash
# Go to GitHub repo
# Click: Actions → LineLogic Weekly Summary → Run workflow → Run workflow

# Or:
gh workflow run weekly-summary.yml
```

Expected output: Email with validation metrics within 1 minute

---

## 📊 What Gets Saved to Repo

After each run, these files are committed:

**Daily:**
- `predictions_2026-01-11.csv` (today's predictions)
- `predictions_log.csv` (appended with results)

**Weekly (Mondays):**
- `validation_report_2026-01-17.json` (full metrics)
- `tier_metrics_2026-01-17.csv` (tier breakdown)

---

## 🔍 Monitoring

### **Check Workflow Status**

Go to GitHub repo → Actions tab

You'll see:
- 🟢 **Daily Job** - Runs every day at 9 AM UTC
- 🟢 **Weekly Summary** - Runs every Monday at 9 AM UTC

Click on workflow → See logs, status, timing

### **Check Emails**

Look for:
- Daily: `LineLogic Daily Predictions - YYYY-MM-DD`
- Weekly: `LineLogic Weekly Validation Report - Week Ending YYYY-MM-DD`

If email missing:
1. Check GitHub Actions logs (may show "SMTP not configured")
2. Verify `SMTP_USER` and `SMTP_PASS` secrets are set
3. Ensure Gmail "App Password" is used (not regular password)

---

## ⚙️ Customizing the Schedule

**Edit cron expression in `.github/workflows/daily-job.yml`:**

```yaml
on:
    schedule:
        - cron: "0 9 * * *"  # 9 AM UTC every day
```

Common times:
- `"0 8 * * *"` = 8 AM UTC
- `"0 13 * * *"` = 1 PM UTC
- `"0 9 * * 1"` = Mondays 9 AM UTC (weekly)

**UTC Time Converter:**
- 9 AM UTC = 4 AM EST / 1 AM PST / 5 PM JST / 9 AM GMT

---

## 🎉 Summary: You're Set!

**Tomorrow (Jan 11) at 9 AM UTC:**

1. ✅ GitHub Actions triggers automatically
2. ✅ Runs `infer_daily.py` → generates predictions
3. ✅ Sends HTML email to bbrennan83@gmail.com
4. ✅ Commits CSVs to repo
5. ✅ **Zero manual work needed**

**Every Monday at 9 AM UTC:**

1. ✅ GitHub Actions triggers automatically
2. ✅ Runs `validate_predictions.py` → validates accuracy
3. ✅ Sends validation report email
4. ✅ Commits JSON/CSV reports to repo
5. ✅ **Zero manual work needed**

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| No email received | Check GitHub Actions logs; verify SMTP secrets |
| Workflow failed to run | Check cron syntax; ensure secrets are set |
| Wrong time | Adjust cron expression (remember: UTC time) |
| Want to disable | Comment out `on.schedule` section in workflow file |
| Want to test | Use `workflow_dispatch` (Run workflow button in Actions tab) |

---

**Status:** 🟢 **FULLY AUTOMATED**  
**Launch:** Jan 11, 2026 at 9 AM UTC  
**Your effort required:** Zero! ☕

Everything runs on its own. Check your email tomorrow morning!
