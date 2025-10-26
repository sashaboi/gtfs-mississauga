# 🔄 Automated GTFS Data Updates

## Overview

Automated system for downloading and ingesting fresh GTFS data from MiWay's live feeds.

## Data Sources

All data is fetched from MiWay's official servers:

1. **Static GTFS** (routes, stops, schedules)
   - URL: https://www.miapp.ca/GTFS/google_transit.zip
   - Updated: Daily
   - Size: ~5-10 MB

2. **Vehicle Positions** (live bus locations)
   - URL: https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb
   - Updated: Every 30-60 seconds
   - Size: ~50-100 KB

3. **Trip Updates** (delays, predictions)
   - URL: https://www.miapp.ca/GTFS_RT/TripUpdate/TripUpdates.pb
   - Updated: Every 30-60 seconds
   - Size: ~50-100 KB

4. **Service Alerts** (construction, detours)
   - URL: https://www.miapp.ca/gtfs_rt/Alerts/Alerts.pb
   - Updated: As needed
   - Size: ~10-20 KB

## Components

### 1. `download_gtfs.py`
Downloads latest data from MiWay servers.

**Features:**
- Downloads all 4 data sources
- Backs up old data before replacing
- Extracts static GTFS zip file
- Verifies data integrity
- Detailed progress output

**Usage:**
```bash
python3 download_gtfs.py
```

**Output:**
- `data_downloads/` - Downloaded files
- `google_transit/` - Extracted static GTFS
- `*.pb` files in root - Real-time data

### 2. `nightly_update.py`
Orchestrates the complete update process.

**Process:**
1. Downloads latest data
2. Loads static data to database
3. Loads real-time data to database
4. Reports success/failure

**Usage:**
```bash
python3 nightly_update.py
```

### 3. `run_nightly_update.sh`
Shell script for cron job execution.

**Features:**
- Activates virtual environment
- Creates timestamped log files
- Cleans up old logs (keeps 7 days)
- Proper error handling

### 4. `setup_cron.sh`
Sets up the automated cron job.

**Usage:**
```bash
./setup_cron.sh
```

## Quick Start

### One-Time Setup

1. **Run setup script:**
```bash
./setup_cron.sh
```

2. **Edit crontab:**
```bash
crontab -e
```

3. **Add the cron job line** (shown by setup script)

4. **Save and exit**

### Manual Run

Test the update process:
```bash
./run_nightly_update.sh
```

Or run individual steps:
```bash
# 1. Download data
python3 download_gtfs.py

# 2. Load to database
python3 load_gtfs.py
python3 ingest_realtime.py
```

## Cron Schedule Examples

### Recommended: Daily at 2 AM
```cron
0 2 * * * /path/to/gtfs-mississauga/run_nightly_update.sh
```

### Every Hour
```cron
0 * * * * /path/to/gtfs-mississauga/run_nightly_update.sh
```

### Every 30 Minutes (Real-Time Updates)
```cron
*/30 * * * * /path/to/gtfs-mississauga/run_nightly_update.sh
```

### Twice Daily (Morning & Evening)
```cron
0 6,18 * * * /path/to/gtfs-mississauga/run_nightly_update.sh
```

### Weekdays Only at 5 AM
```cron
0 5 * * 1-5 /path/to/gtfs-mississauga/run_nightly_update.sh
```

## Logs

**Location:** `logs/nightly_update_YYYYMMDD_HHMMSS.log`

**Retention:** Last 7 days (older logs auto-deleted)

**View latest log:**
```bash
ls -lt logs/ | head -2 | tail -1 | awk '{print $9}' | xargs -I {} cat logs/{}
```

**Monitor in real-time:**
```bash
tail -f logs/$(ls -t logs/ | head -1)
```

## Folder Structure

```
gtfs-mississauga/
├── data_downloads/          # Downloaded raw files
│   ├── google_transit.zip
│   ├── VehiclePositions.pb
│   ├── TripUpdates.pb
│   └── Alerts.pb
├── google_transit/          # Extracted GTFS files
│   ├── agency.txt
│   ├── routes.txt
│   ├── stops.txt
│   ├── trips.txt
│   └── stop_times.txt
├── logs/                    # Update logs
│   └── nightly_update_*.log
├── VehiclePositions.pb      # Active real-time data
├── TripUpdates.pb
├── Alerts.pb
├── miway.db                 # SQLite database
├── download_gtfs.py         # Download script
├── nightly_update.py        # Update orchestrator
├── run_nightly_update.sh    # Cron runner
└── setup_cron.sh            # Setup script
```

## Error Handling

### Download Failures
- Network timeout: Retries not implemented yet
- Invalid URL: Check MiWay server status
- Backup data preserved

### Database Failures
- Old data remains intact
- Update stops at failure point
- Check logs for details

### Disk Space
- Ensure 100+ MB free space
- Old backups auto-deleted
- Logs cleaned after 7 days

## Monitoring

### Check Last Update
```bash
ls -lht logs/ | head -2
```

### Check Database
```bash
sqlite3 miway.db "SELECT COUNT(*) FROM vehicle_positions;"
```

### Verify Data Freshness
```bash
stat -f "%Sm" VehiclePositions.pb
```

## Troubleshooting

### Cron Job Not Running

**Check crontab:**
```bash
crontab -l
```

**Check cron logs (macOS):**
```bash
log show --predicate 'process == "cron"' --last 1h
```

**Test script manually:**
```bash
./run_nightly_update.sh
```

### Permission Errors

**Make scripts executable:**
```bash
chmod +x setup_cron.sh
chmod +x run_nightly_update.sh
```

### Virtual Environment Issues

**Ensure venv exists:**
```bash
ls -la venv/bin/python3
```

**Recreate if needed:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Network Issues

**Test connectivity:**
```bash
curl -I https://www.miapp.ca/GTFS/google_transit.zip
```

**Check firewall/proxy settings**

## Best Practices

1. **Backup Database:** Before first automated run
   ```bash
   cp miway.db miway.db.backup
   ```

2. **Monitor Logs:** Check regularly for errors
   ```bash
   tail -20 logs/$(ls -t logs/ | head -1)
   ```

3. **Test Schedule:** Run manually before automating
   ```bash
   ./run_nightly_update.sh
   ```

4. **Disk Space:** Keep 500MB+ free for safety

5. **Update Frequency:**
   - Static data: Once daily is sufficient
   - Real-time: Every 30-60 minutes recommended
   - Alerts: Every hour or with static data

## Performance

**Typical Execution Times:**
- Download: 10-30 seconds
- Load static: 2-3 minutes
- Load real-time: 5-10 seconds
- **Total: ~3-4 minutes**

**Resource Usage:**
- CPU: Low (mostly I/O)
- Memory: ~100-200 MB
- Network: ~10 MB download
- Disk: ~50 MB after extraction

## Advanced

### Webhook Notifications

Add to `run_nightly_update.sh` before exit:
```bash
if [ $EXIT_CODE -eq 0 ]; then
  curl -X POST https://your-webhook-url \
    -d "status=success&time=$(date)"
else
  curl -X POST https://your-webhook-url \
    -d "status=failed&time=$(date)"
fi
```

### Slack Notifications

Install slack webhook:
```bash
pip install slack-sdk
```

Add notification to `nightly_update.py`

### Database Backup Before Update

Add to `run_nightly_update.sh` before running:
```bash
cp miway.db "miway_backup_$(date +%Y%m%d).db"
find . -name "miway_backup_*.db" -mtime +7 -delete
```

---

**Your MiWay app now updates automatically! 🎉**

