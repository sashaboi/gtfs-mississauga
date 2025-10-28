"""
MiWay Route Planner - Flask Web Application
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import math
import threading
import time
from live_updater import update_all_realtime_data

app = Flask(__name__)
DB_FILE = 'miway.db'

# Track last update time and background worker
last_update_time = None
update_lock = threading.Lock()
background_worker = None
worker_running = False


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def get_all_stops():
    """Get all stops for dropdown"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get unique stops (excluding parent stations)
    cursor.execute("""
        SELECT DISTINCT stop_id, stop_name, stop_lat, stop_lon
        FROM stops 
        WHERE location_type = 0
        ORDER BY stop_name
    """)
    
    stops = [{'id': row['stop_id'], 'name': row['stop_name'], 'lat': row['stop_lat'], 'lon': row['stop_lon']} for row in cursor.fetchall()]
    conn.close()
    return stops


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def get_nearby_stops(user_lat, user_lon, limit=10):
    """Get stops near user's location"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all stops with coordinates
    cursor.execute("""
        SELECT stop_id, stop_name, stop_lat, stop_lon
        FROM stops 
        WHERE location_type = 0
          AND stop_lat IS NOT NULL 
          AND stop_lon IS NOT NULL
    """)
    
    stops = []
    for row in cursor.fetchall():
        # Calculate distance from user
        distance = haversine_distance(user_lat, user_lon, row['stop_lat'], row['stop_lon'])
        stops.append({
            'id': row['stop_id'],
            'name': row['stop_name'],
            'lat': row['stop_lat'],
            'lon': row['stop_lon'],
            'distance': round(distance, 2)  # Distance in km
        })
    
    conn.close()
    
    # Sort by distance and return top N
    stops.sort(key=lambda x: x['distance'])
    return stops[:limit]


def find_routes(source_stop_id, dest_stop_id, departure_time=None):
    """Find routes between two stops"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Build query with optional time filter
    time_filter = ""
    if departure_time:
        time_filter = f"AND source.departure_time >= '{departure_time}'"
    
    query = f"""
        SELECT 
            t.trip_id,
            r.route_short_name,
            r.route_long_name,
            r.route_color,
            source.stop_id as source_stop_id,
            s1.stop_name as source_stop_name,
            source.departure_time,
            dest.stop_id as dest_stop_id,
            s2.stop_name as dest_stop_name,
            dest.arrival_time,
            source.stop_sequence as source_sequence,
            dest.stop_sequence as dest_sequence,
            t.trip_headsign,
            CAST((julianday('2024-01-01 ' || dest.arrival_time) - 
                  julianday('2024-01-01 ' || source.departure_time)) * 24 * 60 
                  AS INTEGER) as duration_minutes
        FROM stop_times source
        JOIN stop_times dest 
            ON source.trip_id = dest.trip_id
        JOIN trips t 
            ON source.trip_id = t.trip_id
        JOIN routes r 
            ON t.route_id = r.route_id
        JOIN stops s1 
            ON source.stop_id = s1.stop_id
        JOIN stops s2 
            ON dest.stop_id = s2.stop_id
        WHERE source.stop_id = ?
          AND dest.stop_id = ?
          AND source.stop_sequence < dest.stop_sequence
          {time_filter}
        ORDER BY source.departure_time
        LIMIT 10
    """
    
    cursor.execute(query, (source_stop_id, dest_stop_id))
    results = cursor.fetchall()
    
    routes = []
    for row in results:
        routes.append({
            'trip_id': row['trip_id'],
            'route_number': row['route_short_name'],
            'route_name': row['route_long_name'],
            'route_color': row['route_color'],
            'source_stop': row['source_stop_name'],
            'dest_stop': row['dest_stop_name'],
            'departure_time': row['departure_time'],
            'arrival_time': row['arrival_time'],
            'duration_minutes': row['duration_minutes'],
            'trip_headsign': row['trip_headsign'],
            'stops_count': row['dest_sequence'] - row['source_sequence'] + 1
        })
    
    conn.close()
    return routes


def get_trip_stops(trip_id, start_sequence, end_sequence):
    """Get all stops for a specific trip between start and end sequences"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            st.stop_sequence,
            s.stop_name,
            st.arrival_time,
            st.departure_time
        FROM stop_times st
        JOIN stops s ON st.stop_id = s.stop_id
        WHERE st.trip_id = ?
          AND st.stop_sequence >= ?
          AND st.stop_sequence <= ?
        ORDER BY st.stop_sequence
    """, (trip_id, start_sequence, end_sequence))
    
    stops = []
    for row in cursor.fetchall():
        stops.append({
            'sequence': row['stop_sequence'],
            'name': row['stop_name'],
            'arrival': row['arrival_time'],
            'departure': row['departure_time']
        })
    
    conn.close()
    return stops


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/status')
def status_page():
    """API Status Dashboard"""
    return render_template('status.html')


