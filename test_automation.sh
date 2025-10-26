#!/bin/bash
# Test the automation system

echo "=============================="
echo "Testing Automation System"
echo "=============================="
echo ""

# Test 1: Download
echo "Test 1: Downloading data..."
python3 download_gtfs.py
if [ $? -eq 0 ]; then
    echo "✅ Download test passed"
else
    echo "❌ Download test failed"
    exit 1
fi

echo ""
echo "=============================="
echo ""

# Test 2: Check files exist
echo "Test 2: Verifying files..."
FILES=("VehiclePositions.pb" "TripUpdates.pb" "Alerts.pb" "google_transit/stops.txt")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
        exit 1
    fi
done

echo ""
echo "=============================="
echo ""

echo "✅ All automation tests passed!"
echo ""
echo "To enable nightly updates:"
echo "  1. Run: ./setup_cron.sh"
echo "  2. Run: crontab -e"
echo "  3. Add the cron line shown"
echo ""

