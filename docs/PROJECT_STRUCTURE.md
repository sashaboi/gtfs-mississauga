# Project Structure

## Directory Layout

```
gtfs-mississauga/
├── static/              # Frontend assets
│   ├── css/
│   │   └── style.css   # All CSS styles (extracted from index.html)
│   └── js/
│       └── app.js      # All JavaScript code (extracted from index.html)
│
├── templates/           # Flask HTML templates
│   ├── index.html      # Main application (now clean, references external files)
│   └── status.html     # API status dashboard
│
├── docs/                # Documentation
│   ├── README.md       # Full documentation
│   ├── TROUBLESHOOTING.md
│   ├── STATUS_PAGE_GUIDE.md
│   ├── TRULY_LIVE_TRACKING.md
│   ├── LIVE_TRACKING.md
│   ├── NEARBY_BUSES.md
│   ├── API_STATUS.md
│   └── ... (other docs)
│
├── scripts/             # Utility scripts
│   ├── setup.sh        # First-time setup
│   ├── run.sh          # Start the application
│   ├── setup_cron.sh   # Setup automated updates
│   └── test_automation.sh
│
├── google_transit/      # GTFS static data
├── data_downloads/      # Downloaded GTFS-RT files
├── logs/                # Application logs
│
├── app.py              # Main Flask application
├── load_gtfs.py        # GTFS data loader
├── ingest_realtime.py  # Real-time data ingester
├── live_updater.py     # Background live data updater
├── health_check.py     # API health checker
├── create_health_table.py
├── nightly_update.py   # Automated update script
├── download_gtfs.py    # GTFS downloader
├── view_realtime.py    # RT data viewer utility
├── requirements.txt    # Python dependencies
├── .gitignore
├── README.md           # Quick start guide
└── miway.db            # SQLite database (generated)
```

## Key Changes

### ✅ Separation of Concerns

**Before:** 
- `index.html` was 1590 lines with inline CSS and JS

**After:**
- `index.html`: 138 lines (clean HTML structure)
- `static/css/style.css`: 523 lines (all styles)
- `static/js/app.js`: 930 lines (all JavaScript)

### ✅ Organized Documentation

All `.md` files moved to `/docs` folder for better organization

### ✅ Centralized Scripts

All `.sh` files moved to `/scripts` folder with updated paths

### ✅ Maintainability

- Easier to edit CSS without touching HTML/JS
- Easier to debug JavaScript separately
- Better code navigation and organization
- Follows standard web development practices

## Running the Application

```bash
# First time
./scripts/setup.sh

# Start app
./scripts/run.sh
```

Application runs on: **http://localhost:5001**
