#!/bin/bash
# Run the tagging pipeline to tag all problems

cd "$(dirname "$0")/.." || exit

echo "Running tagging pipeline..."
echo "Make sure Ollama is running with qwen3:30b model"
echo ""

cd backend
python -m tagging.tagger "$@"
