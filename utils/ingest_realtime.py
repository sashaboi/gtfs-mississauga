"""
GTFS-Realtime Data Ingestion for MiWay
Processes .pb (Protocol Buffer) files for real-time transit data
"""

import sqlite3
from google.transit import gtfs_realtime_pb2
from datetime import datetime
import os

DB_FILE = 'miway.db'

# GTFS-Realtime file paths
ALERTS_FILE = 'Alerts.pb'
TRIP_UPDATES_FILE = 'TripUpdates.pb'
VEHICLE_POSITIONS_FILE = 'VehiclePositions.pb'


def create_realtime_tables(conn):
    """Create tables for storing real-time data"""
    cursor = conn.cursor()
    
    print("Creating real-time data tables...")
    
    # Service Alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            cause TEXT,
            effect TEXT,
            header_text TEXT,
            description_text TEXT,
            url TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Affected entities for alerts (which routes/stops/trips are affected)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_affected_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT,
            entity_type TEXT,
            route_id TEXT,
            trip_id TEXT,
            stop_id TEXT,
            FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
        )
    """)
    
    # Trip Updates table (real-time arrival/departure predictions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trip_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id TEXT,
            route_id TEXT,
            start_date TEXT,
            start_time TEXT,
            schedule_relationship TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
        )
    """)
    
    # Stop Time Updates (predictions for specific stops)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stop_time_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_update_id INTEGER,
            stop_sequence INTEGER,
            stop_id TEXT,
            arrival_delay INTEGER,
            arrival_time INTEGER,
            departure_delay INTEGER,
            departure_time INTEGER,
            schedule_relationship TEXT,
            FOREIGN KEY (trip_update_id) REFERENCES trip_updates(id),
            FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
        )
    """)
    
    # Vehicle Positions table (live bus locations)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_positions (
            vehicle_id TEXT PRIMARY KEY,
            trip_id TEXT,
            route_id TEXT,
            latitude REAL,
            longitude REAL,
            bearing REAL,
            speed REAL,
            current_stop_sequence INTEGER,
            current_stop_id TEXT,
            congestion_level TEXT,
            occupancy_status TEXT,
            timestamp INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
            FOREIGN KEY (current_stop_id) REFERENCES stops(stop_id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trip_updates_trip ON trip_updates(trip_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trip_updates_route ON trip_updates(route_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_positions_trip ON vehicle_positions(trip_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_positions_route ON vehicle_positions(route_id)")
    
    conn.commit()
    print("✅ Real-time tables created\n")


def parse_alerts(file_path):
    """Parse Alerts.pb file"""
    if not os.path.exists(file_path):
        print(f"⚠️  Alerts file not found: {file_path}")
        return []
    
    print(f"Parsing {file_path}...")
    
    with open(file_path, 'rb') as f:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(f.read())
    
    alerts = []
    for entity in feed.entity:
        if entity.HasField('alert'):
            alert = entity.alert
            
            # Get cause and effect
            cause = gtfs_realtime_pb2.Alert.Cause.Name(alert.cause) if alert.HasField('cause') else None
            effect = gtfs_realtime_pb2.Alert.Effect.Name(alert.effect) if alert.HasField('effect') else None
            
            # Get header text (in English if available)
            header_text = ""
            if alert.header_text.translation:
                header_text = alert.header_text.translation[0].text
            
            # Get description text
            description_text = ""
            if alert.description_text.translation:
                description_text = alert.description_text.translation[0].text
            
            # Get URL
            url = ""
            if alert.url.translation:
                url = alert.url.translation[0].text
            
            alert_data = {
                'alert_id': entity.id,
                'cause': cause,
                'effect': effect,
                'header_text': header_text,
                'description_text': description_text,
                'url': url,
                'timestamp': feed.header.timestamp,
                'affected_entities': []
            }
            
            # Parse affected entities
            for informed_entity in alert.informed_entity:
                affected = {
                    'route_id': informed_entity.route_id if informed_entity.HasField('route_id') else None,
                    'trip_id': informed_entity.trip.trip_id if informed_entity.HasField('trip') else None,
                    'stop_id': informed_entity.stop_id if informed_entity.HasField('stop_id') else None
                }
                alert_data['affected_entities'].append(affected)
            
            alerts.append(alert_data)
    
    print(f"✅ Parsed {len(alerts)} alerts\n")
    return alerts


def parse_trip_updates(file_path):
    """Parse TripUpdates.pb file"""
    if not os.path.exists(file_path):
        print(f"⚠️  Trip updates file not found: {file_path}")
        return []
    
    print(f"Parsing {file_path}...")
    
    with open(file_path, 'rb') as f:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(f.read())
    
    trip_updates = []
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_update = entity.trip_update
            trip = trip_update.trip
            
            schedule_rel = gtfs_realtime_pb2.TripDescriptor.ScheduleRelationship.Name(
                trip.schedule_relationship
            ) if trip.HasField('schedule_relationship') else 'SCHEDULED'
            
            update_data = {
                'trip_id': trip.trip_id if trip.HasField('trip_id') else None,
                'route_id': trip.route_id if trip.HasField('route_id') else None,
                'start_date': trip.start_date if trip.HasField('start_date') else None,
                'start_time': trip.start_time if trip.HasField('start_time') else None,
                'schedule_relationship': schedule_rel,
                'timestamp': trip_update.timestamp if trip_update.HasField('timestamp') else feed.header.timestamp,
                'stop_time_updates': []
            }
            
            # Parse stop time updates
            for stu in trip_update.stop_time_update:
                stop_update = {
                    'stop_sequence': stu.stop_sequence if stu.HasField('stop_sequence') else None,
                    'stop_id': stu.stop_id if stu.HasField('stop_id') else None,
                    'arrival_delay': stu.arrival.delay if stu.HasField('arrival') and stu.arrival.HasField('delay') else None,
                    'arrival_time': stu.arrival.time if stu.HasField('arrival') and stu.arrival.HasField('time') else None,
                    'departure_delay': stu.departure.delay if stu.HasField('departure') and stu.departure.HasField('delay') else None,
                    'departure_time': stu.departure.time if stu.HasField('departure') and stu.departure.HasField('time') else None,
                    'schedule_relationship': gtfs_realtime_pb2.TripUpdate.StopTimeUpdate.ScheduleRelationship.Name(
                        stu.schedule_relationship
                    ) if stu.HasField('schedule_relationship') else 'SCHEDULED'
                }
                update_data['stop_time_updates'].append(stop_update)
            
            trip_updates.append(update_data)
    
    print(f"✅ Parsed {len(trip_updates)} trip updates\n")
    return trip_updates


def parse_vehicle_positions(file_path):
    """Parse VehiclePositions.pb file"""
    if not os.path.exists(file_path):
        print(f"⚠️  Vehicle positions file not found: {file_path}")
        return []
    
    print(f"Parsing {file_path}...")
    
    with open(file_path, 'rb') as f:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(f.read())
    
    vehicles = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = entity.vehicle
            
            congestion = None
            if vehicle.HasField('congestion_level'):
                congestion = gtfs_realtime_pb2.VehiclePosition.CongestionLevel.Name(vehicle.congestion_level)
            
            occupancy = None
            if vehicle.HasField('occupancy_status'):
                occupancy = gtfs_realtime_pb2.VehiclePosition.OccupancyStatus.Name(vehicle.occupancy_status)
            
            vehicle_data = {
                'vehicle_id': vehicle.vehicle.id if vehicle.HasField('vehicle') and vehicle.vehicle.HasField('id') else entity.id,
                'trip_id': vehicle.trip.trip_id if vehicle.HasField('trip') and vehicle.trip.HasField('trip_id') else None,
                'route_id': vehicle.trip.route_id if vehicle.HasField('trip') and vehicle.trip.HasField('route_id') else None,
                'latitude': vehicle.position.latitude if vehicle.HasField('position') else None,
                'longitude': vehicle.position.longitude if vehicle.HasField('position') else None,
                'bearing': vehicle.position.bearing if vehicle.HasField('position') and vehicle.position.HasField('bearing') else None,
                'speed': vehicle.position.speed if vehicle.HasField('position') and vehicle.position.HasField('speed') else None,
                'current_stop_sequence': vehicle.current_stop_sequence if vehicle.HasField('current_stop_sequence') else None,
                'current_stop_id': vehicle.stop_id if vehicle.HasField('stop_id') else None,
                'congestion_level': congestion,
                'occupancy_status': occupancy,
                'timestamp': vehicle.timestamp if vehicle.HasField('timestamp') else feed.header.timestamp
            }
            
            vehicles.append(vehicle_data)
    
    print(f"✅ Parsed {len(vehicles)} vehicle positions\n")
    return vehicles


def load_alerts_to_db(conn, alerts):
    """Load parsed alerts into database"""
    cursor = conn.cursor()
    
    # Clear old alerts
    cursor.execute("DELETE FROM alert_affected_entities")
    cursor.execute("DELETE FROM alerts")
    
    for alert in alerts:
        cursor.execute("""
            INSERT OR REPLACE INTO alerts 
            (alert_id, cause, effect, header_text, description_text, url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            alert['alert_id'],
            alert['cause'],
            alert['effect'],
            alert['header_text'],
            alert['description_text'],
            alert['url'],
            alert['timestamp']
        ))
        
        # Insert affected entities
        for entity in alert['affected_entities']:
            entity_type = 'route' if entity['route_id'] else 'trip' if entity['trip_id'] else 'stop'
            cursor.execute("""
                INSERT INTO alert_affected_entities 
                (alert_id, entity_type, route_id, trip_id, stop_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                alert['alert_id'],
                entity_type,
                entity['route_id'],
                entity['trip_id'],
                entity['stop_id']
            ))
    
    conn.commit()
    print(f"✅ Loaded {len(alerts)} alerts to database\n")


def load_trip_updates_to_db(conn, trip_updates):
    """Load parsed trip updates into database"""
    cursor = conn.cursor()
    
    # Clear old updates (keep last hour for reference)
    one_hour_ago = int(datetime.now().timestamp()) - 3600
    cursor.execute("DELETE FROM stop_time_updates WHERE trip_update_id IN (SELECT id FROM trip_updates WHERE timestamp < ?)", (one_hour_ago,))
    cursor.execute("DELETE FROM trip_updates WHERE timestamp < ?", (one_hour_ago,))
    
    for update in trip_updates:
        cursor.execute("""
            INSERT INTO trip_updates 
            (trip_id, route_id, start_date, start_time, schedule_relationship, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            update['trip_id'],
            update['route_id'],
            update['start_date'],
            update['start_time'],
            update['schedule_relationship'],
            update['timestamp']
        ))
        
        trip_update_id = cursor.lastrowid
        
        # Insert stop time updates
        for stu in update['stop_time_updates']:
            cursor.execute("""
                INSERT INTO stop_time_updates 
                (trip_update_id, stop_sequence, stop_id, arrival_delay, arrival_time, 
                 departure_delay, departure_time, schedule_relationship)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip_update_id,
                stu['stop_sequence'],
                stu['stop_id'],
                stu['arrival_delay'],
                stu['arrival_time'],
                stu['departure_delay'],
                stu['departure_time'],
                stu['schedule_relationship']
            ))
    
    conn.commit()
    print(f"✅ Loaded {len(trip_updates)} trip updates to database\n")


def load_vehicle_positions_to_db(conn, vehicles):
    """Load parsed vehicle positions into database"""
    cursor = conn.cursor()
    
    for vehicle in vehicles:
        cursor.execute("""
            INSERT OR REPLACE INTO vehicle_positions 
            (vehicle_id, trip_id, route_id, latitude, longitude, bearing, speed,
             current_stop_sequence, current_stop_id, congestion_level, occupancy_status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vehicle['vehicle_id'],
            vehicle['trip_id'],
            vehicle['route_id'],
            vehicle['latitude'],
            vehicle['longitude'],
            vehicle['bearing'],
            vehicle['speed'],
            vehicle['current_stop_sequence'],
            vehicle['current_stop_id'],
            vehicle['congestion_level'],
            vehicle['occupancy_status'],
            vehicle['timestamp']
        ))
    
    conn.commit()
    print(f"✅ Loaded {len(vehicles)} vehicle positions to database\n")