@app.route('/api/stops')
def api_stops():
    """API endpoint to get all stops"""
    stops = get_all_stops()
    return jsonify(stops)


@app.route('/api/nearby-stops', methods=['GET'])
def api_nearby_stops():
    """API endpoint to get nearby stops based on user location"""
    user_lat = request.args.get('lat', type=float)
    user_lon = request.args.get('lon', type=float)
    limit = request.args.get('limit', 10, type=int)
    
    if user_lat is None or user_lon is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid coordinates'}), 400
    
    nearby_stops = get_nearby_stops(user_lat, user_lon, limit)
    
    return jsonify({
        'stops': nearby_stops,
        'count': len(nearby_stops),
        'user_location': {
            'latitude': user_lat,
            'longitude': user_lon
        }
    })


@app.route('/api/find-route', methods=['POST'])
@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint to search routes"""
    data = request.get_json()
    
    source_stop_id = data.get('source')
    dest_stop_id = data.get('destination')
    use_current_time = data.get('useCurrentTime', False)
    
    if not source_stop_id or not dest_stop_id:
        return jsonify({'error': 'Source and destination required'}), 400
    
    if source_stop_id == dest_stop_id:
        return jsonify({'error': 'Source and destination cannot be the same'}), 400
    
    # Get current time if requested
    departure_time = None
    if use_current_time:
        departure_time = datetime.now().strftime('%H:%M:%S')
    
    routes = find_routes(source_stop_id, dest_stop_id, departure_time)
    
    return jsonify({
        'routes': routes,
        'count': len(routes),
        'current_time': departure_time
    })


@app.route('/api/trip/<trip_id>/<int:start_seq>/<int:end_seq>')
def api_trip_details(trip_id, start_seq, end_seq):
    """API endpoint to get trip details"""
    stops = get_trip_stops(trip_id, start_seq, end_seq)
    return jsonify({'stops': stops})


@app.route('/api/routes')
def api_routes():
    """API endpoint to get all routes"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT route_id, route_short_name, route_long_name, route_color
        FROM routes
        ORDER BY CAST(route_short_name AS INTEGER)
    """)
    
    routes = []
    for row in cursor.fetchall():
        routes.append({
            'id': row['route_id'],
            'number': row['route_short_name'],
            'name': row['route_long_name'],
            'color': row['route_color']
        })
    
    conn.close()
    return jsonify(routes)


@app.route('/api/vehicles')
def api_vehicles():
    """API endpoint to get all vehicle positions"""
    route_id = request.args.get('route_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            vp.*,
            r.route_short_name,
            r.route_long_name,
            r.route_color,
            s.stop_name as current_stop_name,
            t.trip_headsign
        FROM vehicle_positions vp
        LEFT JOIN routes r ON vp.route_id = r.route_id
        LEFT JOIN stops s ON vp.current_stop_id = s.stop_id
        LEFT JOIN trips t ON vp.trip_id = t.trip_id
    """
    
    params = []
    if route_id:
        query += " WHERE vp.route_id = ?"
        params.append(route_id)
    
    query += " ORDER BY vp.route_id, vp.vehicle_id"
    
    cursor.execute(query, params)
    
    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            'vehicle_id': row['vehicle_id'],
            'trip_id': row['trip_id'],
            'route_id': row['route_id'],
            'route_number': row['route_short_name'],
            'route_name': row['route_long_name'],
            'route_color': row['route_color'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'bearing': row['bearing'],
            'speed': row['speed'],
            'current_stop': row['current_stop_name'],
            'headsign': row['trip_headsign'],
            'occupancy': row['occupancy_status'],
            'timestamp': row['timestamp']
        })
    
    conn.close()
    return jsonify({'vehicles': vehicles, 'count': len(vehicles)})


