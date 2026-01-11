# LineLogic Email Notifications - Setup Complete ✅

## What Was Added

Your LineLogic POC now has a complete email notification system for daily operations. Here's what's ready to go:

### 📧 Email Infrastructure

- **SummaryGenerator** (`src/linelogic/eval/summary.py`): Generates beautiful HTML emails with:
  - Current bankroll tracking (starting $1,000 + cumulative P&L)
  - Daily picks with model probability, market odds, edge %, and stakes
  - Settlement reports with outcomes, P&L, and ROI
  - Color-coded HTML tables styled for readability

- **EmailSender** (`src/linelogic/email_sender.py`): Integrates with SendGrid API
  - Free tier: 100 emails/day (sufficient for daily reports)
  - Graceful error handling when API key not configured
  - Professional HTML email formatting

### 🔌 CLI Integration

Both daily commands now support email:

```bash
# Recommend with email (default: your.email@example.com)
linelogic recommend-daily --date 2026-01-15

# Or skip email
linelogic recommend-daily --date 2026-01-15 --no-email

# Or use different email
linelogic recommend-daily --date 2026-01-15 --email your.email@example.com

# Settlement emails work the same way
linelogic settle-daily --date 2026-01-14 --email your.email@example.com
```

### ⚙️ Scheduler Integration

**Local (LaunchAgent)** - sends emails at 9 AM daily if SENDGRID_API_KEY in `.env`
**Cloud (GitHub Actions)** - sends emails at 9 AM UTC daily if SENDGRID_API_KEY in GitHub Secrets

### 📋 Configuration

Three files were added/updated:

1. **`src/linelogic/config/settings.py`**: Added `sendgrid_api_key` field
2. **`.github/workflows/daily-job.yml`**: Updated to pass SENDGRID_API_KEY and --email flags
3. **`scripts/daily_linelogic.sh`**: Updated to include an email recipient
4. **`docs/specs/setup/12_email_setup.md`**: Complete SendGrid setup guide

## Next Steps

### 1. Create SendGrid Account (5 minutes)

1. Go to https://sendgrid.com/
2. Click "Sign Up" → create free account
3. Verify your email
4. Go to **Settings → API Keys**
5. Click **Create API Key** → name it "LineLogic"
6. Select **Full Access** → **Create & Copy**
7. Copy the key (starts with `SG.`)

### 2. Configure Local Environment

Add to `.env`:
```bash
SENDGRID_API_KEY=SG.your_actual_key_here
```

Test it locally:
```bash
linelogic recommend-daily --date 2026-01-15
# Should show: "📧 Summary emailed to your.email@example.com"
```

### 3. (Optional) Configure GitHub Actions

For 24/7 daily runs without your laptop being on:

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Name: `SENDGRID_API_KEY`
4. Value: Paste your SendGrid API key
5. Click **Add secret**

The workflow will automatically send emails on daily runs.

## What Each Email Shows

### Recommendation Email (9 AM)

```
Subject: LineLogic Daily Picks - 2026-01-15

┌─ Current Bankroll ─────────────────┐
│ $1,030.50                          │
│ Starting: $1,000 | P&L: +$30.50   │
└────────────────────────────────────┘

Today's Picks (6 recommendations):
┌─────────────────┬──────┬────┬─────┬──────────┐
│ Team            │ Prob │ Od │ Edge│  Stake   │
├─────────────────┼──────┼────┼─────┼──────────┤
│ Cavaliers (H)   │ 52%  │-110│ 2%  │  $5.00   │
│ Pacers (H)      │ 52%  │-110│ 2%  │  $5.00   │
│ ... 4 more                                    │
└─────────────────┴──────┴────┴─────┴──────────┘
```

### Settlement Email (After 9 AM + games complete)

