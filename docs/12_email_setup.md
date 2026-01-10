# Email Notifications Setup

LineLogic can send daily email summaries with bankroll tracking, picks, and settlement reports using SendGrid's free tier.

## SendGrid Setup

### 1. Create Free SendGrid Account

1. Go to https://sendgrid.com/
2. Click "Sign Up" 
3. Create account (free tier: 100 emails/day)
4. Verify email address

### 2. Create API Key

1. Log into SendGrid dashboard
2. Navigate to **Settings → API Keys**
3. Click **Create API Key**
4. Name: `LineLogic` (or similar)
5. Select **Full Access**
6. Click **Create & Copy**
7. Copy the API key (starts with `SG.`)

### 3. Configure Local Environment

Add to `.env` file in LineLogic root:

```bash
SENDGRID_API_KEY=SG.your_actual_api_key_here
```

### 4. Configure GitHub Actions (for CI/CD)

1. Go to your GitHub repo
2. **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Name: `SENDGRID_API_KEY`
5. Value: Paste your SendGrid API key
6. Click **Add secret**

## Email Features

### Daily Recommendation Email

**Sent after** `recommend-daily` runs (9 AM daily):

- Current bankroll balance
- Today's picks (team, model probability, market odds, edge, stake)
- Styled HTML table with color coding

**Example:**
```
Subject: LineLogic Daily Picks - 2026-01-10

Current Bankroll: $1,050.25

Today's Picks (6 recommendations):
[Table with Cavaliers, Pacers, Pistons, Celtics, Bulls, Jazz]
```

### Daily Settlement Email

**Sent after** `settle-daily` runs (after `recommend-daily`):

- Yesterday's results (win/loss, profit/loss per pick)
- Total P&L for the day
- ROI percentage
- Updated bankroll

**Example:**
```
Subject: LineLogic Settlement Report - 2026-01-09

Yesterday's Results (4 settled picks):
[Table with outcomes and P&L]

P&L: +$50.00
ROI: +2.5%
Current Bankroll: $1,050.25
```

## Usage

### Local (LaunchAgent)

Email automatically sends if SENDGRID_API_KEY is set in `.env`:

```bash
# Will send email if API key configured
linelogic recommend-daily --date 2026-01-10

# Skip email with --no-email flag
linelogic recommend-daily --date 2026-01-10 --no-email

# Specify different email address
linelogic recommend-daily --date 2026-01-10 --email your.email@example.com
```

### GitHub Actions

Email automatically sends if `SENDGRID_API_KEY` secret is configured:

1. Ensure secret is added (see section 4 above)
2. Daily job runs automatically at 9 AM UTC
3. Emails sent to: `bbrennan83@gmail.com` (configurable in workflow YAML)

To change email recipient in GitHub Actions, edit `.github/workflows/daily-job.yml`:

```yaml
- name: Run recommend-daily
  run: |
    python -m linelogic.app.cli recommend-daily --date ${{ steps.dates.outputs.today }} --email your.email@example.com
```

## Troubleshooting

### Email not sent?

1. Check API key is valid in SendGrid dashboard
2. Verify `SENDGRID_API_KEY` env var is set:
   ```bash
   echo $SENDGRID_API_KEY
   ```
3. Check `.linelogic/linelogic.log` for errors
4. Try with `--no-email` flag to verify rest of command works
5. Run with verbose logging (set `LOG_LEVEL=DEBUG` in `.env`)

### Email is in spam?

1. Add linelogic@example.com to contacts
2. Mark as "Not Spam" in email client
3. Consider changing `from_email` in `EmailSender` class to your domain

### Too many emails?

1. Remove `SENDGRID_API_KEY` from `.env` to disable emails locally
2. Use `--no-email` flag to skip for single runs
3. Disable GitHub Actions workflow for testing

## Email Sender Settings

Default sender email: `linelogic@example.com`

To use a custom domain:

1. Verify domain in SendGrid (Settings → Sender Authentication)
2. Edit `src/linelogic/email_sender.py`:
   ```python
   from_email: str = "noreply@yourdomain.com",
   ```

## Free Tier Limits

- **100 emails/day** (sufficient for 1 email per day + margin)
- **No attachment support** (but includes styled HTML tables)
- **No link tracking** (fine for internal summaries)

For production upgrade to:
- SendGrid Pro: $9.95/month (10,000 emails/month)
- SendGrid Advanced: Custom pricing

## Security

**Important:** Never commit API keys to git!

- `.env` is in `.gitignore` (safe)
- GitHub Secrets are encrypted (safe)
- If key is leaked:
  1. Delete key in SendGrid dashboard (API Keys section)
  2. Create new key
  3. Update `.env` and GitHub Secrets

