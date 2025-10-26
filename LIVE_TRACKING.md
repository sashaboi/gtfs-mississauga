# 🚍 Live Bus Tracking Feature

## Overview

The MiWay Route Planner now includes real-time bus tracking on an interactive map!

## Features

### 📍 Live Map View
- Interactive map powered by Leaflet.js (OpenStreetMap)
- Shows all active MiWay buses in real-time
- Bus icons rotate based on heading direction
- Click any bus to see detailed information

### 🚌 Bus Information
When you click on a bus marker, you'll see:
- Route number and name
- Direction/headsign
- Vehicle ID
- Current speed (km/h)
- Current stop location
- Occupancy level (crowding)

### 🎯 Route Filter
- Dropdown to select specific routes
- View all buses or filter by route number
- Auto-loads service alerts for selected route

### 📊 Live Statistics
- **Buses Tracked**: Total number of active buses
- **Routes Active**: Number of routes currently running
- **Last Update**: Timestamp of last data refresh

### 🚨 Service Alerts
- Shows construction notices
- Detour information
- Stop relocations
- Other service disruptions

### 🔄 Auto-Refresh
- Updates every 30 seconds automatically
- Manual refresh button available
- Real-time position tracking

## How to Use

1. **Start the app:**
```bash
./run.sh
```

2. **Open browser:**
```
http://localhost:5001
```

3. **Click the "🚍 Live Tracking" tab**

4. **Select a route from the dropdown or view all buses**

5. **Click on any bus icon** to see details

6. **Watch as buses move** (refreshes every 30 seconds)

## Technical Details

### Map Technology
- **Leaflet.js** - Open-source mapping library
- **OpenStreetMap** - Free map tiles
- **No API key required** - Works out of the box

### Data Sources
- Vehicle positions from `VehiclePositions.pb`
- Service alerts from `Alerts.pb`
- Route information from GTFS static data

### API Endpoints Used

```
GET /api/routes                 - Get all MiWay routes
GET /api/vehicles              - Get all vehicle positions
GET /api/vehicles?route_id=X   - Filter by route
GET /api/alerts               - Get all service alerts
GET /api/alerts?route_id=X    - Get alerts for route
```

### Data Refresh
- Client auto-refreshes every 30 seconds
- To get latest data, run:
```bash
python3 ingest_realtime.py
```

## Example View

### All Routes (127 buses tracked)
Shows every active bus across Mississauga with different routes visible.

### Single Route (e.g., Route 1 - Dundas)
Filters to show only buses on that specific route, with relevant alerts.

## Map Features

### Zoom & Pan
- Scroll to zoom in/out
- Click and drag to pan around
- Double-click to zoom to location

### Bus Markers
- 🚌 Emoji rotates to show bus direction
- Color-coded by route (future enhancement)
- Click for detailed popup

### Info Popup Example
```
🚌 Route 1

Dundas

→ East to Rouge Hill

Vehicle: 2197
Speed: 35.4 km/h
At: Hurontario Station
Occupancy: FEW SEATS AVAILABLE
```

## Performance

- Handles 127+ buses smoothly
- Map tiles cached by browser
- Efficient marker updates (removes old, adds new)
- Minimal memory footprint

## Browser Compatibility

✅ Chrome/Edge
✅ Firefox
✅ Safari
✅ Mobile browsers

## Future Enhancements

Potential additions:
- [ ] Show bus route path on map
- [ ] Predicted arrival times at stops
- [ ] Click stop to see approaching buses
- [ ] Historical data / replays
- [ ] Push notifications for your route
- [ ] Favorite routes
- [ ] Traffic layer
- [ ] Bike-friendly routes

## Troubleshooting

### Map not loading?
- Check browser console for errors
- Ensure internet connection (needs map tiles)
- Verify Leaflet.js is loading

### No buses showing?
- Run `python3 ingest_realtime.py` to load fresh data
- Check if `VehiclePositions.pb` has recent data
- Verify database has vehicle_positions table

### Auto-refresh not working?
- Check browser console
- Switch to another tab and back
- Manually click refresh button

---

**Enjoy tracking your MiWay buses in real-time! 🚌**

