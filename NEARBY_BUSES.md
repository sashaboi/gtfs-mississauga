# 📍 Find Buses Near Me Feature

## Overview

A powerful new feature that shows which buses you can catch from your current location, complete with real-time ETAs!

## How It Works

### User Flow
1. Click **"📍 Find Buses Near Me"** button on Live Tracking tab
2. Grant location permission when prompted
3. App finds your nearest stops (within 500m)
4. Identifies buses heading to those stops
5. Shows sorted list with ETAs
6. Click any bus card to see it on the map

### Behind the Scenes
1. **Get user location** via browser Geolocation API
2. **Find nearby stops** using Haversine distance formula
3. **Match vehicles to stops** by checking their upcoming route
4. **Calculate ETA** based on distance and average speed
5. **Sort by arrival time** (soonest first)

## Features

### 🚌 Smart Bus Matching
- Checks each vehicle's upcoming stops
- Only shows buses actually heading to your nearby stops
- Filters out buses more than 30 minutes away

### ⏰ Real-Time ETAs
- Color-coded by urgency:
  - **Red (pulsing)**: 0-5 minutes - "Now"
  - **Yellow**: 6-10 minutes - "Soon"
  - **Green**: 11+ minutes

### 📍 Map Integration
- Your location marked with red circle
- Nearby buses highlighted (others dimmed)
- Click bus card to zoom and focus on map
- User location displayed at 📍 marker

### 📊 Rich Information
For each bus, you see:
- Route number and name
- Direction/headsign
- Exact stop it will arrive at
- Distance of stop from you
- Vehicle ID
- Occupancy status (how crowded)
- ETA in minutes

## API Endpoint

### `POST /api/nearby-buses`

**Request:**
```json
{
  "latitude": 43.5890,
  "longitude": -79.6441,
  "radius": 0.5
}
```

**Response:**
```json
{
  "buses": [
    {
      "vehicle_id": "2197",
      "route_number": "1",
      "route_name": "Dundas",
      "headsign": "East to Rouge Hill",
      "stop_name": "Hurontario Station",
      "stop_distance_from_user": 0.3,
      "bus_distance_from_stop": 1.2,
      "eta_minutes": 5,
      "vehicle_lat": 43.5892,
      "vehicle_lon": -79.6450,
      "occupancy": "FEW_SEATS_AVAILABLE"
    }
  ],
  "nearby_stops": [...],
  "count": 10,
  "user_location": {
    "latitude": 43.5890,
    "longitude": -79.6441
  }
}
```

## Algorithm Details

### ETA Calculation
```
1. Get distance from vehicle to stop (Haversine formula)
2. Assume average bus speed: 25 km/h
3. ETA (minutes) = (distance_km / 25) * 60
```

### Stop Matching
```python
For each vehicle:
  1. Get vehicle's current trip_id
  2. Query upcoming stops in sequence
  3. Check if any match user's nearby stops
  4. If yes, calculate ETA and add to results
  5. Filter: only show if ETA <= 30 minutes
```

### Nearby Stops
- Uses same logic as "Use My Location" feature
- Searches within 500m radius by default
- Sorted by distance from user
- Maximum 10 stops checked

## Example Use Cases

### Scenario 1: Morning Commute
```
User at home, needs to get to work
→ Click "Find Buses Near Me"
→ Sees Route 3 arriving in 4 minutes at nearby stop
→ Clicks card to see bus on map
→ Leaves house to catch bus
```

### Scenario 2: Evening Plans
```
User at Square One, wants to go downtown
→ Multiple buses available
→ Sees Route 19 (8 min) and Route 26 (12 min)
→ Checks occupancy: Route 19 is FULL
→ Decides to wait for Route 26 with seats available
```

### Scenario 3: New to Area
```
Tourist doesn't know the bus routes
→ Click button to see all options
→ App shows 5 different buses they can take
→ Each with stop name and direction
→ Easy decision making
```

## UI Components

### Bus Card Layout
```
┌─────────────────────────────────┐
│ [Route 1]        [ETA: 5 mins]  │
│                                  │
│ Dundas                           │
│ → East to Rouge Hill             │
│                                  │
│ 📍 Stop: Hurontario Station      │
│    (0.3 km away)                 │
│ 🚌 Vehicle: 2197                 │
│ 👥 FEW SEATS AVAILABLE           │
└─────────────────────────────────┘
```

### Color Coding
- **Route Badge**: Purple gradient
- **ETA Green**: 11+ minutes away
- **ETA Yellow**: 6-10 minutes (soon)
- **ETA Red (pulsing)**: 0-5 minutes (hurry!)
- **User Marker**: Red circle

## Performance

- Efficient query using indexes on trip_id and stop_id
- Limits to 10 nearest stops
- Only checks 20 upcoming stops per vehicle
- Results sorted by ETA (client-side)
- Map updates smoothly with markers

## Future Enhancements

Potential improvements:
- [ ] Use real-time trip updates for accurate ETAs
- [ ] Account for traffic delays
- [ ] Show walking directions to stop
- [ ] Push notifications when bus is 2 min away
- [ ] Save favorite stops
- [ ] "Remind me" feature
- [ ] Multiple destination routing
- [ ] Compare routes by fastest arrival time

## Technical Notes

### Accuracy
- ETAs are estimates based on average speed
- Does not account for:
  - Traffic conditions
  - Scheduled stops
  - Time of day variations
  - Weather delays
- For most accurate times, check real-time trip updates

### Browser Compatibility
- Requires Geolocation API support
- Works on: Chrome, Firefox, Safari, Edge
- Mobile browsers fully supported
- HTTPS required in production (not on localhost)

### Privacy
- Location accessed only when button clicked
- Not stored or logged
- Used only for current query
- Permission prompt shown by browser

## Troubleshooting

### "Location permission denied"
- User needs to allow location in browser settings
- On mobile: check app permissions
- Try refreshing page

### "No buses found nearby"
- Check if real-time data is loaded
- Run: `python3 ingest_realtime.py`
- May be no buses in area currently
- Try increasing radius (future feature)

### "Error finding buses"
- Check database connection
- Verify vehicle_positions table has data
- Check browser console for errors

---

**Now you'll never miss your bus! 🚌**

