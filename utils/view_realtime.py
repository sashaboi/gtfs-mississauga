"""
View GTFS-Realtime Data
Shows alerts, vehicle positions, and trip updates
"""

import sqlite3
from datetime import datetime

DB_FILE = 'miway.db'

def view_alerts():
    """Display current service alerts"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🚨 SERVICE ALERTS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT * FROM alerts 
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    alerts = cursor.fetchall()
    
    if not alerts:
        print("No active alerts\n")
        return
    
    for alert in alerts:
        print(f"\n📢 Alert ID: {alert['alert_id']}")
        print(f"   Cause:  {alert['cause']}")
        print(f"   Effect: {alert['effect']}")
        print(f"   Header: {alert['header_text']}")
        if alert['description_text']:
            print(f"   Description: {alert['description_text'][:100]}...")
        
        # Get affected entities
        cursor.execute("""
            SELECT * FROM alert_affected_entities 
            WHERE alert_id = ?
        """, (alert['alert_id'],))
        
        entities = cursor.fetchall()
        if entities:
            print(f"   Affects:")
            for entity in entities[:3]:  # Show first 3
                if entity['route_id']:
                    print(f"      - Route {entity['route_id']}")
                elif entity['stop_id']:
                    cursor.execute("SELECT stop_name FROM stops WHERE stop_id = ?", (entity['stop_id'],))
                    stop = cursor.fetchone()
                    print(f"      - Stop: {stop['stop_name'] if stop else entity['stop_id']}")
    
    print()
    conn.close()


def view_vehicle_positions():
    """Display current vehicle positions"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🚍 LIVE VEHICLE POSITIONS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            vp.*,
            r.route_short_name,
            r.route_long_name,
            s.stop_name as current_stop_name
        FROM vehicle_positions vp
        LEFT JOIN routes r ON vp.route_id = r.route_id
        LEFT JOIN stops s ON vp.current_stop_id = s.stop_id
        ORDER BY vp.route_id, vp.vehicle_id
        LIMIT 10
    """)
    
    vehicles = cursor.fetchall()
    
    if not vehicles:
        print("No vehicle positions available\n")
        return
    
    print(f"\nShowing {len(vehicles)} vehicles (of {cursor.execute('SELECT COUNT(*) FROM vehicle_positions').fetchone()[0]} total):\n")
    
    for vehicle in vehicles:
        print(f"🚌 Vehicle {vehicle['vehicle_id']}")
        print(f"   Route: {vehicle['route_short_name']} - {vehicle['route_long_name']}")
        print(f"   Location: {vehicle['latitude']:.5f}, {vehicle['longitude']:.5f}")
        if vehicle['speed']:
            print(f"   Speed: {vehicle['speed']:.1f} m/s ({vehicle['speed'] * 3.6:.1f} km/h)")
        if vehicle['bearing']:
            print(f"   Bearing: {vehicle['bearing']:.1f}°")
        if vehicle['current_stop_name']:
            print(f"   At Stop: {vehicle['current_stop_name']}")
        if vehicle['occupancy_status']:
            print(f"   Occupancy: {vehicle['occupancy_status']}")
        print()
    
    conn.close()


def view_trip_updates():
    """Display trip updates with delays"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("⏰ TRIP UPDATES & DELAYS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            tu.*,
            r.route_short_name,
            r.route_long_name
        FROM trip_updates tu
        LEFT JOIN routes r ON tu.route_id = r.route_id
        ORDER BY tu.timestamp DESC
        LIMIT 10
    """)
    
    updates = cursor.fetchall()
    
    if not updates:
        print("No trip updates available\n")
        return
    
    print(f"\nShowing {len(updates)} trips (of {cursor.execute('SELECT COUNT(*) FROM trip_updates').fetchone()[0]} total):\n")
    
    for update in updates:
        print(f"🚌 Route {update['route_short_name']} - {update['route_long_name']}")
        print(f"   Trip ID: {update['trip_id']}")
        print(f"   Schedule: {update['schedule_relationship']}")
        
        # Get stop time updates with delays
        cursor.execute("""
            SELECT 
                stu.*,
                s.stop_name
            FROM stop_time_updates stu
            LEFT JOIN stops s ON stu.stop_id = s.stop_id
            WHERE stu.trip_update_id = ?
            AND (stu.arrival_delay IS NOT NULL OR stu.departure_delay IS NOT NULL)
            ORDER BY stu.stop_sequence
            LIMIT 5
        """, (update['id'],))
        
        delays = cursor.fetchall()
        if delays:
            print(f"   Delays:")
            for delay in delays:
                if delay['arrival_delay'] or delay['departure_delay']:
                    delay_min = (delay['arrival_delay'] or delay['departure_delay']) // 60
                    status = "early" if delay_min < 0 else "late"
                    print(f"      {delay['stop_name']}: {abs(delay_min)} min {status}")
        print()
    
    conn.close()


def main():
    """Display all real-time data"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "GTFS-Realtime Data Viewer" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    try:
        view_alerts()
        view_vehicle_positions()
        view_trip_updates()
        
        print("=" * 80)
        print("✅ Real-time data displayed successfully!")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

