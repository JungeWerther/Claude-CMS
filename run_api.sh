#!/bin/bash
# Script to run the FastAPI server

# Get the absolute path to the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Add uv to PATH if not already present
export PATH="$HOME/.local/bin:$PATH"

# Add current directory to PYTHONPATH so Python can find lib and services modules
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
