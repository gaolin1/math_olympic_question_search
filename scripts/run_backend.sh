#!/bin/bash
# Run the FastAPI backend server

cd "$(dirname "$0")/.." || exit

echo "Starting Math Olympic Search API..."
echo "Make sure Ollama is running with qwen3:30b model"
echo ""

cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
