# 🚀 Quick Start: Automated Updates

## TL;DR

```bash
# One-time setup
./setup_cron.sh
crontab -e  # Add the line shown

# Manual run (test it)
./run_nightly_update.sh

# Check logs
tail -f logs/$(ls -t logs/ | head -1)
```

## What You Get

✅ **Fresh data automatically** - No manual downloads
✅ **Latest bus positions** - Updated every night  
✅ **Current schedules** - Always in sync with MiWay
✅ **Service alerts** - Construction, detours, etc.

## Data Sources (Live from MiWay)

All data fetched from official MiWay servers:

1. **Static GTFS**: https://www.miapp.ca/GTFS/google_transit.zip
   - Routes, stops, schedules
   - ~7 MB, updated daily

2. **Vehicle Positions**: https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb
   - Live bus GPS locations
   - ~10 KB, updates every 30s

3. **Trip Updates**: https://www.miapp.ca/GTFS_RT/TripUpdate/TripUpdates.pb
   - Real-time delays
   - ~200 KB, updates every 30s

4. **Alerts**: https://www.miapp.ca/gtfs_rt/Alerts/Alerts.pb
   - Service disruptions
   - ~20 KB, as needed

## Setup (5 Minutes)

### Step 1: Run Setup Script
```bash
./setup_cron.sh
```

This creates the automation scripts.

### Step 2: Add to Crontab

```bash
crontab -e
```

Paste this line (shown by setup script):
```
0 2 * * * /Users/onkardeshpande/Documents/GitHub/gtfs-mississauga/run_nightly_update.sh
```

Save and exit.

### Step 3: Test It

```bash
./run_nightly_update.sh
```

Watch it download and update everything!

## What Happens Every Night

```
2:00 AM
  ↓
Download latest GTFS data
  ↓
Extract and verify
  ↓
Update database (static data)
  ↓
Update database (real-time)
  ↓
Done! (~3 minutes)
```

## Commands

### Download Only
```bash
python3 download_gtfs.py
```

### Full Update
```bash
python3 nightly_update.py
```

### Check Last Run
```bash
ls -lt logs/ | head -2
```

### View Latest Log
```bash
tail -50 logs/$(ls -t logs/ | head -1)
```

## Schedules

**Daily at 2 AM** (recommended):
```cron
0 2 * * * /path/to/run_nightly_update.sh
```

**Every hour** (more current):
```cron
0 * * * * /path/to/run_nightly_update.sh
```

**Every 30 minutes** (very fresh):
```cron
*/30 * * * * /path/to/run_nightly_update.sh
```

## Folder Structure

```
gtfs-mississauga/
├── data_downloads/         ← Downloaded files
├── google_transit/         ← Extracted GTFS
├── logs/                   ← Update logs
├── *.pb                    ← Real-time data
├── miway.db               ← Your database
└── run_nightly_update.sh  ← Cron script
```

## Troubleshooting

### Cron not running?
```bash
# Check it's in crontab
crontab -l

# Run manually to test
./run_nightly_update.sh
```

### Permission denied?
```bash
chmod +x setup_cron.sh
chmod +x run_nightly_update.sh
```

### Network error?
```bash
# Test connectivity
curl -I https://www.miapp.ca/GTFS/google_transit.zip
```

## Success Indicators

✅ New files in `data_downloads/`
✅ Updated timestamp on `*.pb` files
✅ New log file in `logs/`
✅ No errors in log
✅ App shows fresh data

## Manual Override

Need to update right now?
```bash
./run_nightly_update.sh
```

Or step-by-step:
```bash
python3 download_gtfs.py      # Download
python3 load_gtfs.py          # Load static
python3 ingest_realtime.py    # Load real-time
```

---

**That's it! Your app updates automatically now! 🎉**

Questions? See `AUTOMATED_UPDATES.md` for full documentation.

