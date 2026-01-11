# ✅ Final Launch Checklist - Jan 11 Fully Automated

**Date:** Jan 10, 2026 (Tonight - Last checks before launch)  
**Status:** 🟢 READY

---

## 🔐 GitHub Secrets Verification

Run this to verify your secrets are set:

```bash
# List all secrets (you need GitHub CLI installed)
gh secret list --repo YOUR_OWNER/YOUR_REPO
```

**Required Secrets (should all show as set):**

- [ ] ✅ `BALLDONTLIE_API_KEY` - Set
- [ ] ✅ `SMTP_USER` - Set (Gmail: your-email@gmail.com)
- [ ] ✅ `SMTP_PASS` - Set (Gmail app password, 16 chars)
- [ ] ✅ `FROM_EMAIL` - Set (typically same as SMTP_USER)

**If any are missing, add them now:**
```
GitHub repo → Settings → Secrets and variables → Actions → New repository secret
```

---

## 🤖 GitHub Actions Workflows

**Check both workflows exist and are enabled:**

```bash
# List workflows
gh workflow list --repo YOUR_OWNER/YOUR_REPO
```

**Should show:**
- ✅ `daily-job.yml` - Status: Active
- ✅ `weekly-summary.yml` - Status: Active

**If not active, enable them:**
```
GitHub repo → Actions → Select workflow → Enable workflow
```

---

## 📄 Updated Workflows

**Verify the workflows have been updated with new scripts:**

```bash
# Check daily-job.yml contains infer_daily.py
grep "infer_daily.py" .github/workflows/daily-job.yml

# Check weekly-summary.yml contains validate_predictions.py
grep "validate_predictions.py" .github/workflows/weekly-summary.yml
```

**Expected output:**
- ✅ Both commands return the script names (no "not found")

---

## 🐍 Scripts Are Ready

**Verify both scripts exist and are executable:**

```bash
ls -la scripts/infer_daily.py scripts/validate_predictions.py
```

**Expected:**
- ✅ Both files exist (size > 0 bytes)
- ✅ Both are readable

---

## 📝 Data Files Ready

**Verify all required data files exist:**

```bash
ls -la .linelogic/nba_model_v1.0.0.pkl
ls -la .linelogic/nba_model_v1.0.0_metadata.json
ls -la .linelogic/games_cache.csv
ls -la predictions_log.csv
```

**Expected:**
- ✅ Model file exists (size > 5 MB)
- ✅ Metadata file exists (size > 1 KB)
- ✅ Games cache exists (size > 1 MB)
- ✅ Predictions log template exists

---

## 🧪 Test Run (Optional but Recommended)

**Test the daily workflow locally first:**

```bash
# Activate venv
source .venv/bin/activate

# Set API key
export BALLDONTLIE_API_KEY=your_key_here

# Run inference script
python scripts/infer_daily.py --verbose --output test_predictions_$(date +%Y-%m-%d).csv

# Should complete without errors and generate CSV
```

**Expected:**
- ✅ Script runs successfully
- ✅ CSV file created with predictions
- ✅ CSV has columns: date, home_team, away_team, pred_*, confidence_tier, recommendation

---

## 🚀 Workflow Manual Test

**Optionally, trigger workflows manually to test:**

```bash
# Test daily job
gh workflow run daily-job.yml --repo YOUR_OWNER/YOUR_REPO

# Test weekly job
gh workflow run weekly-summary.yml --repo YOUR_OWNER/YOUR_REPO
```

**Expected within 1-2 minutes:**
- ✅ Email arrives at bbrennan83@gmail.com
- ✅ Email has HTML table with predictions/validation
- ✅ GitHub Actions shows "Success" status

---

## 📧 Email Test Checklist

**Once you trigger a test workflow, check email:**

- [ ] ✅ Email received from GitHub Actions
- [ ] ✅ Subject line correct: `LineLogic Daily Predictions - YYYY-MM-DD`
- [ ] ✅ HTML table is pretty and readable
- [ ] ✅ Predictions show correct data (if games exist)
- [ ] ✅ Confidence tiers assigned correctly
- [ ] ✅ No error messages in email body

---

## 🕐 Schedule Verification

