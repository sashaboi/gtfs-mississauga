#!/bin/bash
# Setup Cron Job for Nightly Updates

PROJECT_DIR="/Users/onkardeshpande/Documents/GitHub/gtfs-mississauga"
LOG_DIR="$PROJECT_DIR/logs"
VENV_PATH="$PROJECT_DIR/venv/bin/python3"

# Create logs directory
mkdir -p "$LOG_DIR"

# Create the cron job script
cat > "$PROJECT_DIR/run_nightly_update.sh" << 'EOF'
#!/bin/bash
# Nightly Update Runner Script

# Set project directory
PROJECT_DIR="/Users/onkardeshpande/Documents/GitHub/gtfs-mississauga"
cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Create log file with timestamp
LOG_FILE="logs/nightly_update_$(date +%Y%m%d_%H%M%S).log"

# Run the update
echo "Starting nightly update at $(date)" > "$LOG_FILE"
python3 nightly_update.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "Completed with exit code: $EXIT_CODE at $(date)" >> "$LOG_FILE"

# Keep only last 7 days of logs
find logs/ -name "nightly_update_*.log" -mtime +7 -delete

exit $EXIT_CODE
EOF

chmod +x "$PROJECT_DIR/run_nightly_update.sh"

echo "=============================="
echo "Cron Job Setup"
echo "=============================="
echo ""
echo "The nightly update script has been created at:"
echo "  $PROJECT_DIR/run_nightly_update.sh"
echo ""
echo "To schedule it to run daily at 2:00 AM, add this to your crontab:"
echo ""
echo "# MiWay GTFS Nightly Update"
echo "0 2 * * * $PROJECT_DIR/run_nightly_update.sh"
echo ""
echo "To edit your crontab, run:"
echo "  crontab -e"
echo ""
echo "Then paste the line above."
echo ""
echo "Alternative schedules:"
echo "  Every hour:        0 * * * * $PROJECT_DIR/run_nightly_update.sh"
echo "  Every 30 minutes:  */30 * * * * $PROJECT_DIR/run_nightly_update.sh"
echo "  Every day at noon: 0 12 * * * $PROJECT_DIR/run_nightly_update.sh"
echo ""
echo "Logs will be stored in: $LOG_DIR"
echo ""
echo "To test the script now, run:"
echo "  $PROJECT_DIR/run_nightly_update.sh"
echo ""

