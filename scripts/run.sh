#!/bin/bash
# MiWay Route Planner - Startup Script

# Change to project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Check if database exists
if [ ! -f "miway.db" ]; then
    echo "❌ Database not found!"
    echo "Please run: ./scripts/setup.sh first"
    exit 1
fi

# Start the app
echo "🚌 Starting MiWay Route Planner..."
echo "🌐 Open your browser to: http://localhost:5001"
echo ""
python3 app.py

