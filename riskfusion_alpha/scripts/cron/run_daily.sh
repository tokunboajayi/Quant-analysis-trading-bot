#!/bin/bash
# RiskFusion Daily Runner Wrapper
# Usage: ./run_daily.sh

set -e

# Change to project root (assumed script is in scripts/cron)
cd "$(dirname "$0")/../.."

# Load env
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

DATE=$(date +%Y-%m-%d)
LOG_DIR="data/audit/cron_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run_$DATE.log"

echo "[$(date)] Starting Daily Run for $DATE..." | tee -a "$LOG_FILE"

# Run (via python direct or docker)
# Using python direct here assuming venv is active or available.
# Ideally use absolute path to python in venv
VENV_PYTHON=".venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python"
fi

$VENV_PYTHON -m riskfusion.cli run_daily --date "$DATE" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] SUCCESS." | tee -a "$LOG_FILE"
else
    echo "[$(date)] FAILED. Exit code $EXIT_CODE" | tee -a "$LOG_FILE"
    # Optional: Send Alert
fi
