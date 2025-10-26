"""
Nightly Update Job
Downloads latest GTFS data and updates database
"""

import subprocess
import sys
from datetime import datetime
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'=' * 80}")
    print(f"{description}")
    print(f"{'=' * 80}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main nightly update process"""
    start_time = datetime.now()
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "MiWay Nightly Update Job" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")
    print(f"\nStarted: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Track success/failure
    steps = {
        'download': False,
        'load_static': False,
        'load_realtime': False
    }
    
    # Step 1: Download latest data
    steps['download'] = run_command(
        'python3 download_gtfs.py',
        '📥 STEP 1: Downloading Latest GTFS Data'
    )
    
    if not steps['download']:
        print("\n❌ Download failed. Stopping update process.")
        return 1
    
    # Step 2: Load static data into database
    steps['load_static'] = run_command(
        'python3 load_gtfs.py',
        '💾 STEP 2: Loading Static GTFS Data to Database'
    )
    
    if not steps['load_static']:
        print("\n⚠️  Static data load failed. Continuing with real-time data...")
    
    # Step 3: Load real-time data
    steps['load_realtime'] = run_command(
        'python3 ingest_realtime.py',
        '🚍 STEP 3: Loading Real-Time Data to Database'
    )
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 31 + "UPDATE SUMMARY" + " " * 33 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:  {duration:.1f} seconds")
    print()
    print("Status:")
    print(f"  {'✅' if steps['download'] else '❌'} Download Data")
    print(f"  {'✅' if steps['load_static'] else '❌'} Load Static Data")
    print(f"  {'✅' if steps['load_realtime'] else '❌'} Load Real-Time Data")
    print()
    
    if all(steps.values()):
        print("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        print()
        print("The MiWay app has been updated with the latest data.")
        print()
        return 0
    else:
        print("⚠️  SOME STEPS FAILED")
        print()
        print("Please check the errors above.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())

