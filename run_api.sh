#!/bin/bash
# Script to run the FastAPI server

cd "$(dirname "$0")"

# Add uv to PATH if not already present
export PATH="$HOME/.local/bin:$PATH"

uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
