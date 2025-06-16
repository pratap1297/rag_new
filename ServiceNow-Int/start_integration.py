#!/usr/bin/env python3
"""
ServiceNow Integration Startup Script
Simple script to start the ServiceNow scheduler integration with the Router Rescue AI backend.
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Load environment variables from multiple locations
load_dotenv()  # Load from current directory
root_env_path = Path(__file__).parent.parent.parent / '.env'
if root_env_path.exists():
    load_dotenv(root_env_path)  # Load from root directory
    print(f"✅ Loaded environment from: {root_env_path}")
else:
    print(f"ℹ️  No .env file found at: {root_env_path}")

from backend_integration import BackendIntegration

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\nReceived shutdown signal. Stopping integration...")
    if 'integration' in globals():
        integration.stop_integration()
    sys.exit(0)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'SERVICENOW_INSTANCE',
        'SERVICENOW_USERNAME', 
        'SERVICENOW_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file.")
        print(f"📁 Expected .env file location: {root_env_path}")
        print("📋 See env_template_root.txt for reference configuration.")
        print("\n💡 Quick setup:")
        print(f"   1. Copy env_template_root.txt to {root_env_path}")
        print("   2. Edit the .env file with your ServiceNow credentials")
        print("   3. Run this script again")
        return False
    
    return True

def print_configuration():
    """Print current configuration"""
    print("🔧 Configuration:")
    print(f"   ServiceNow Instance: {os.getenv('SERVICENOW_INSTANCE')}")
    print(f"   Username: {os.getenv('SERVICENOW_USERNAME')}")
    print(f"   Fetch Interval: {os.getenv('SERVICENOW_FETCH_INTERVAL', '15')} minutes")
    print(f"   Priority Filter: {os.getenv('SERVICENOW_PRIORITY_FILTER', '1,2,3')}")
    print(f"   State Filter: {os.getenv('SERVICENOW_STATE_FILTER', '1,2,3')}")
    print(f"   Days Back: {os.getenv('SERVICENOW_DAYS_BACK', '7')}")
    print(f"   Categories: {os.getenv('SERVICENOW_CATEGORIES', 'Network,Infrastructure')}")
    print(f"   Backend URL: {os.getenv('BACKEND_URL', 'http://localhost:8000')}")
    print()

def test_servicenow_connection():
    """Test ServiceNow connection before starting"""
    print("🔍 Testing ServiceNow connection...")
    try:
        from servicenow_connector import ServiceNowConnector
        connector = ServiceNowConnector()
        if connector.test_connection():
            print("✅ ServiceNow connection successful!")
            return True
        else:
            print("❌ ServiceNow connection failed!")
            return False
    except Exception as e:
        print(f"❌ Error testing ServiceNow connection: {str(e)}")
        return False

def main():
    """Main function to start the integration"""
    print("🚀 Starting ServiceNow Integration for Router Rescue AI")
    print("=" * 60)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Print configuration
    print_configuration()
    
    # Test ServiceNow connection
    if not test_servicenow_connection():
        print("\n💡 Troubleshooting tips:")
        print("   - Verify your ServiceNow credentials in .env file")
        print("   - Check if your ServiceNow instance URL is correct")
        print("   - Ensure your ServiceNow user has API access permissions")
        print("   - Check network connectivity to ServiceNow")
        sys.exit(1)
    
    # Create and start integration
    try:
        print("🔌 Initializing ServiceNow integration...")
        global integration
        integration = BackendIntegration()
        
        print("✅ Starting scheduler...")
        integration.start_integration()
        
        print("🎯 Integration started successfully!")
        print("📊 Monitoring for incidents...")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        # Keep the script running
        while True:
            time.sleep(60)
            
            # Print status every 10 minutes
            if int(time.time()) % 600 == 0:
                if hasattr(integration, 'scheduler') and integration.scheduler:
                    try:
                        stats = integration.scheduler.get_fetch_statistics()
                        print(f"📈 Status: {stats.get('total_cached_incidents', 0)} incidents cached, "
                              f"last fetch: {stats.get('last_fetch_time', 'Never')}")
                    except Exception as e:
                        print(f"⚠️  Error getting statistics: {str(e)}")
                
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"❌ Error starting integration: {str(e)}")
        logging.exception("Integration startup error")
        sys.exit(1)
    finally:
        if 'integration' in globals():
            print("🔄 Stopping integration...")
            integration.stop_integration()
            print("✅ Integration stopped successfully")

if __name__ == "__main__":
    main() 