def main():
    """Main function to ingest all GTFS-Realtime data"""
    print("=" * 80)
    print("GTFS-Realtime Data Ingestion")
    print("=" * 80)
    print()
    
    # Check if database exists
    if not os.path.exists(DB_FILE):
        print(f"❌ Error: Database not found: {DB_FILE}")
        print("Please run load_gtfs.py first!")
        return
    
    # Connect to database
    conn = sqlite3.connect(DB_FILE)
    
    try:
        # Create real-time tables
        create_realtime_tables(conn)
        
        # Parse and load alerts
        alerts = parse_alerts(ALERTS_FILE)
        if alerts:
            load_alerts_to_db(conn, alerts)
        
        # Parse and load trip updates
        trip_updates = parse_trip_updates(TRIP_UPDATES_FILE)
        if trip_updates:
            load_trip_updates_to_db(conn, trip_updates)
        
        # Parse and load vehicle positions
        vehicles = parse_vehicle_positions(VEHICLE_POSITIONS_FILE)
        if vehicles:
            load_vehicle_positions_to_db(conn, vehicles)
        
        # Summary
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alert_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trip_updates")
        trip_update_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vehicle_positions")
        vehicle_count = cursor.fetchone()[0]
        
        print("=" * 80)
        print("✅ REAL-TIME DATA LOADED SUCCESSFULLY!")
        print("=" * 80)
        print(f"📊 Summary:")
        print(f"   - Service Alerts:    {alert_count}")
        print(f"   - Trip Updates:      {trip_update_count}")
        print(f"   - Vehicle Positions: {vehicle_count}")
        print()
        print(f"💾 Database: {DB_FILE}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()