```
Subject: LineLogic Settlement Report - 2026-01-14

Yesterday's Results (4 settled picks):
┌─────────────┬───────┬─────────┬────────┐
│ Team        │Stake  │ Result  │  P&L   │
├─────────────┼───────┼─────────┼────────┤
│ Cavaliers   │ $5.00 │ ✅ WIN  │ +$4.55 │
│ Pacers      │ $5.00 │ ❌ LOSS │ -$5.50 │
│ ... 2 more                             │
└─────────────┴───────┴─────────┴────────┘

P&L: -$1.00
ROI: -5.0%
Current Bankroll: $1,029.50
```

## Architecture Overview

```
Daily Operations Flow:
┌─────────────────────────────────────────────┐
│  LaunchAgent (9 AM) or GitHub Actions       │
├─────────────────────────────────────────────┤
│                                             │
│  1. recommend-daily                         │
│     └─ Fetch games → Run model → Save      │
│        ├─ SummaryGenerator generates HTML  │
│        └─ EmailSender sends via SendGrid   │
│                                             │
│  2. settle-daily                            │
│     └─ Mark yesterday as complete          │
│        ├─ SummaryGenerator generates HTML  │
│        └─ EmailSender sends via SendGrid   │
│                                             │
│  3. Commit database (GitHub Actions only)  │
│                                             │
└─────────────────────────────────────────────┘
```

## Testing

```bash
# Test local run without email (if no API key)
linelogic recommend-daily --date 2026-01-15 --no-email

# Test with email (requires SENDGRID_API_KEY in .env)
linelogic recommend-daily --date 2026-01-15
# Check inbox for: "LineLogic Daily Picks - 2026-01-15"

# Check logs
tail -50 .linelogic/daily_job.log

# Debug with verbose logging
LOG_LEVEL=DEBUG linelogic recommend-daily --date 2026-01-15
```

## Status

✅ **Email infrastructure ready**
- SummaryGenerator: Generates HTML tables with bankroll tracking
- EmailSender: SendGrid API integration with error handling
- CLI integration: --email and --no-email flags on both commands
- Schedulers updated: LaunchAgent and GitHub Actions ready

⏳ **Waiting for your setup**
- Create SendGrid account and get API key
- Add SENDGRID_API_KEY to .env (local testing)
- Add SENDGRID_API_KEY to GitHub Secrets (GitHub Actions)

## All 74 Tests Still Passing ✅

```
============================= 74 passed in 6.30s =============================
```

## Documentation

- **Email Setup**: [../specs/setup/12_email_setup.md](../specs/setup/12_email_setup.md)
- **Local Scheduler**: [../specs/setup/10_daily_scheduler.md](../specs/setup/10_daily_scheduler.md)
- **GitHub Actions**: [../specs/setup/11_github_actions_scheduler.md](../specs/setup/11_github_actions_scheduler.md)
- **Updated README**: New daily operations section with examples

## Files Changed

- ✅ `src/linelogic/config/settings.py` - Added sendgrid_api_key field
- ✅ `src/linelogic/app/cli.py` - Added --email and --no-email flags
- ✅ `src/linelogic/eval/summary.py` - Fixed f-string formatting
- ✅ `src/linelogic/email_sender.py` - (Already existed, no changes)
- ✅ `.github/workflows/daily-job.yml` - Updated with email flags and secrets
- ✅ `scripts/daily_linelogic.sh` - Updated with email addresses
- ✅ `docs/specs/setup/12_email_setup.md` - New comprehensive setup guide
- ✅ `README.md` - Added daily operations section and updated roadmap

## Next Phase: Model Training

Once you have 30-60 days of labeled picks, you can train v2 models:

```
30-60 days of daily runs
    ↓
~150-300 labeled recommendations
    ↓
Feature engineering (spreads, totals, team strength, etc.)
    ↓
GLM/XGBoost model training
    ↓
v2 production model with real predictive power
```

Current stub model (52% vs 50%) will be replaced with data-driven probabilities.

---

**Ready to receive daily emails? Create your SendGrid account and add the API key!**