**Verify cron schedules are correct for your timezone:**

**Daily Job:**
```yaml
cron: "0 9 * * *"  # 9 AM UTC = 4 AM EST / 1 AM PST
```

**Weekly Job:**
```yaml
cron: "0 9 * * 1"  # Mondays 9 AM UTC
```

**Change if needed:**
- Edit `.github/workflows/daily-job.yml` or `.github/workflows/weekly-summary.yml`
- Change cron expression
- Commit and push to GitHub
- Workflows auto-update

---

## 📱 Notification Preferences

**Want to change recipient email?**

Edit `.github/workflows/daily-job.yml` and `.github/workflows/weekly-summary.yml`:

```yaml
# Change this line in both workflows:
msg['To'] = 'bbrennan83@gmail.com'
# To:
msg['To'] = 'your-email@example.com'
```

Then commit and push.

---

## 🛑 Known Issues & Solutions

### Issue: "SMTP credentials not set"
**Solution:** Add `SMTP_USER` and `SMTP_PASS` to GitHub Secrets

### Issue: "Email failed: authentication failed"
**Solution:** Verify Gmail app password (not regular password). Set up here: https://myaccount.google.com/apppasswords

### Issue: Workflow didn't run at scheduled time
**Solution:** 
- GitHub Actions may have delays (up to 15 min)
- Manual test: Use `workflow_dispatch` to run manually
- Check Actions tab to see if it's scheduled

### Issue: "FileNotFoundError: predictions_log.csv"
**Solution:** File was created; may not be committed yet. First run will create it automatically.

---

## ✅ Pre-Launch Checklist (Complete All)

**Do this tonight (Jan 10):**

- [ ] GitHub Secrets verified (all 4 set)
- [ ] Workflows exist and are active
- [ ] Scripts exist and are readable
- [ ] Data files exist (.pkl, .json, .csv)
- [ ] Local test run successful (optional)
- [ ] Manual workflow test successful (optional)
- [ ] Email received from test (optional)

**If all checked, you're 100% ready for tomorrow!**

---

## 🚀 Tomorrow Morning (Jan 11)

**Nothing to do!** The automation takes care of everything.

**But you can:**
1. Check GitHub Actions tab to see workflow running (9 AM UTC = 4 AM EST)
2. Refresh email inbox around 4:30 AM EST
3. See predictions arrive automatically ✉️

---

## 📊 What Happens Automatically

### **Daily at 9 AM UTC (Starting Jan 11)**
```
Generate predictions with confidence tiers
    ↓
Send HTML email to bbrennan83@gmail.com
    ↓
Commit CSV to GitHub repo
    ↓
Done! (Zero work needed)
```

### **Every Monday at 9 AM UTC**
```
Validate all predictions from the week
    ↓
Calculate accuracy by TIER 1-4
    ↓
Send HTML email with calibration metrics
    ↓
Commit JSON + CSV reports to repo
    ↓
Done! (Zero work needed)
```

---

## 🎯 Success Indicators

**Everything is working if:**

✅ You get daily emails with predictions (morning of Jan 11+)  
✅ Email shows predictions in pretty HTML table  
✅ Email shows confidence tiers (TIER 1-4)  
✅ Every Monday, you get validation email  
✅ Validation email shows accuracy metrics  
✅ GitHub repo has prediction CSVs committed daily  
✅ GitHub repo has validation reports committed weekly

---

## 📞 Support

**If something doesn't work:**

1. Check GitHub Actions logs: `Actions tab → workflow → latest run → Logs`
2. Look for error messages (SMTP, FileNotFoundError, etc.)
3. Verify secrets and workflows are set correctly
4. Manual test: Use `workflow_dispatch` to run now
5. Check email spam folder (may be filtered)

---

**Status:** 🟢 **READY FOR FULLY AUTOMATED LAUNCH**

**Launch Time:** Jan 11, 2026 at 9 AM UTC (4 AM EST / 1 AM PST)  
**Your effort tomorrow:** ZERO ☕  
**Expected outcome:** Automated daily/weekly emails with zero manual work

---

**Final Note:** Everything is set up. The workflows will run automatically. You can go to sleep tonight—the system takes over in the morning! 🚀
