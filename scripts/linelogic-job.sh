#!/bin/bash
# LineLogic job management helper

LABEL="com.linelogic.daily-job"
PLIST="/Users/bbrennan/Library/LaunchAgents/com.linelogic.daily-job.plist"
LOG_DIR="/Users/bbrennan/Desktop/LineLogic/.linelogic"

case "${1:-status}" in
    start)
        echo "Starting LineLogic daily job..."
        launchctl load "$PLIST" 2>/dev/null || launchctl start "$LABEL"
        echo "✅ Job started"
        ;;
    
    stop)
        echo "Stopping LineLogic daily job..."
        launchctl stop "$LABEL"
        echo "✅ Job stopped"
        ;;
    
    restart)
        echo "Restarting LineLogic daily job..."
        launchctl stop "$LABEL"
        sleep 1
        launchctl start "$LABEL"
        echo "✅ Job restarted"
        ;;
    
    status)
        echo "LineLogic Job Status:"
        if launchctl list | grep -q "$LABEL"; then
            echo "✅ Loaded"
            launchctl list "$LABEL"
        else
            echo "❌ Not loaded"
        fi
        ;;
    
    logs)
        echo "=== Job Log (daily_job.log) ==="
        tail -50 "$LOG_DIR/daily_job.log"
        echo ""
        echo "=== LaunchAgent stdout ==="
        tail -20 "$LOG_DIR/launchd.out.log" 2>/dev/null || echo "(no output yet)"
        ;;
    
    unload)
        echo "Unloading LineLogic daily job..."
        launchctl unload "$PLIST"
        echo "✅ Job unloaded"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|unload}"
        echo ""
        echo "Examples:"
        echo "  $0 status          # Check if job is running"
        echo "  $0 logs            # View recent job logs"
        echo "  $0 stop            # Temporarily stop job"
        echo "  $0 start           # Resume job"
        echo "  $0 unload          # Permanently remove job"
        ;;
esac
