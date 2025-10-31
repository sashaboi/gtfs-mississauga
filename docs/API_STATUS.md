# MiWay API Status Report

**Last Checked:** October 28, 2025

## Issue Summary

The MiWay GTFS Real-Time API endpoints are currently **UNAVAILABLE**.

## Error Details

```
Connection error: ('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
```

### Failed Endpoints

1. **Vehicle Positions**: `https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb`
2. **Trip Updates**: `https://www.miapp.ca/GTFS_RT/TripUpdate/TripUpdates.pb`
3. **Alerts**: `https://www.miapp.ca/gtfs_rt/Alerts/Alerts.pb`
4. **Static GTFS**: `https://www.miapp.ca/GTFS/google_transit.zip`

### Technical Analysis

- **HTTP Status**: 503 Service Unavailable (when using HTTP)
- **HTTPS Status**: Connection reset during TLS handshake
- **Network Test**: Even `curl -k` (insecure) fails at TLS level
- **Conclusion**: Server-side issue, not a client/code problem

## Current Workaround

The application will continue to work with:

### ✅ **Available Features:**
- Route planning using **static GTFS data** (loaded locally)
- Stop search and nearby stops
- Route information and schedules

### ❌ **Unavailable Features:**
- Live bus tracking (requires real-time vehicle positions)
- Real-time ETAs (requires trip updates)
- Service alerts (requires alerts feed)

## What Works

Since we have the static GTFS data loaded in `miway.db`, these features work perfectly:
- All route planning
- Stop locations
- Schedule information
- All the UI functionality

## How to Verify API is Back Online

Run the health check:

```bash
python3 health_check.py
```

Look for `✅ Healthy` status for all endpoints.

## Alternative Solutions

### Option 1: Wait for MiWay to Fix Their Servers
- Monitor the endpoints periodically
- The app will automatically resume live tracking once APIs are available

### Option 2: Use Mock/Simulated Data (Development)
- We can create simulated vehicle positions for testing
- Not useful for production but good for UI development

### Option 3: Contact MiWay IT
- Report the API outage to MiWay technical support
- Ask for alternative endpoints or status updates

## App Behavior

The application has been updated to:
1. ✅ **Gracefully handle API failures** - No crashes
2. ✅ **Show error details** - Users see what's wrong
3. ✅ **Continue working** - Route planning still functions
4. ⏱️ **Retry automatically** - Background worker will reconnect when APIs are back

## Error Handling in Code

The code now:
- Catches connection errors
- Returns detailed error information
- Logs all API failures
- Provides fallback behavior
- Shows user-friendly messages in UI

---

**Next Steps:**
1. Keep the app running - it won't crash
2. Route planning features work fine with static data  
3. Live tracking will auto-resume when MiWay fixes their servers
4. Check API status periodically with `python3 health_check.py`

