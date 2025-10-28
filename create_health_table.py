"""
Create health check table in the database
"""

import sqlite3

DB_FILE = 'miway.db'

def create_health_check_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create health_checks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            endpoint_name TEXT NOT NULL,
            endpoint_url TEXT NOT NULL,
            status TEXT NOT NULL,
            status_code INTEGER,
            response_time REAL,
            content_length INTEGER,
            error_message TEXT,
            rate_limited INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_health_checks_timestamp 
        ON health_checks(timestamp DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_health_checks_endpoint 
        ON health_checks(endpoint_name)
    """)
    
    conn.commit()
    conn.close()
    print("✅ Health check table created successfully")

if __name__ == '__main__':
    create_health_check_table()

