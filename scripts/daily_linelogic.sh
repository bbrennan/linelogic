#!/bin/bash
# Daily LineLogic job: recommend and settle
# This script runs both recommend-daily and settle-daily

set -e

# Configuration
LINELOGIC_HOME="/Users/bbrennan/Desktop/LineLogic"
LOG_DIR="${LINELOGIC_HOME}/.linelogic"
SCRIPT_LOG="${LOG_DIR}/daily_job.log"

# Optional recipient; if unset, CLI will skip sending.
TO_EMAIL="${TO_EMAIL:-}"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Get today's date in YYYY-MM-DD format
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -u -d "yesterday" +%Y-%m-%d 2>/dev/null || date -u -v-1d +%Y-%m-%d)

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" >> "$SCRIPT_LOG"
}

# Change to LineLogic directory
cd "$LINELOGIC_HOME"

log "=== Starting daily LineLogic job ==="

# Run recommend-daily for today
if [[ -n "$TO_EMAIL" ]]; then
    log "Running: linelogic recommend-daily --date $TODAY --email $TO_EMAIL"
    RECOMMEND_ARGS=(recommend-daily --date "$TODAY" --email "$TO_EMAIL")
else
    log "Running: linelogic recommend-daily --date $TODAY --no-email (TO_EMAIL not set)"
    RECOMMEND_ARGS=(recommend-daily --date "$TODAY" --no-email)
fi

if .venv/bin/python -m linelogic.app.cli "${RECOMMEND_ARGS[@]}" >> "$SCRIPT_LOG" 2>&1; then
    log "✅ recommend-daily succeeded"
else
    log "❌ recommend-daily failed"
fi

# Wait a moment between commands
sleep 2

# Run settle-daily for yesterday (to settle completed games)
if [[ -n "$TO_EMAIL" ]]; then
    log "Running: linelogic settle-daily --date $YESTERDAY --email $TO_EMAIL"
    SETTLE_ARGS=(settle-daily --date "$YESTERDAY" --email "$TO_EMAIL")
else
    log "Running: linelogic settle-daily --date $YESTERDAY --no-email (TO_EMAIL not set)"
    SETTLE_ARGS=(settle-daily --date "$YESTERDAY" --no-email)
fi

if .venv/bin/python -m linelogic.app.cli "${SETTLE_ARGS[@]}" >> "$SCRIPT_LOG" 2>&1; then
    log "✅ settle-daily succeeded"
else
    log "❌ settle-daily failed"
fi

log "=== Daily LineLogic job complete ==="
