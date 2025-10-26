# MiWay Route Planner

A web application for planning bus routes using Mississauga MiWay GTFS data.

## Features

- Search for direct routes between any two bus stops
- View departure and arrival times
- See next available buses
- Complete route details with all intermediate stops

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

## How it works

The app loads GTFS (General Transit Feed Specification) data from the `google_transit/` folder into a SQLite database. It then queries this database to find trips that contain both your source and destination stops in the correct order.

No complex pathfinding needed - the GTFS data already contains complete trip information!

