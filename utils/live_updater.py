"""
Live GTFS-Realtime Data Updater
Fetches fresh data from MiWay servers and updates database
"""

import requests
import sqlite3
from google.transit import gtfs_realtime_pb2
from datetime import datetime
import os
import time

DB_FILE = 'miway.db'

# MiWay Real-Time URLs
URLS = {
    'vehicle_positions': 'https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb',
    'trip_updates': 'https://www.miapp.ca/GTFS_RT/TripUpdate/TripUpdates.pb',
    'alerts': 'https://www.miapp.ca/gtfs_rt/Alerts/Alerts.pb'
}


def download_pb_file(url, timeout=10):
    """
    Download a Protocol Buffer file from URL
    Returns tuple: (data, error_dict, response_time, status_code, content_length)
    """
    error_info = None
    start_time = time.time()
    
    # Add browser-like headers to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response_time = time.time() - start_time
        
        # Log response details
        print(f"  Status: {response.status_code}, Size: {len(response.content)} bytes")
        
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', 'unknown')
            error_info = {
                'status_code': 429,
                'error': 'Rate Limited',
                'message': f'Too many requests. Retry after: {retry_after} seconds',
                'retry_after': retry_after,
                'response_time': response_time
            }
            print(f"  ⚠️  Rate limited! Retry after: {retry_after}")
            return None, error_info, response_time, 429, 0
        
        # Check for other HTTP errors
        if response.status_code >= 400:
            error_info = {
                'status_code': response.status_code,
                'error': f'HTTP {response.status_code}',
                'message': response.text[:200] if response.text else 'No error message',
                'url': url,
                'response_time': response_time
            }
            print(f"  ❌ HTTP {response.status_code}: {response.text[:100]}")
            return None, error_info, response_time, response.status_code, 0
        
        response.raise_for_status()
        return response.content, None, response_time, response.status_code, len(response.content)
        
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        error_info = {
            'status_code': 0,
            'error': 'Timeout',
            'message': f'Request timed out after {timeout} seconds',
            'url': url,
            'response_time': response_time
        }
        print(f"  ❌ Timeout after {timeout}s")
        return None, error_info, response_time, 0, 0
        
    except requests.exceptions.ConnectionError as e:
        response_time = time.time() - start_time
        error_info = {
            'status_code': 0,
            'error': 'Connection Error',
            'message': str(e),
            'url': url,
            'response_time': response_time
        }
        print(f"  ❌ Connection error: {e}")
        return None, error_info, response_time, 0, 0
        
    except Exception as e:
        response_time = time.time() - start_time
        error_info = {
            'status_code': 0,
            'error': type(e).__name__,
            'message': str(e),
            'url': url,
            'response_time': response_time
        }
        print(f"  ❌ Error: {e}")
        return None, error_info, response_time, 0, 0


def parse_vehicle_positions(pb_data):
    """Parse VehiclePositions.pb data"""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(pb_data)
    
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
            
            vehicles.append({
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
            })
    
    return vehicles


def parse_trip_updates(pb_data):
    """Parse TripUpdates.pb data"""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(pb_data)
    
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
    
    return trip_updates


def parse_alerts(pb_data):
    """Parse Alerts.pb data"""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(pb_data)
    
    alerts = []
    for entity in feed.entity:
        if entity.HasField('alert'):
            alert = entity.alert
            
            cause = gtfs_realtime_pb2.Alert.Cause.Name(alert.cause) if alert.HasField('cause') else None
            effect = gtfs_realtime_pb2.Alert.Effect.Name(alert.effect) if alert.HasField('effect') else None
            
            header_text = ""
            if alert.header_text.translation:
                header_text = alert.header_text.translation[0].text
            
            description_text = ""
            if alert.description_text.translation:
                description_text = alert.description_text.translation[0].text
            
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
            
            for informed_entity in alert.informed_entity:
                affected = {
                    'route_id': informed_entity.route_id if informed_entity.HasField('route_id') else None,
                    'trip_id': informed_entity.trip.trip_id if informed_entity.HasField('trip') else None,
                    'stop_id': informed_entity.stop_id if informed_entity.HasField('stop_id') else None
                }
                alert_data['affected_entities'].append(affected)
            
            alerts.append(alert_data)
    
    return alerts


def update_vehicle_positions(conn, vehicles):
    """Update vehicle positions in database"""
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
    return len(vehicles)


def update_trip_updates(conn, trip_updates):
    """Update trip updates in database"""
    cursor = conn.cursor()
    
    # Clear old updates (keep last hour)
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
    return len(trip_updates)


