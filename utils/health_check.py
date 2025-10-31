"""
GTFS Endpoints Health Check and Audit Log
Tests all MiWay endpoints and logs their status
"""

import requests
import time
from datetime import datetime
import json
import os
import sqlite3

# MiWay Endpoints
ENDPOINTS = {
    'Static GTFS': 'https://www.miapp.ca/GTFS/google_transit.zip',
    'Vehicle Positions': 'https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb',
    'Trip Updates': 'https://www.miapp.ca/GTFS_RT/TripUpdate/TripUpdates.pb',
    'Alerts': 'https://www.miapp.ca/gtfs_rt/Alerts/Alerts.pb'
}

DB_FILE = 'miway.db'
LOG_FILE = 'logs/health_check.log'


def check_endpoint(name, url, timeout=10):
    """
    Check a single endpoint and return detailed status
    """
    result = {
        'name': name,
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'status': 'unknown',
        'status_code': None,
        'response_time': None,
        'content_length': None,
        'headers': {},
        'error': None,
        'rate_limited': False
    }
    
    # Add browser-like headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    start_time = time.time()
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response_time = time.time() - start_time
        
        result['status_code'] = response.status_code
        result['response_time'] = round(response_time, 2)
        result['content_length'] = int(response.headers.get('Content-Length', 0))
        
        # Capture important headers
        result['headers'] = {
            'Content-Type': response.headers.get('Content-Type'),
            'Content-Length': response.headers.get('Content-Length'),
            'Last-Modified': response.headers.get('Last-Modified'),
            'Cache-Control': response.headers.get('Cache-Control'),
            'Retry-After': response.headers.get('Retry-After'),
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
        }
        
        # Check status
        if response.status_code == 200:
            result['status'] = 'healthy'
            # Get actual content size
            content = response.content
            result['content_length'] = len(content)
        elif response.status_code == 429:
            result['status'] = 'rate_limited'
            result['rate_limited'] = True
            result['error'] = f"Rate limited. Retry after: {response.headers.get('Retry-After', 'unknown')}"
        elif response.status_code >= 500:
            result['status'] = 'server_error'
            result['error'] = f"Server error: {response.status_code}"
        elif response.status_code >= 400:
            result['status'] = 'client_error'
            result['error'] = f"Client error: {response.status_code}"
        else:
            result['status'] = 'warning'
            result['error'] = f"Unexpected status: {response.status_code}"
        
        response.close()
        
    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['response_time'] = timeout
        result['error'] = f"Request timed out after {timeout} seconds"
        
    except requests.exceptions.ConnectionError as e:
        result['status'] = 'connection_error'
        result['response_time'] = time.time() - start_time
        result['error'] = f"Connection error: {str(e)[:100]}"
        
    except Exception as e:
        result['status'] = 'error'
        result['response_time'] = time.time() - start_time
        result['error'] = f"{type(e).__name__}: {str(e)[:100]}"
    
    return result


def format_size(bytes):
    """Format bytes to human readable"""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    else:
        return f"{bytes / (1024 * 1024):.1f} MB"


def print_result(result):
    """Pretty print a check result"""
    # Status emoji
    status_emoji = {
        'healthy': '✅',
        'rate_limited': '⚠️',
        'timeout': '⏱️',
        'connection_error': '❌',
        'server_error': '🔥',
        'client_error': '❌',
        'warning': '⚠️',
        'error': '❌',
        'unknown': '❓'
    }
    
    emoji = status_emoji.get(result['status'], '❓')
    
    print(f"\n{emoji} {result['name']}")
    print(f"   URL: {result['url']}")
    print(f"   Status: {result['status'].upper()}")
    
    if result['status_code']:
        print(f"   HTTP Code: {result['status_code']}")
    
    if result['response_time']:
        print(f"   Response Time: {result['response_time']}s")
    
    if result['content_length']:
        print(f"   Size: {format_size(result['content_length'])}")
    
    if result['rate_limited']:
        print(f"   ⚠️  RATE LIMITED!")
        if result['headers'].get('Retry-After'):
            print(f"   Retry After: {result['headers']['Retry-After']}s")
        if result['headers'].get('X-RateLimit-Remaining'):
            print(f"   Remaining Requests: {result['headers']['X-RateLimit-Remaining']}")
    
    if result['error']:
        print(f"   Error: {result['error']}")
    
    # Show useful headers
    if result['headers'].get('Last-Modified'):
        print(f"   Last Modified: {result['headers']['Last-Modified']}")
    
    if result['headers'].get('Cache-Control'):
        print(f"   Cache: {result['headers']['Cache-Control']}")


