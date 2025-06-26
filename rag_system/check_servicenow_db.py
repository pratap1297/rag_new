#!/usr/bin/env python3
"""
Check ServiceNow cache database
"""

import sqlite3
import os

def check_servicenow_db():
    """Check ServiceNow cache database"""
    
    db_path = 'data/servicenow_cache.db'
    if not os.path.exists(db_path):
        print(f"❌ ServiceNow cache database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Tables in database: {[table[0] for table in tables]}")
        
        # Check incidents count
        cursor.execute("SELECT COUNT(*) FROM incidents_cache")
        total_incidents = cursor.fetchone()[0]
        print(f"📋 Total incidents in cache: {total_incidents}")
        
        if total_incidents > 0:
            # Get sample incidents
            cursor.execute("SELECT number, short_description FROM incidents_cache LIMIT 10")
            incidents = cursor.fetchall()
            print(f"\n🔍 Sample incidents:")
            for i, (number, description) in enumerate(incidents, 1):
                print(f"  {i}. {number}: {description}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_servicenow_db() 