#!/bin/bash
# Run the React frontend dev server

cd "$(dirname "$0")/../frontend" || exit

echo "Starting Math Olympic Search Frontend..."
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

npm run dev