def save_to_database(results):
    """Save results to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        for result in results:
            cursor.execute("""
                INSERT INTO health_checks (
                    timestamp, endpoint_name, endpoint_url, status, status_code,
                    response_time, content_length, error_message, rate_limited
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                result['name'],
                result['url'],
                result['status'],
                result['status_code'],
                result['response_time'],
                result['content_length'],
                result['error'],
                1 if result['rate_limited'] else 0
            ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error saving to database: {e}")


def save_to_log(results):
    """Save results to log file (deprecated, keeping for backwards compatibility)"""
    os.makedirs('logs', exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def run_health_check():
    """Run health check on all endpoints"""
    print("=" * 80)
    print("MiWay GTFS Endpoints Health Check")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    for name, url in ENDPOINTS.items():
        result = check_endpoint(name, url)
        results.append(result)
        print_result(result)
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    healthy = sum(1 for r in results if r['status'] == 'healthy')
    rate_limited = sum(1 for r in results if r['rate_limited'])
    errors = sum(1 for r in results if r['status'] in ['error', 'server_error', 'client_error', 'connection_error', 'timeout'])
    
    print(f"\n✅ Healthy: {healthy}/{len(results)}")
    
    if rate_limited > 0:
        print(f"⚠️  Rate Limited: {rate_limited}")
        print("\n⚠️  WARNING: You are being rate limited!")
        print("   Consider reducing update frequency.")
    
    if errors > 0:
        print(f"❌ Errors: {errors}")
    
    # Total data size
    total_size = sum(r['content_length'] or 0 for r in results)
    print(f"\nTotal Data Size: {format_size(total_size)}")
    
    # Average response time
    avg_time = sum(r['response_time'] or 0 for r in results) / len(results)
    print(f"Average Response Time: {avg_time:.2f}s")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if rate_limited > 0:
        print("\n⚠️  Rate Limiting Detected:")
        print("   1. Increase update interval (currently 30s)")
        print("   2. Implement exponential backoff")
        print("   3. Consider caching more aggressively")
    
    if any(r['response_time'] and r['response_time'] > 5 for r in results):
        print("\n⚠️  Slow Response Times:")
        print("   1. Check network connection")
        print("   2. MiWay servers may be overloaded")
        print("   3. Consider increasing timeout")
    
    if healthy == len(results):
        print("\n✅ All endpoints healthy!")
        print("   Current configuration is working well.")
    
    print()
    
    # Save to database
    save_to_database(results)
    print(f"📝 Results saved to database")
    print()
    
    return results


def monitor_for_rate_limiting(duration_seconds=300, check_interval=30):
    """
    Monitor endpoints for rate limiting over a period
    duration_seconds: How long to monitor (default 5 minutes)
    check_interval: Seconds between checks (default 30)
    """
    print("=" * 80)
    print("Rate Limiting Monitor")
    print("=" * 80)
    print(f"Duration: {duration_seconds}s ({duration_seconds/60:.1f} minutes)")
    print(f"Check Interval: {check_interval}s")
    print(f"Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    start_time = time.time()
    check_count = 0
    rate_limit_count = 0
    
    while time.time() - start_time < duration_seconds:
        check_count += 1
        print(f"\n--- Check #{check_count} at {datetime.now().strftime('%H:%M:%S')} ---")
        
        for name, url in ENDPOINTS.items():
            result = check_endpoint(name, url, timeout=5)
            
            if result['rate_limited']:
                rate_limit_count += 1
                print(f"⚠️  {name}: RATE LIMITED!")
            elif result['status'] == 'healthy':
                print(f"✅ {name}: OK ({result['response_time']}s)")
            else:
                print(f"❌ {name}: {result['status'].upper()}")
        
        time.sleep(check_interval)
    
    print("\n" + "=" * 80)
    print("Monitor Complete")
    print("=" * 80)
    print(f"Total Checks: {check_count}")
    print(f"Rate Limits: {rate_limit_count}")
    
    if rate_limit_count > 0:
        print(f"\n⚠️  Rate limiting occurred {rate_limit_count} times!")
        print("Consider increasing update interval.")
    else:
        print("\n✅ No rate limiting detected during monitoring period.")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        # Run monitoring mode
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        interval = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        monitor_for_rate_limiting(duration, interval)
    else:
        # Run single health check
        run_health_check()

