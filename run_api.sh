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

# Run uvicorn using python -m to ensure PYTHONPATH is respected
nohup uv run python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "FastAPI server started in background (PID: $(cat "$PID_FILE"))"
echo "Logs: $LOG_FILE"
echo "To stop: kill \$(cat $PID_FILE)"
