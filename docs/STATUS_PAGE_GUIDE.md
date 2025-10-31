# API Status Dashboard Guide

## Overview

The API Status Dashboard provides real-time monitoring of MiWay GTFS endpoints, tracking their health, performance, and availability over time.

## Access

Visit: **http://localhost:5001/status**

Or click the **"🔍 API Status"** link in the top navigation bar of the main app.

## Features

### 1. Current Status Cards

Live status of all four MiWay GTFS endpoints:
- **Static GTFS** - Static schedule data (ZIP file)
- **Vehicle Positions** - Real-time bus locations
- **Trip Updates** - Real-time trip delays and updates
- **Alerts** - Service alerts and disruptions

Each card shows:
- ✅ **Healthy** - Endpoint working correctly
- ❌ **Error** - Connection or server issues
- ⚠️ **Rate Limited** - Too many requests
- ⏱️ **Timeout** - Response took too long

### 2. Detailed Metrics

For each endpoint:
- **HTTP Status Code** - Server response code
- **Response Time** - How long the request took (in seconds)
- **Content Size** - Size of data returned
- **Error Message** - Details if something went wrong
- **Last Check** - When this endpoint was last tested

### 3. 24-Hour Statistics

Shows uptime percentage for each endpoint over the last 24 hours:
- **Uptime %** - Percentage of successful checks
- **Total Checks** - Number of health checks performed
- **Passed/Failed** - Breakdown of results

### 4. Health Check History

Complete log of recent health checks (last 50 by default):
- Full timeline of all endpoint checks
- Timestamp for each check
- Status and error details
- Response times and data sizes

## How It Works

### Data Collection

1. Health checks are run periodically using `health_check.py`
2. Results are stored in the `health_checks` table in `miway.db`
3. Dashboard queries this data via REST API endpoints

### Running Manual Health Checks

```bash
# Run a single health check
python3 health_check.py

# Monitor continuously for 5 minutes (checks every 30 seconds)
python3 health_check.py monitor 300 30
```

### Auto-Refresh

The dashboard automatically refreshes every 30 seconds to show the latest data.

## Database Schema

```sql
CREATE TABLE health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    endpoint_name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    status TEXT NOT NULL,
    status_code INTEGER,
    response_time REAL,
    content_length INTEGER,
    error_message TEXT,
    rate_limited INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

The status page uses these backend endpoints:

### `/api/health-history`
Returns recent health check records.

**Parameters:**
- `limit` (optional, default: 100) - Number of records to return
- `endpoint` (optional) - Filter by specific endpoint name

**Example:**
```
GET /api/health-history?limit=50
GET /api/health-history?endpoint=Vehicle%20Positions
```

### `/api/health-summary`
Returns latest status and 24-hour statistics for all endpoints.

**Response:**
```json
{
  "latest": [
    {
      "endpoint_name": "Vehicle Positions",
      "status": "healthy",
      "status_code": 200,
      "response_time": 0.45,
      "content_length": 15234,
      "timestamp": "2025-10-28T17:09:39"
    }
  ],
  "stats_24h": [
    {
      "endpoint_name": "Vehicle Positions",
      "total_checks": 120,
      "healthy_count": 115,
      "rate_limited_count": 0,
      "avg_response_time": 0.52
    }
  ]
}
```

## Interpreting Results

### Status Types

| Status | Meaning | Action |
|--------|---------|--------|
| `healthy` | ✅ Endpoint working perfectly | None needed |
| `connection_error` | ❌ Can't connect to server | Server may be down |
| `timeout` | ⏱️ Request took too long | Server overloaded or slow |
| `rate_limited` | ⚠️ Too many requests (429) | Reduce check frequency |
| `server_error` | 🔥 Server error (5xx) | MiWay server issue |
| `client_error` | ❌ Client error (4xx) | Request problem |

### Response Times

- **< 1 second** - Excellent
- **1-3 seconds** - Good
- **3-5 seconds** - Acceptable
- **> 5 seconds** - Slow (may timeout)

### Content Sizes

- **Vehicle Positions**: ~10-50 KB (varies by number of active buses)
- **Trip Updates**: ~20-100 KB (varies by active trips)
- **Alerts**: ~1-10 KB (usually small)
- **Static GTFS**: ~2-5 MB (large ZIP file)

## Troubleshooting

### No Data Showing

If the dashboard shows "No health check data available yet":

1. Run a health check manually:
   ```bash
   python3 health_check.py
   ```

2. Check the database:
   ```bash
   sqlite3 miway.db "SELECT COUNT(*) FROM health_checks;"
   ```

3. Ensure the `health_checks` table exists:
   ```bash
   python3 create_health_table.py
   ```

### All Endpoints Show Errors

This is currently expected! MiWay's API servers are experiencing issues (503 Service Unavailable). The dashboard will show errors until MiWay fixes their servers.

### Rate Limiting

If you see rate limiting warnings:
1. Reduce background update frequency in `app.py`
2. Increase delay between health checks
3. The app already implements proper headers and delays

## Scheduled Monitoring

You can set up automatic health checks using cron:

```bash
# Check every hour
0 * * * * cd /path/to/gtfs-mississauga && /path/to/venv/bin/python3 health_check.py

# Check every 30 minutes
*/30 * * * * cd /path/to/gtfs-mississauga && /path/to/venv/bin/python3 health_check.py
```

## Benefits

1. **Transparency** - See exactly when and why APIs fail
2. **Historical Data** - Track patterns and uptime over time
3. **Debugging** - Detailed error messages help diagnose issues
4. **Monitoring** - Know immediately when services are down
5. **Performance Tracking** - Monitor response times and data sizes

## Future Enhancements

Potential improvements:
- Email/SMS alerts when endpoints go down
- Uptime percentage graphs
- Response time charts
- Configurable alert thresholds
- Export history to CSV
- Endpoint-specific views with deep dive analytics

---

**Note:** The status dashboard is independent of the main app. Even if MiWay APIs are down, you can still view route planning features using static GTFS data.

