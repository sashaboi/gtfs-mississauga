# MiWay Route Planner 🚌

A real-time web application for planning bus routes and tracking live buses using Mississauga MiWay GTFS data.

## Quick Start

```bash
# First time setup
./scripts/setup.sh

# Run the application
./scripts/run.sh
```

Then open: **http://localhost:5001**

## Project Structure

```
gtfs-mississauga/
├── static/           # Frontend assets
│   ├── css/         # Stylesheets
│   └── js/          # JavaScript files
├── templates/       # HTML templates
├── docs/            # Documentation
├── scripts/         # Setup and run scripts
├── google_transit/  # GTFS data files
├── app.py           # Main Flask application
├── load_gtfs.py     # GTFS data loader
├── ingest_realtime.py  # Real-time data ingester
├── live_updater.py  # Background live data updater
└── requirements.txt # Python dependencies
```

## Features

- ✅ Real-time bus tracking with live map
- ✅ Route planning between stops
- ✅ Find buses near you with ETAs
- ✅ Service alerts and notifications
- ✅ Location-based stop finder
- ✅ API health monitoring dashboard

## Documentation

Full documentation is available in the `/docs` folder:

- **[Full Documentation](docs/README.md)** - Complete user guide
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[API Status Guide](docs/STATUS_PAGE_GUIDE.md)** - How to use the status dashboard
- **[Live Tracking](docs/TRULY_LIVE_TRACKING.md)** - How real-time updates work

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: Vanilla JavaScript, Leaflet.js for maps
- **Data**: GTFS & GTFS-Realtime from MiWay

## License

This project is for educational purposes.

---

Made with ❤️ for Mississauga transit riders


