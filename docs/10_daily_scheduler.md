# LineLogic Daily Job Scheduler

Automatically runs `recommend-daily` and `settle-daily` every day at 9:00 AM without manual intervention.

## Setup Status

✅ **Installed and running**

The LaunchAgent has been configured to run daily:
- **Time**: 9:00 AM daily
- **What runs**: 
  - `recommend-daily` for today (generates picks for today's games)
  - `settle-daily` for yesterday (settles picks from yesterday's games)
- **Logs**: `.linelogic/daily_job.log` + LaunchAgent logs

## Management Commands

```bash
# Check if job is running
./scripts/linelogic-job.sh status

# View recent logs
./scripts/linelogic-job.sh logs

# Temporarily stop the job
./scripts/linelogic-job.sh stop

# Resume the job
./scripts/linelogic-job.sh start

# Restart immediately
./scripts/linelogic-job.sh restart

# Permanently remove the job
./scripts/linelogic-job.sh unload
```

## How It Works

1. **LaunchAgent Configuration**: `~/Library/LaunchAgents/com.linelogic.daily-job.plist`
   - Runs at 9:00 AM every day
   - Auto-loads on login

2. **Shell Script**: `scripts/daily_linelogic.sh`
   - Gets today's date
   - Gets yesterday's date
   - Runs `recommend-daily --date TODAY`
   - Waits 2 seconds
   - Runs `settle-daily --date YESTERDAY`
   - Logs all output to `.linelogic/daily_job.log`

## Logs

Check what happened:
```bash
# See job logs
tail -50 .linelogic/daily_job.log

# See LaunchAgent logs
tail -20 .linelogic/launchd.out.log
tail -20 .linelogic/launchd.err.log
```

## Customizing Schedule

To change the time (currently 9:00 AM):

```bash
# Edit the plist
vim ~/Library/LaunchAgents/com.linelogic.daily-job.plist

# Change these values:
# <key>Hour</key>
# <integer>9</integer>         <- Change this (0-23, 24-hr format)
# <key>Minute</key>
# <integer>0</integer>         <- Change this (0-59)

# Reload
./scripts/linelogic-job.sh restart
```

## Troubleshooting

**Job not running?**
```bash
# Check if it's loaded
launchctl list | grep com.linelogic

# Check logs
./scripts/linelogic-job.sh logs

# Try manually running the script
./scripts/daily_linelogic.sh
```

**Want to check what time it will run?**
```bash
# Show LaunchAgent info
launchctl list com.linelogic.daily-job

# Look for "StartCalendarInterval"
```

## Data Accumulation

Each day:
- New recommendations added to SQLite
- Previous day's picks settled
- Build up labeled dataset for v2 model training

After ~30-60 days: Ready to train real GLM/XGBoost model.
