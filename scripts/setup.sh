#!/bin/bash
# MiWay Route Planner - Setup Script

# Change to project root directory
cd "$(dirname "$0")/.."

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
python3 utils/load_gtfs.py

echo ""
echo "Creating health check table..."
python3 utils/create_health_table.py

echo ""
echo "Loading GTFS real-time data (alerts, vehicles, delays)..."
python3 utils/ingest_realtime.py

echo ""
echo "=============================="
echo "✅ Setup complete!"
echo "=============================="
echo ""
echo "To start the app, run:"
echo "  ./scripts/run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python3 app.py"
echo ""

