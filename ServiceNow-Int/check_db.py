#!/usr/bin/env python3
import sqlite3
import json

def check_db():
    try:
        conn = sqlite3.connect('servicenow_cache.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        # Check incidents table
        if 'incidents' in tables:
            cursor.execute("SELECT COUNT(*) FROM incidents")
            count = cursor.fetchone()[0]
            print(f"Total incidents: {count}")
            
            if count > 0:
                cursor.execute("SELECT number, data FROM incidents LIMIT 10")
                incidents = cursor.fetchall()
                print("Sample incidents:")
                for i, (number, data_str) in enumerate(incidents, 1):
                    if data_str:
                        data = json.loads(data_str)
                        short_desc = data.get('short_description', 'No description')
                        print(f"  {i}. {number}: {short_desc}")
                    else:
                        print(f"  {i}. {number}: No data")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db() 