#!/bin/bash
# Script to run the FastAPI server

# Get the absolute path to the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Add uv to PATH if not already present
export PATH="$HOME/.local/bin:$PATH"

# Add current directory to PYTHONPATH so Python can find lib and services modules
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# PID file location
PID_FILE="$SCRIPT_DIR/uvicorn.pid"
LOG_FILE="$SCRIPT_DIR/uvicorn.log"

# Kill any currently running service if it exists
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Stopping existing server (PID: $OLD_PID)..."
        kill "$OLD_PID"
        sleep 1
        # Force kill if still running
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            kill -9 "$OLD_PID"
        fi
    fi
    rm -f "$PID_FILE"
fi


# Run uvicorn using python -m to ensure PYTHONPATH is respected
nohup uv run python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "FastAPI server started in background on port 8000 (PID: $(cat "$PID_FILE"))"
echo "Logs: $LOG_FILE"
echo "To stop: kill \$(cat $PID_FILE)"
