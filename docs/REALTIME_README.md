# GTFS-Realtime Integration

## Overview

This system ingests real-time transit data from Protocol Buffer (.pb) files provided by MiWay GTFS-Realtime feeds.

## What Are .pb Files?

**Protocol Buffers (.pb)** are Google's efficient binary format for serializing structured data. GTFS-Realtime uses this format to provide:

1. **Service Alerts** - Construction, detours, stop changes
2. **Trip Updates** - Real-time arrival/departure predictions and delays
3. **Vehicle Positions** - Live bus locations on the map

## Files Ingested

```
Alerts.pb          → Service alerts, detours, stop changes
TripUpdates.pb     → Real-time trip delays and predictions
VehiclePositions.pb → Live bus GPS coordinates
```

## Database Schema

### Real-Time Tables Created:

**1. `alerts`** - Service disruptions
- alert_id, cause, effect, header_text, description_text, url, timestamp

**2. `alert_affected_entities`** - What routes/stops/trips are affected
- alert_id, entity_type, route_id, trip_id, stop_id

**3. `trip_updates`** - Real-time trip status
- trip_id, route_id, start_date, start_time, schedule_relationship, timestamp

**4. `stop_time_updates`** - Predictions for specific stops
- trip_update_id, stop_sequence, stop_id, arrival_delay, arrival_time, departure_delay, departure_time

**5. `vehicle_positions`** - Live bus locations
- vehicle_id, trip_id, route_id, latitude, longitude, bearing, speed, current_stop_id, occupancy_status, timestamp

## Usage

### 1. Ingest Real-Time Data

```bash
python3 ingest_realtime.py
```

This will:
- Parse all three .pb files
- Load data into the database
- Show summary statistics

**Current Data (from last run):**
- 69 Service Alerts
- 131 Trip Updates
- 127 Live Vehicle Positions

### 2. View Real-Time Data

```bash
python3 view_realtime.py
```

This displays:
- Active service alerts with affected routes/stops
- Live bus positions with GPS coordinates, speed, and occupancy
- Trip updates showing delays in minutes

## Example Data

### Service Alert Example:
```
📢 Alert: 3 Bloor
   Cause: CONSTRUCTION
   Effect: STOP_MOVED
   Description: Stop 1348 on Bloor St at Grand Forks Rd is relocated 45 metres east
   Affects: Route 3
```

### Vehicle Position Example:
```
🚌 Vehicle 2197 - Route 1 Dundas
   Location: 43.60267, -79.59108
   Speed: 35.4 km/h
   Bearing: 37°
   Occupancy: FEW_SEATS_AVAILABLE
```

### Trip Update Example:
```
🚌 Route 5 - Dixie
   Trip ID: 28656975
   Schedule: SCHEDULED
   Delays:
      - Burnhamthorpe Terminal: 3 min late
      - Matheson Blvd: 2 min late
```

## Integration with Web App

The real-time data can be used to enhance the route planner:

1. **Show delays** on search results
2. **Display live bus locations** on a map
3. **Alert users** to service disruptions
4. **Show bus occupancy** (crowding levels)
5. **Update arrival times** with real-time predictions

## Automated Updates

For production, you should:

1. **Fetch fresh .pb files** periodically (every 30-60 seconds)
2. **Run ingestion automatically** via cron job or background task
3. **Cache results** to minimize database queries

Example cron job (every minute):
```bash
* * * * * cd /path/to/project && ./venv/bin/python3 ingest_realtime.py > /dev/null 2>&1
```

## API Endpoints (Future Enhancement)

Potential endpoints to add to `app.py`:

```python
GET  /api/alerts              # Get all active alerts
GET  /api/alerts/route/:id    # Get alerts for specific route
GET  /api/vehicles            # Get all vehicle positions
GET  /api/vehicles/route/:id  # Get vehicles on specific route
GET  /api/trip-delay/:trip_id # Get real-time delays for trip
```

## Dependencies

```bash
pip install gtfs-realtime-bindings requests
```

## Resources

- [GTFS-Realtime Specification](https://developers.google.com/transit/gtfs-realtime/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [GTFS-Realtime Bindings (Python)](https://pypi.org/project/gtfs-realtime-bindings/)

## Performance Notes

- Vehicle positions update every 30-60 seconds
- Trip updates update every 30-60 seconds  
- Alerts update less frequently (hourly or as needed)
- Old data is automatically purged (trip updates older than 1 hour)

---

✅ **Real-time data is now fully integrated!**

