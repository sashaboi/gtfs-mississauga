"""
Download Latest GTFS Data from MiWay
Fetches both static and real-time data
"""

import requests
import zipfile
import os
import shutil
from datetime import datetime

# MiWay Data URLs
URLS = {
    'static': 'https://www.miapp.ca/GTFS/google_transit.zip',
    'vehicle_positions': 'https://www.miapp.ca/GTFS_RT/Vehicle/VehiclePositions.pb',
    'trip_updates': 'https://www.miapp.ca/GTFS_RT/TripUpdate/TripUpdates.pb',
    'alerts': 'https://www.miapp.ca/gtfs_rt/Alerts/Alerts.pb'
}

# Directories
DOWNLOAD_DIR = 'data_downloads'
STATIC_DIR = 'google_transit'
REALTIME_DIR = '.'  # Root directory for .pb files

def ensure_directories():
    """Create necessary directories"""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    print(f"✅ Directories ready: {DOWNLOAD_DIR}, {STATIC_DIR}\n")


def download_file(url, filename, description):
    """Download a file from URL"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    print(f"📥 Downloading {description}...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content) / 1024  # KB
        print(f"✅ Downloaded: {filename} ({file_size:.1f} KB)\n")
        return filepath
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading {description}: {e}\n")
        return None


def extract_static_gtfs(zip_path):
    """Extract google_transit.zip to google_transit folder"""
    print(f"📦 Extracting GTFS static data...")
    
    try:
        # Backup old data if exists
        if os.path.exists(STATIC_DIR) and os.listdir(STATIC_DIR):
            backup_dir = f"{STATIC_DIR}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"   Backing up old data to: {backup_dir}")
            shutil.copytree(STATIC_DIR, backup_dir)
        
        # Clear existing data
        if os.path.exists(STATIC_DIR):
            for file in os.listdir(STATIC_DIR):
                os.remove(os.path.join(STATIC_DIR, file))
        
        # Extract new data
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(STATIC_DIR)
        
        # List extracted files
        files = os.listdir(STATIC_DIR)
        print(f"✅ Extracted {len(files)} files:")
        for file in sorted(files):
            print(f"   - {file}")
        print()
        
        return True
    
    except Exception as e:
        print(f"❌ Error extracting GTFS data: {e}\n")
        return False


def move_realtime_files():
    """Move .pb files to root directory"""
    print("📦 Moving real-time files to root...")
    
    pb_files = {
        'VehiclePositions.pb': 'VehiclePositions.pb',
        'TripUpdates.pb': 'TripUpdates.pb',
        'Alerts.pb': 'Alerts.pb'
    }
    
    for source_name, dest_name in pb_files.items():
        source = os.path.join(DOWNLOAD_DIR, source_name)
        dest = os.path.join(REALTIME_DIR, dest_name)
        
        if os.path.exists(source):
            # Backup old file
            if os.path.exists(dest):
                backup = f"{dest}.backup"
                shutil.copy2(dest, backup)
                print(f"   Backed up: {dest_name}")
            
            # Move new file
            shutil.copy2(source, dest)
            print(f"✅ Updated: {dest_name}")
        else:
            print(f"⚠️  Not found: {source_name}")
    
    print()


def verify_data():
    """Verify downloaded data"""
    print("🔍 Verifying data integrity...\n")
    
    issues = []
    
    # Check static GTFS files
    required_static = [
        'agency.txt', 'routes.txt', 'stops.txt', 
        'trips.txt', 'stop_times.txt'
    ]
    
    for file in required_static:
        path = os.path.join(STATIC_DIR, file)
        if not os.path.exists(path):
            issues.append(f"Missing: {file}")
        elif os.path.getsize(path) == 0:
            issues.append(f"Empty: {file}")
        else:
            size_kb = os.path.getsize(path) / 1024
            print(f"✅ {file}: {size_kb:.1f} KB")
    
    print()
    
    # Check real-time files
    realtime_files = ['VehiclePositions.pb', 'TripUpdates.pb', 'Alerts.pb']
    
    for file in realtime_files:
        path = os.path.join(REALTIME_DIR, file)
        if not os.path.exists(path):
            issues.append(f"Missing: {file}")
        elif os.path.getsize(path) == 0:
            issues.append(f"Empty: {file}")
        else:
            size_kb = os.path.getsize(path) / 1024
            print(f"✅ {file}: {size_kb:.1f} KB")
    
    print()
    
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        return False
    else:
        print("✅ All data files verified!\n")
        return True


def main():
    """Main download function"""
    print("=" * 80)
    print("MiWay GTFS Data Downloader")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ensure directories exist
    ensure_directories()
    
    # Download static GTFS (zip file)
    print("=" * 80)
    print("DOWNLOADING STATIC GTFS DATA")
    print("=" * 80)
    print()
    
    zip_path = download_file(
        URLS['static'],
        'google_transit.zip',
        'Static GTFS Data'
    )
    
    if zip_path:
        extract_static_gtfs(zip_path)
    
    # Download real-time data
    print("=" * 80)
    print("DOWNLOADING REAL-TIME GTFS DATA")
    print("=" * 80)
    print()
    
    download_file(
        URLS['vehicle_positions'],
        'VehiclePositions.pb',
        'Vehicle Positions'
    )
    
    download_file(
        URLS['trip_updates'],
        'TripUpdates.pb',
        'Trip Updates'
    )
    
    download_file(
        URLS['alerts'],
        'Alerts.pb',
        'Service Alerts'
    )
    
    # Move real-time files to root
    move_realtime_files()
    
    # Verify data
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()
    
    if verify_data():
        print("=" * 80)
        print("✅ DOWNLOAD COMPLETE!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Load static data:    python3 load_gtfs.py")
        print("  2. Load real-time data: python3 ingest_realtime.py")
        print("  3. Start app:           python3 app.py")
        print()
    else:
        print("=" * 80)
        print("⚠️  DOWNLOAD COMPLETED WITH ISSUES")
        print("=" * 80)
        print()
        print("Please check the errors above and try again.")
        print()


if __name__ == '__main__':
    main()