@app.route('/api/alerts')
def api_alerts():
    """API endpoint to get service alerts"""
    route_id = request.args.get('route_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if route_id:
        cursor.execute("""
            SELECT DISTINCT a.*
            FROM alerts a
            JOIN alert_affected_entities aae ON a.alert_id = aae.alert_id
            WHERE aae.route_id = ?
            ORDER BY a.timestamp DESC
        """, (route_id,))
    else:
        cursor.execute("""
            SELECT * FROM alerts
            ORDER BY timestamp DESC
            LIMIT 20
        """)
    
    alerts = []
    for row in cursor.fetchall():
        alerts.append({
            'id': row['alert_id'],
            'cause': row['cause'],
            'effect': row['effect'],
            'header': row['header_text'],
            'description': row['description_text'],
            'url': row['url'],
            'timestamp': row['timestamp']
        })
    
    conn.close()
    return jsonify({'alerts': alerts, 'count': len(alerts)})


@app.route('/api/refresh-realtime', methods=['GET', 'POST'])
def api_refresh_realtime():
    """
    Force refresh of real-time data from MiWay servers
    Downloads fresh VehiclePositions, TripUpdates, and Alerts
    """
    global last_update_time
    
    with update_lock:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Manual refresh triggered...")
            results = update_all_realtime_data()
            
            if results['success']:
                last_update_time = datetime.now()
                return jsonify({
                    'success': True,
                    'message': 'Real-time data updated successfully',
                    'timestamp': results['timestamp'],
                    'vehicles': results['vehicles'],
                    'trip_updates': results['trip_updates'],
                    'alerts': results['alerts'],
                    'errors': results['errors'] if results['errors'] else None,
                    'error_details': results.get('error_details', None)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Update failed',
                    'errors': results['errors'],
                    'error_details': results.get('error_details', [])
                }), 500
        
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500


@app.route('/api/data-freshness')
def api_data_freshness():
    """Get information about when data was last updated"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get newest vehicle position timestamp
    cursor.execute("SELECT MAX(timestamp) as latest FROM vehicle_positions")
    vehicle_ts = cursor.fetchone()['latest']
    
    # Get newest trip update timestamp
    cursor.execute("SELECT MAX(timestamp) as latest FROM trip_updates")
    trip_ts = cursor.fetchone()['latest']
    
    # Get newest alert timestamp
    cursor.execute("SELECT MAX(timestamp) as latest FROM alerts")
    alert_ts = cursor.fetchone()['latest']
    
    conn.close()
    
    # Convert timestamps to datetime
    data_age_seconds = None
    if vehicle_ts:
        data_age_seconds = int(datetime.now().timestamp()) - vehicle_ts
    
    return jsonify({
        'last_update': last_update_time.isoformat() if last_update_time else None,
        'vehicle_timestamp': vehicle_ts,
        'trip_update_timestamp': trip_ts,
        'alert_timestamp': alert_ts,
        'data_age_seconds': data_age_seconds,
        'is_stale': data_age_seconds > 300 if data_age_seconds else True  # Stale if > 5 minutes
    })


@app.route('/api/health-history')
def api_health_history():
    """Get health check history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        endpoint = request.args.get('endpoint', None)
        
        conn = get_db()
        cursor = conn.cursor()
        
        if endpoint:
            cursor.execute("""
                SELECT * FROM health_checks 
                WHERE endpoint_name = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (endpoint, limit))
        else:
            cursor.execute("""
                SELECT * FROM health_checks 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health-summary')
def api_health_summary():
    """Get health check summary statistics"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get latest check for each endpoint
        cursor.execute("""
            WITH latest_checks AS (
                SELECT endpoint_name, MAX(timestamp) as latest_time
                FROM health_checks
                GROUP BY endpoint_name
            )
            SELECT h.*
            FROM health_checks h
            INNER JOIN latest_checks l 
                ON h.endpoint_name = l.endpoint_name 
                AND h.timestamp = l.latest_time
            ORDER BY h.endpoint_name
        """)
        
        columns = [description[0] for description in cursor.description]
        latest = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get statistics for last 24 hours
        cursor.execute("""
            SELECT 
                endpoint_name,
                COUNT(*) as total_checks,
                SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
                SUM(CASE WHEN rate_limited = 1 THEN 1 ELSE 0 END) as rate_limited_count,
                AVG(CASE WHEN response_time IS NOT NULL THEN response_time ELSE 0 END) as avg_response_time,
                MIN(timestamp) as first_check,
                MAX(timestamp) as last_check
            FROM health_checks
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
            GROUP BY endpoint_name
        """)
        
        columns = [description[0] for description in cursor.description]
        stats = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'latest': latest,
            'stats_24h': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nearby-buses', methods=['GET'])
def api_nearby_buses():
    """Find buses near user's location"""
    user_lat = request.args.get('lat', type=float)
    user_lon = request.args.get('lon', type=float)
    radius_km = request.args.get('radius', 0.5, type=float)  # Default 500m radius
    limit = request.args.get('limit', 10, type=int)
    
    if user_lat is None or user_lon is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    # Get nearby stops
    nearby_stops = get_nearby_stops(user_lat, user_lon, limit=10)
    
    if not nearby_stops:
        return jsonify({
            'buses': [],
            'nearby_stops': [],
            'message': 'No stops found nearby'
        })
    
    # Get nearby stops within radius
    nearby_stops = [s for s in nearby_stops if s['distance'] <= radius_km]
    
    if not nearby_stops:
        return jsonify({
            'buses': [],
            'nearby_stops': [],
            'message': f'No stops within {radius_km} km'
        })
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all vehicles
    cursor.execute("""
        SELECT 
            vp.*,
            r.route_short_name,
            r.route_long_name,
            r.route_color,
            t.trip_headsign
        FROM vehicle_positions vp
        LEFT JOIN routes r ON vp.route_id = r.route_id
        LEFT JOIN trips t ON vp.trip_id = t.trip_id
    """)
    
    vehicles = cursor.fetchall()
    
    # Find buses heading towards nearby stops
    nearby_buses = []
    
    for vehicle in vehicles:
        if not vehicle['trip_id'] or not vehicle['latitude']:
            continue
        
        # Get the route for this vehicle
        cursor.execute("""
            SELECT st.stop_id, st.stop_sequence, s.stop_name, s.stop_lat, s.stop_lon
            FROM stop_times st
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE st.trip_id = ?
            AND st.stop_sequence >= ?
            ORDER BY st.stop_sequence
            LIMIT 20
        """, (vehicle['trip_id'], vehicle['current_stop_sequence'] or 0))
        
        upcoming_stops = cursor.fetchall()
        
        # Check if any upcoming stops match our nearby stops
        for stop in upcoming_stops:
            for nearby in nearby_stops:
                if stop['stop_id'] == nearby['id']:
                    # Calculate distance from vehicle to stop
                    bus_to_stop_dist = haversine_distance(
                        vehicle['latitude'], vehicle['longitude'],
                        stop['stop_lat'], stop['stop_lon']
                    )
                    
                    # Rough ETA calculation (assuming average speed)
                    avg_speed_kmh = 25  # Average bus speed
                    eta_minutes = int((bus_to_stop_dist / avg_speed_kmh) * 60)
                    
                    if eta_minutes <= 30:  # Only show buses within 30 min
                        nearby_buses.append({
                            'vehicle_id': vehicle['vehicle_id'],
                            'route_number': vehicle['route_short_name'],
                            'route_name': vehicle['route_long_name'],
                            'route_color': vehicle['route_color'],
                            'headsign': vehicle['trip_headsign'],
                            'stop_id': stop['stop_id'],
                            'stop_name': stop['stop_name'],
                            'stop_distance_from_user': nearby['distance'],
                            'bus_distance_from_stop': round(bus_to_stop_dist, 2),
                            'eta_minutes': eta_minutes,
                            'vehicle_lat': vehicle['latitude'],
                            'vehicle_lon': vehicle['longitude'],
                            'occupancy': vehicle['occupancy_status']
                        })
                    break
    
    conn.close()
    
    # Sort by ETA
    nearby_buses.sort(key=lambda x: x['eta_minutes'])
    
    return jsonify({
        'buses': nearby_buses[:10],  # Top 10 soonest
        'nearby_stops': nearby_stops,
        'count': len(nearby_buses[:10]),
        'user_location': {
            'latitude': user_lat,
            'longitude': user_lon
        }
    })


def background_update_worker():
    """
    Background worker that fetches fresh real-time data every 30 seconds
    """
    global last_update_time, worker_running
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Background worker started (updates every 30 seconds)")
    
    while worker_running:
        try:
            with update_lock:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Background update starting...")
                results = update_all_realtime_data()
                
                if results['success']:
                    last_update_time = datetime.now()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Background update complete")
                    print(f"   Vehicles: {results['vehicles']}, Trips: {results['trip_updates']}, Alerts: {results['alerts']}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Background update had errors: {results['errors']}")
        
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Background update error: {e}")
        
        # Wait 30 seconds before next update
        time.sleep(30)


def start_background_worker():
    """Start the background update worker"""
    global background_worker, worker_running
    
    worker_running = True
    background_worker = threading.Thread(target=background_update_worker, daemon=True)
    background_worker.start()


def stop_background_worker():
    """Stop the background update worker"""
    global worker_running
    worker_running = False
    if background_worker:
        background_worker.join(timeout=5)


if __name__ == '__main__':
    import os
    import atexit
    
    # Check if database exists
    if not os.path.exists(DB_FILE):
        print("=" * 80)
        print("❌ ERROR: Database not found!")
        print("=" * 80)
        print()
        print("Please run the data loader first:")
        print("  python load_gtfs.py")
        print()
        exit(1)
    
    print("=" * 80)
    print("🚌 MiWay Route Planner with Live Updates")
    print("=" * 80)
    print()
    print("🌐 Starting server at http://localhost:5001")
    print("   Press Ctrl+C to stop")
    print()
    
    # Initial data update
    print("📥 Performing initial real-time data update...")
    initial_results = update_all_realtime_data()
    if initial_results['success']:
        last_update_time = datetime.now()
        print(f"✅ Initial update complete: {initial_results['vehicles']} vehicles loaded")
    else:
        print(f"⚠️  Initial update had errors: {initial_results['errors']}")
    print()
    
    # Start background worker
    start_background_worker()
    
    # Register cleanup function
    atexit.register(stop_background_worker)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5001, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping server...")
        stop_background_worker()
        print("✅ Server stopped")

