#!/bin/sh
# run-cron.sh - Run scheduled notification tasks in background

set -e

echo "Starting cron scheduler for garden notifications..."

# Function to run daily notifications
run_daily() {
    while true; do
        # Calculate seconds until next 6 AM Central (12 PM UTC)
        # For simplicity, run every 24 hours starting at container boot
        # In production, adjust timing as needed

        # Sleep until 6 AM Central Time (12:00 PM UTC)
        current_hour=$(date -u +%H)
        current_minute=$(date -u +%M)

        # Target: 12:00 UTC (6 AM Central)
        target_hour=12
        target_minute=0

        # Calculate minutes until next run
        if [ "$current_hour" -lt "$target_hour" ]; then
            hours_until=$((target_hour - current_hour))
        elif [ "$current_hour" -eq "$target_hour" ] && [ "$current_minute" -lt "$target_minute" ]; then
            hours_until=0
        else
            hours_until=$((24 - current_hour + target_hour))
        fi

        minutes_until=$((hours_until * 60 + target_minute - current_minute))
        seconds_until=$((minutes_until * 60))

        echo "Next daily notification run in $minutes_until minutes"
        sleep "$seconds_until"

        echo "Running daily notifications..."
        python manage.py send_daily_notifications

        # Sleep for a bit to avoid running twice in the same minute
        sleep 120
    done
}

# Function to run weekly notifications
run_weekly() {
    while true; do
        # Run on Sundays at 8 AM Central (2 PM UTC)
        current_day=$(date -u +%u)  # 1=Monday, 7=Sunday
        current_hour=$(date -u +%H)

        # Target: Sunday (day 7) at 14:00 UTC
        if [ "$current_day" -eq 7 ] && [ "$current_hour" -ge 14 ]; then
            # Already past this week's run, wait until next Sunday
            days_until=7
        elif [ "$current_day" -eq 7 ]; then
            # Today is Sunday but before run time
            days_until=0
        else
            # Calculate days until Sunday
            days_until=$((7 - current_day))
        fi

        # Calculate total seconds to sleep
        hours_today=$((24 - current_hour + 14))
        if [ "$days_until" -eq 0 ]; then
            hours_until=$((14 - current_hour))
        else
            hours_until=$((days_until * 24 + 14 - current_hour))
        fi

        seconds_until=$((hours_until * 3600))

        echo "Next weekly digest run in $((hours_until / 24)) days and $((hours_until % 24)) hours"
        sleep "$seconds_until"

        echo "Running weekly digest..."
        python manage.py send_weekly_digest

        # Sleep for a bit to avoid running twice
        sleep 3600
    done
}

# Run both schedulers in background
run_daily &
run_weekly &

# Keep the script running
wait
