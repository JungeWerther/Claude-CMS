#!/bin/bash
# Script to run the FastAPI server

cd "$(dirname "$0")"
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
