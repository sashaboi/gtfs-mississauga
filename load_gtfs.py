"""
Load GTFS data from CSV files into SQLite database
"""

import sqlite3
import csv
import os
from pathlib import Path

# Database file
DB_FILE = 'miway.db'
GTFS_DIR = 'google_transit'

def create_schema(conn):
    """Create database schema"""
    print("Creating database schema...")
    
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS stop_times")
    cursor.execute("DROP TABLE IF EXISTS trips")
    cursor.execute("DROP TABLE IF EXISTS routes")
    cursor.execute("DROP TABLE IF EXISTS stops")
    cursor.execute("DROP TABLE IF EXISTS calendar_dates")
    cursor.execute("DROP TABLE IF EXISTS agency")
    
    # Stops table
    cursor.execute("""
        CREATE TABLE stops (
            stop_id TEXT PRIMARY KEY,
            stop_code TEXT,
            stop_name TEXT NOT NULL,
            stop_lat REAL,
            stop_lon REAL,
            location_type INTEGER,
            parent_station TEXT,
            wheelchair_boarding INTEGER
        )
    """)
    
    # Routes table
    cursor.execute("""
        CREATE TABLE routes (
            route_id TEXT PRIMARY KEY,
            agency_id TEXT,
            route_short_name TEXT,
            route_long_name TEXT,
            route_type INTEGER,
            route_color TEXT,
            route_text_color TEXT
        )
    """)
    
    # Trips table
    cursor.execute("""
        CREATE TABLE trips (
            trip_id TEXT PRIMARY KEY,
            route_id TEXT NOT NULL,
            service_id TEXT,
            trip_headsign TEXT,
            direction_id INTEGER,
            block_id TEXT,
            shape_id TEXT,
            wheelchair_accessible INTEGER,
            FOREIGN KEY (route_id) REFERENCES routes(route_id)
        )
    """)
    
    # Stop Times table
    cursor.execute("""
        CREATE TABLE stop_times (
            trip_id TEXT NOT NULL,
            arrival_time TEXT,
            departure_time TEXT,
            stop_id TEXT NOT NULL,
            stop_sequence INTEGER NOT NULL,
            pickup_type INTEGER,
            drop_off_type INTEGER,
            timepoint INTEGER,
            PRIMARY KEY (trip_id, stop_sequence),
            FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
            FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
        )
    """)
    
    # Create indexes
    print("Creating indexes...")
    cursor.execute("CREATE INDEX idx_stop_times_trip ON stop_times(trip_id)")
    cursor.execute("CREATE INDEX idx_stop_times_stop ON stop_times(stop_id)")
    cursor.execute("CREATE INDEX idx_trips_route ON trips(route_id)")
    cursor.execute("CREATE INDEX idx_stops_name ON stops(stop_name)")
    
    conn.commit()
    print("✅ Schema created\n")


