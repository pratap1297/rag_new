#!/usr/bin/env python3
"""
Check ServiceNow incidents count in cache database
"""

import sqlite3
import os

def check_servicenow_cache():
    """Check ServiceNow incidents in cache database"""
    db_path = 'data/servicenow_cache.db'
    
    if not os.path.exists(db_path):
        print(f"❌ ServiceNow cache database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute('SELECT COUNT(*) FROM incidents_cache')
        count = cursor.fetchone()[0]
        
        print(f"📊 ServiceNow incidents in cache: {count}")
        
        # Get some additional stats
        cursor = conn.execute('SELECT COUNT(*) FROM incidents_cache WHERE ingested = 1')
        ingested_count = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(*) FROM fetch_history')
        fetch_count = cursor.fetchone()[0]
        
        print(f"📥 Ingested incidents: {ingested_count}")
        print(f"🔄 Total fetch operations: {fetch_count}")
        
        # Get recent fetch info
        cursor = conn.execute('''
            SELECT fetch_time, incidents_fetched, incidents_processed, incidents_ingested 
            FROM fetch_history 
            ORDER BY fetch_time DESC 
            LIMIT 1
        ''')
        recent = cursor.fetchone()
        
        if recent:
            print(f"🕒 Last fetch: {recent[0]}")
            print(f"📋 Last fetch stats - Fetched: {recent[1]}, Processed: {recent[2]}, Ingested: {recent[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking ServiceNow cache: {e}")

if __name__ == "__main__":
    check_servicenow_cache() 