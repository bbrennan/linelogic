# GitHub Actions: LineLogic Daily Job (Always-On)

Run LineLogic daily at 9 AM UTC **without your laptop being on**. GitHub Actions handles it 24/7.

## Setup Instructions

### 1. Push to GitHub

```bash
cd /Users/bbrennan/Desktop/LineLogic

# If not already a GitHub repo:
git remote add origin https://github.com/YOUR_USERNAME/linelogic.git
git branch -M main
git push -u origin main

# Alternatively, if you want to keep it private on GitHub:
# Create repo on github.com, then push
```

### 2. Add Secrets to GitHub

Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add two secrets:
- `BALLDONTLIE_API_KEY`: Your BALLDONTLIE API key
- `ODDS_API_KEY`: Your TheOddsAPI key

**Never commit these to git!**

#### Quick Verify (Recommended)

After rotating a key (especially `ODDS_API_KEY`), do a fast verification:

1. GitHub → **Repo → Settings → Secrets and variables → Actions**
2. Confirm these secret names exist (exact spelling):
  - `BALLDONTLIE_API_KEY`
  - `ODDS_API_KEY`
  - (If emailing is enabled) `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`, `TO_EMAIL`
3. Go to **Actions → LineLogic Daily Job → Run workflow** and run it once.

Notes:
- GitHub will not reveal secret values after you save them (by design).
- If a key is missing, the workflow should fail quickly or skip optional steps.

### 3. Enable Actions

Go to: **GitHub Repo → Actions → Enable workflows**

The workflow should appear as "LineLogic Daily Job"

### 4. Test Manually

Go to: **Actions → LineLogic Daily Job → Run workflow → Run workflow**

This tests the setup immediately without waiting for 9 AM.

---

## How It Works

**Every day at 9:00 AM UTC:**

1. GitHub spins up an Ubuntu container
2. Checks out your repo
3. Installs dependencies
4. Runs `recommend-daily` for today
5. Runs `settle-daily` for yesterday
6. Commits updated database back to GitHub
7. Stores logs as artifact (7 days retention)

**Result:**
- Database updated daily
- All picks + results in `.linelogic/linelogic.db`
- History visible in git commits
- Logs available in GitHub Actions UI

---

## Schedule Customization

The workflow runs at **9 AM UTC** by default. To change:

Edit `.github/workflows/daily-job.yml`:

```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # Change these numbers
```

**Cron format**: `minute hour day month weekday`

Examples:
- `0 9 * * *` = 9:00 AM UTC daily
- `0 13 * * *` = 1:00 PM UTC daily
- `0 14 * * MON-FRI` = 2 PM UTC Mon-Fri (weekdays only)
- `30 7 * * *` = 7:30 AM UTC daily

[Cron reference](https://crontab.guru/)

---

## Monitoring

### View Job Runs

**GitHub Repo → Actions → LineLogic Daily Job**

Shows:
- ✅ Successful runs
- ❌ Failed runs
- Execution time
- Logs

### View Logs

Click any run to see detailed logs:
- API request times
- Cache hits/misses
- Rate limit events
- Database commits

### Download Artifacts

Each run uploads `.linelogic/linelogic.log` (7-day retention)

Click run → Artifacts → Download

---

## Benefits vs. LaunchAgent

| Feature | LaunchAgent | GitHub Actions |
|---------|------------|----------------|
| Always runs on schedule | ❌ (needs laptop on) | ✅ (24/7) |
| No setup beyond code | ✅ | ❌ (needs GitHub secrets) |
| Free | ✅ | ✅ (2000 min/month free) |
| Visible history | ❌ | ✅ (all runs visible) |
| Alerts on failure | ❌ | ✅ (email notifications) |
| Multi-machine | ❌ | ✅ |

---

## Troubleshooting

**Workflow not appearing?**
- Push `.github/workflows/daily-job.yml` to repo
- Wait ~1 minute for GitHub to scan

**Jobs failing?**
- Go to Actions → Click failed job
- Check logs for error (API key issue, dependency missing, etc.)
- Fix and push new commit

**Database conflicts?**
- If you run local `recommend-daily` + GitHub Actions runs simultaneously
- Git will have merge conflicts
- Solution: Pull before running locally, or disable LaunchAgent

---

## Recommended Setup

**For production POC:**
1. Use GitHub Actions (9 AM UTC or your timezone)
2. Disable LaunchAgent on your laptop
3. Pull database daily to see results locally

```bash
git pull  # Latest database with all picks + results
sqlite3 .linelogic/linelogic.db "SELECT COUNT(*) FROM recommendations;"
```

**Database growth:**
- ~30 picks/day
- ~900 picks/month
- Ready for v2 model in 30-60 days