def load_stops(conn):
    """Load stops.txt"""
    print("Loading stops.txt...")
    cursor = conn.cursor()
    
    with open(f'{GTFS_DIR}/stops.txt', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        batch = []
        
        for row in reader:
            batch.append((
                row['stop_id'],
                row.get('stop_code', ''),
                row['stop_name'],
                float(row['stop_lat']) if row.get('stop_lat') else None,
                float(row['stop_lon']) if row.get('stop_lon') else None,
                int(row.get('location_type', 0)),
                row.get('parent_station', ''),
                int(row.get('wheelchair_boarding', 0))
            ))
            count += 1
            
            # Insert in batches of 1000
            if len(batch) >= 1000:
                cursor.executemany(
                    'INSERT INTO stops VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    batch
                )
                batch = []
        
        # Insert remaining
        if batch:
            cursor.executemany(
                'INSERT INTO stops VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                batch
            )
    
    conn.commit()
    print(f"✅ Loaded {count} stops\n")


def load_routes(conn):
    """Load routes.txt"""
    print("Loading routes.txt...")
    cursor = conn.cursor()
    
    with open(f'{GTFS_DIR}/routes.txt', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        
        for row in reader:
            cursor.execute(
                'INSERT INTO routes VALUES (?, ?, ?, ?, ?, ?, ?)',
                (
                    row['route_id'],
                    row.get('agency_id', ''),
                    row.get('route_short_name', ''),
                    row.get('route_long_name', ''),
                    int(row.get('route_type', 3)),
                    row.get('route_color', ''),
                    row.get('route_text_color', '')
                )
            )
            count += 1
    
    conn.commit()
    print(f"✅ Loaded {count} routes\n")


def load_trips(conn):
    """Load trips.txt"""
    print("Loading trips.txt (this may take a moment)...")
    cursor = conn.cursor()
    
    with open(f'{GTFS_DIR}/trips.txt', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        batch = []
        
        for row in reader:
            batch.append((
                row['trip_id'],
                row['route_id'],
                row.get('service_id', ''),
                row.get('trip_headsign', ''),
                int(row.get('direction_id', 0)),
                row.get('block_id', ''),
                row.get('shape_id', ''),
                int(row.get('wheelchair_accessible', 0))
            ))
            count += 1
            
            if len(batch) >= 5000:
                cursor.executemany(
                    'INSERT INTO trips VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    batch
                )
                batch = []
        
        if batch:
            cursor.executemany(
                'INSERT INTO trips VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                batch
            )
    
    conn.commit()
    print(f"✅ Loaded {count} trips\n")


def load_stop_times(conn):
    """Load stop_times.txt"""
    print("Loading stop_times.txt (this will take a few moments - 960K+ rows)...")
    cursor = conn.cursor()
    
    with open(f'{GTFS_DIR}/stop_times.txt', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        batch = []
        
        for row in reader:
            batch.append((
                row['trip_id'],
                row.get('arrival_time', ''),
                row.get('departure_time', ''),
                row['stop_id'],
                int(row['stop_sequence']),
                int(row.get('pickup_type', 0)),
                int(row.get('drop_off_type', 0)),
                int(row.get('timepoint', 0))
            ))
            count += 1
            
            # Insert in batches of 10000 for speed
            if len(batch) >= 10000:
                cursor.executemany(
                    'INSERT INTO stop_times VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    batch
                )
                batch = []
                if count % 100000 == 0:
                    print(f"   Processed {count:,} rows...")
        
        if batch:
            cursor.executemany(
                'INSERT INTO stop_times VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                batch
            )
    
    conn.commit()
    print(f"✅ Loaded {count:,} stop times\n")


def main():
    """Main function to load all GTFS data"""
    print("=" * 80)
    print("MiWay GTFS Data Loader")
    print("=" * 80)
    print()
    
    # Check if GTFS directory exists
    if not os.path.exists(GTFS_DIR):
        print(f"❌ Error: {GTFS_DIR} directory not found!")
        return
    
    # Remove old database if exists
    if os.path.exists(DB_FILE):
        print(f"Removing old database: {DB_FILE}")
        os.remove(DB_FILE)
        print()
    
    # Connect to database
    conn = sqlite3.connect(DB_FILE)
    
    try:
        # Create schema
        create_schema(conn)
        
        # Load data
        load_stops(conn)
        load_routes(conn)
        load_trips(conn)
        load_stop_times(conn)
        
        # Verify data
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stops")
        stops_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM routes")
        routes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trips")
        trips_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stop_times")
        stop_times_count = cursor.fetchone()[0]
        
        print("=" * 80)
        print("✅ DATABASE LOADED SUCCESSFULLY!")
        print("=" * 80)
        print(f"📊 Summary:")
        print(f"   - Stops:       {stops_count:,}")
        print(f"   - Routes:      {routes_count:,}")
        print(f"   - Trips:       {trips_count:,}")
        print(f"   - Stop Times:  {stop_times_count:,}")
        print()
        print(f"💾 Database: {DB_FILE}")
        print()
        print("🚀 Ready to run the app! Run: python app.py")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()

