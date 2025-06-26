#!/usr/bin/env python3
"""
Fix ServiceNow Data Inconsistency
Triggers a manual ServiceNow sync to re-ingest incidents and fix the discrepancy
"""

import requests
import json
import time
import os

def trigger_servicenow_sync():
    """Trigger a manual ServiceNow sync"""
    
    print("🔧 Fixing ServiceNow Data Inconsistency")
    print("=" * 50)
    
    # Check if API server is running
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ API server is not running on port 8000")
            print("   Please start the RAG system first:")
            print("   python src/main_managed.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server on port 8000")
        print("   Please start the RAG system first:")
        print("   python src/main_managed.py")
        return False
    
    print("✅ API server is running")
    
    # Trigger manual sync with comprehensive filters
    sync_filters = {
        "priority_filter": ["1", "2", "3", "4", "5"],  # All priorities
        "state_filter": ["1", "2", "3", "4", "5", "6", "7"],  # All states
        "days_back": 30,  # Last 30 days
        "max_incidents_per_fetch": 1000,  # Fetch up to 1000 incidents
        "auto_ingest": True  # Automatically ingest into vector database
    }
    
    print(f"\n🔄 Triggering manual ServiceNow sync...")
    print(f"   Filters: {json.dumps(sync_filters, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/servicenow/sync",
            json=sync_filters,
            timeout=60  # 60 second timeout for sync operation
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ ServiceNow sync completed successfully!")
            print(f"📊 Results:")
            print(f"   Incidents Fetched: {result.get('incidents_fetched', 0)}")
            print(f"   Incidents Processed: {result.get('incidents_processed', 0)}")
            print(f"   Incidents Ingested: {result.get('incidents_ingested', 0)}")
            print(f"   New Incidents: {result.get('new_incidents', 0)}")
            print(f"   Updated Incidents: {result.get('updated_incidents', 0)}")
            print(f"   Duration: {result.get('duration', 0):.2f} seconds")
            
            if result.get('incidents_ingested', 0) > 0:
                print(f"\n🎉 ServiceNow data has been re-ingested!")
                print(f"   The discrepancy between conversation and query should now be resolved.")
                return True
            else:
                print(f"\n⚠️  No incidents were ingested. This might mean:")
                print(f"   - No incidents found in ServiceNow")
                print(f"   - All incidents are already up to date")
                print(f"   - There might be an issue with the ServiceNow connection")
                return False
                
        else:
            print(f"❌ ServiceNow sync failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ServiceNow sync timed out (60 seconds)")
        print("   The sync operation is still running in the background")
        return False
    except Exception as e:
        print(f"❌ Error triggering ServiceNow sync: {e}")
        return False

def check_servicenow_status():
    """Check ServiceNow integration status"""
    
    print(f"\n🔍 Checking ServiceNow Integration Status")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/servicenow/status", timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ ServiceNow Integration Status:")
            print(f"   Initialized: {status.get('initialized', False)}")
            print(f"   Connection Healthy: {status.get('connection_healthy', False)}")
            print(f"   Scheduler Running: {status.get('scheduler_running', False)}")
            print(f"   Last Sync Time: {status.get('last_sync_time', 'Never')}")
            
            # Show statistics
            stats = status.get('statistics', {})
            if stats:
                print(f"   Total Fetched: {stats.get('total_fetched', 0)}")
                print(f"   Total Processed: {stats.get('total_processed', 0)}")
                print(f"   Total Ingested: {stats.get('total_ingested', 0)}")
                print(f"   Last Error: {stats.get('last_error', 'None')}")
            
            return status.get('connection_healthy', False)
        else:
            print(f"❌ Failed to get ServiceNow status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking ServiceNow status: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ServiceNow Data Fix Script")
    print("=" * 60)
    print("This script will fix the ServiceNow data inconsistency by")
    print("triggering a manual sync to re-ingest all incidents.")
    print()
    
    # Check ServiceNow status first
    if not check_servicenow_status():
        print("\n❌ ServiceNow integration is not healthy")
        print("   Please check your ServiceNow configuration in .env")
        return False
    
    # Trigger the sync
    success = trigger_servicenow_sync()
    
    if success:
        print(f"\n✅ ServiceNow data fix completed!")
        print(f"   You can now test the conversation and query again.")
        print(f"   Both should now show the same number of incidents.")
    else:
        print(f"\n❌ ServiceNow data fix failed!")
        print(f"   Please check the logs for more details.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 