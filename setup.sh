#!/bin/bash
# MiWay Route Planner - Setup Script

echo "🚌 MiWay Route Planner - Setup"
echo "=============================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install Flask gtfs-realtime-bindings requests

echo ""
echo "Loading GTFS static data into database..."
python3 load_gtfs.py

echo ""
echo "Loading GTFS real-time data (alerts, vehicles, delays)..."
python3 ingest_realtime.py

echo ""
echo "=============================="
echo "✅ Setup complete!"
echo "=============================="
echo ""
echo "To start the app, run:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python3 app.py"
echo ""