def update_alerts(conn, alerts):
    """Update alerts in database"""
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
    return len(alerts)


def log_health_check(endpoint_name, url, status, status_code, response_time, content_length, error_message, rate_limited):
    """Log health check to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO health_checks (
                timestamp, endpoint_name, endpoint_url, status, status_code,
                response_time, content_length, error_message, rate_limited
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            endpoint_name,
            url,
            status,
            status_code,
            response_time,
            content_length,
            error_message,
            1 if rate_limited else 0
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  Warning: Failed to log health check: {e}")


def update_all_realtime_data():
    """
    Download and update all real-time data
    Returns dict with counts, timestamp, and detailed errors
    """
    results = {
        'success': False,
        'timestamp': datetime.now().isoformat(),
        'vehicles': 0,
        'trip_updates': 0,
        'alerts': 0,
        'errors': [],
        'error_details': []  # Detailed error info
    }
    
    conn = sqlite3.connect(DB_FILE)
    
    try:
        # Update vehicle positions
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloading vehicle positions...")
        pb_data, error, response_time, status_code, content_length = download_pb_file(URLS['vehicle_positions'])
        
        # Log to health check table
        if pb_data:
            log_health_check('Vehicle Positions', URLS['vehicle_positions'], 'healthy', 
                           status_code, response_time, content_length, None, False)
            vehicles = parse_vehicle_positions(pb_data)
            results['vehicles'] = update_vehicle_positions(conn, vehicles)
            print(f"  ✅ Updated {results['vehicles']} vehicles")
        else:
            error_msg = 'Failed to download vehicle positions'
            log_health_check('Vehicle Positions', URLS['vehicle_positions'], 
                           'connection_error' if error and error.get('error') == 'Connection Error' else 'error',
                           status_code, response_time, content_length, 
                           error.get('message') if error else 'Unknown error',
                           error.get('status_code') == 429 if error else False)
            if error:
                error_msg += f": {error['error']}"
                results['error_details'].append({
                    'source': 'vehicle_positions',
                    **error
                })
            results['errors'].append(error_msg)
        
        # Update trip updates
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloading trip updates...")
        pb_data, error, response_time, status_code, content_length = download_pb_file(URLS['trip_updates'])
        
        if pb_data:
            log_health_check('Trip Updates', URLS['trip_updates'], 'healthy',
                           status_code, response_time, content_length, None, False)
            trip_updates = parse_trip_updates(pb_data)
            results['trip_updates'] = update_trip_updates(conn, trip_updates)
            print(f"  ✅ Updated {results['trip_updates']} trip updates")
        else:
            error_msg = 'Failed to download trip updates'
            log_health_check('Trip Updates', URLS['trip_updates'],
                           'connection_error' if error and error.get('error') == 'Connection Error' else 'error',
                           status_code, response_time, content_length,
                           error.get('message') if error else 'Unknown error',
                           error.get('status_code') == 429 if error else False)
            if error:
                error_msg += f": {error['error']}"
                results['error_details'].append({
                    'source': 'trip_updates',
                    **error
                })
            results['errors'].append(error_msg)
        
        # Update alerts
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloading alerts...")
        pb_data, error, response_time, status_code, content_length = download_pb_file(URLS['alerts'])
        
        if pb_data:
            log_health_check('Alerts', URLS['alerts'], 'healthy',
                           status_code, response_time, content_length, None, False)
            alerts = parse_alerts(pb_data)
            results['alerts'] = update_alerts(conn, alerts)
            print(f"  ✅ Updated {results['alerts']} alerts")
        else:
            error_msg = 'Failed to download alerts'
            log_health_check('Alerts', URLS['alerts'],
                           'connection_error' if error and error.get('error') == 'Connection Error' else 'error',
                           status_code, response_time, content_length,
                           error.get('message') if error else 'Unknown error',
                           error.get('status_code') == 429 if error else False)
            if error:
                error_msg += f": {error['error']}"
                results['error_details'].append({
                    'source': 'alerts',
                    **error
                })
            results['errors'].append(error_msg)
        
        # Success if at least one source worked
        results['success'] = results['vehicles'] > 0 or results['trip_updates'] > 0 or results['alerts'] > 0
        
    except Exception as e:
        results['errors'].append(str(e))
        results['error_details'].append({
            'source': 'system',
            'error': type(e).__name__,
            'message': str(e)
        })
        print(f"  ❌ Error: {e}")
    
    finally:
        conn.close()
    
    return results


if __name__ == '__main__':
    print("Testing live updater...")
    results = update_all_realtime_data()
    print("\nResults:", results)

