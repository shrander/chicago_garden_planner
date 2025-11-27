#!/bin/sh
# cron-entrypoint.sh - Cron scheduler for garden notifications

set -e

echo "Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready!"
echo "Starting notification scheduler..."

# Function to run at specific times
wait_until_time() {
    target_hour=$1
    target_minute=$2

    while true; do
        current_time=$(date -u +%H%M)
        target_time=$(printf "%02d%02d" "$target_hour" "$target_minute")

        if [ "$current_time" = "$target_time" ]; then
            return 0
        fi

        sleep 30
    done
}

# Function to calculate seconds until next occurrence
seconds_until() {
    target_hour=$1
    target_minute=${2:-0}

    current_hour=$(date -u +%H)
    current_minute=$(date -u +%M)
    current_seconds=$(date -u +%S)

    # Convert everything to minutes from midnight
    current_total=$((current_hour * 60 + current_minute))
    target_total=$((target_hour * 60 + target_minute))

    # Calculate difference
    if [ "$target_total" -gt "$current_total" ]; then
        minutes_diff=$((target_total - current_total))
    else
        # Next occurrence is tomorrow
        minutes_diff=$((1440 - current_total + target_total))
    fi

    # Convert to seconds and subtract current seconds in the minute
    seconds=$((minutes_diff * 60 - current_seconds))
    echo "$seconds"
}

# Function to get day of week (0=Sunday, 6=Saturday)
get_day_of_week() {
    date -u +%w
}

# Daily notifications at 12:00 UTC (6 AM Central)
run_daily() {
    while true; do
        wait_seconds=$(seconds_until 12 0)
        echo "$(date -u) - Next daily notification in $((wait_seconds / 3600))h $((wait_seconds % 3600 / 60))m"
        sleep "$wait_seconds"

        echo "$(date -u) - Running daily notifications..."
        python manage.py send_daily_notifications

        # Sleep a bit to avoid running twice
        sleep 120
    done
}

# Weekly digest on Sundays at 14:00 UTC (8 AM Central)
run_weekly() {
    while true; do
        current_day=$(get_day_of_week)
        current_hour=$(date -u +%H)

        # Calculate hours until next Sunday 14:00 UTC
        if [ "$current_day" -eq 0 ]; then
            # Today is Sunday
            if [ "$current_hour" -lt 14 ]; then
                # Before 14:00, run today
                wait_seconds=$(seconds_until 14 0)
            else
                # After 14:00, next Sunday
                days_until=7
                wait_seconds=$((days_until * 86400 + $(seconds_until 14 0)))
            fi
        else
            # Days until Sunday (0)
            days_until=$((7 - current_day))
            wait_seconds=$((days_until * 86400 + $(seconds_until 14 0)))
        fi

        echo "$(date -u) - Next weekly digest in $((wait_seconds / 86400))d $((wait_seconds % 86400 / 3600))h"
        sleep "$wait_seconds"

        echo "$(date -u) - Running weekly digest..."
        python manage.py send_weekly_digest

        # Sleep a bit to avoid running twice
        sleep 3600
    done
}

# Start both schedulers in background
run_daily &
run_weekly &

echo "Notification schedulers started"
echo "  - Daily: 12:00 UTC (6 AM Central)"
echo "  - Weekly: Sundays 14:00 UTC (8 AM Central)"

# Keep container running
wait
