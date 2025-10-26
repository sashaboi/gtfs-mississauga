# MiWay Route Planner

A web application for planning bus routes using Mississauga MiWay GTFS data.

## Features

### Static Route Planning
- Search for direct routes between any two bus stops
- View departure and arrival times
- See next available buses
- Complete route details with all intermediate stops
- 📍 Location-based stop finder (uses browser GPS)

### Real-Time Data
- 🚨 Live service alerts (construction, detours, stop changes)
- 🚍 Real-time bus positions (127+ buses tracked)
- ⏰ Trip delay predictions
- 👥 Bus occupancy status (crowding levels)
- 📍 **Find buses near you** - Shows which buses you can catch with ETAs!

## Quick Start

### Option 1: Using Scripts (Recommended)

1. **First time setup:**
```bash
./setup.sh
```

2. **Run the app:**
```bash
./run.sh
```

3. **Open browser to:** `http://localhost:5001`

### Option 2: Manual Setup

1. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install Flask
```

3. **Load GTFS data into database:**
```bash
python3 load_gtfs.py
```

4. **Run the app:**
```bash
python3 app.py
```

5. **Open browser to:** `http://localhost:5001`

### Optional: Load Real-Time Data

To add live bus tracking, alerts, and delays:

```bash
source venv/bin/activate
python3 ingest_realtime.py
```

This loads:
- Service alerts (construction, detours)
- Live vehicle positions (GPS coordinates)
- Real-time trip updates (delays)

View the data:
```bash
python3 view_realtime.py
```

See [REALTIME_README.md](REALTIME_README.md) for more details.

## Automated Updates (NEW!)

Keep your data fresh automatically! The app can download the latest GTFS data from MiWay's servers.

### Quick Setup
```bash
./setup_cron.sh
crontab -e  # Add the line shown
```

This will update your app nightly with:
- ✅ Latest routes and schedules
- ✅ Fresh vehicle positions  
- ✅ Current service alerts

**Data Sources:**
- Static GTFS: https://www.miapp.ca/GTFS/google_transit.zip
- Vehicle Positions: https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb
- Trip Updates: https://www.miapp.ca/GTFS_RT/TripUpdate/TripUpdates.pb
- Alerts: https://www.miapp.ca/gtfs_rt/Alerts/Alerts.pb

See [AUTOMATED_UPDATES.md](AUTOMATED_UPDATES.md) for full documentation.

## How it works

The app loads GTFS (General Transit Feed Specification) data from the `google_transit/` folder into a SQLite database. It then queries this database to find trips that contain both your source and destination stops in the correct order.

No complex pathfinding needed - the GTFS data already contains complete trip information!

