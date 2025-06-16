#!/usr/bin/env python3
"""
ServiceNow Integration Setup Script
Helps configure and test ServiceNow integration for RAG system
"""

import os
import json
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{step}. {description}")
    print("-" * 40)

def check_environment():
    """Check if ServiceNow environment variables are set"""
    print_step(1, "Checking Environment Variables")
    
    load_dotenv()
    
    required_vars = [
        'SERVICENOW_INSTANCE',
        'SERVICENOW_USERNAME', 
        'SERVICENOW_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
        else:
            # Mask password for security
            display_value = value if var != 'SERVICENOW_PASSWORD' else '*' * len(value)
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n⚠️ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return False
    
    print("\n✅ All required environment variables are set")
    return True

def check_system_config():
    """Check if ServiceNow is configured in system config"""
    print_step(2, "Checking System Configuration")
    
    config_path = Path("rag-system/data/config/system_config.json")
    
    if not config_path.exists():
        print(f"❌ System config not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        servicenow_config = config.get('servicenow', {})
        
        if not servicenow_config:
            print("❌ ServiceNow configuration not found in system_config.json")
            print("Adding default ServiceNow configuration...")
            
            # Add default ServiceNow config
            config['servicenow'] = {
                "enabled": False,
                "fetch_interval_minutes": 15,
                "batch_size": 100,
                "max_incidents_per_fetch": 1000,
                "priority_filter": ["1", "2", "3"],
                "state_filter": ["1", "2", "3"],
                "days_back": 7,
                "network_only": False,
                "auto_ingest": True,
                "cache_enabled": True,
                "cache_ttl_hours": 1
            }
            
            # Write back to file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Default ServiceNow configuration added")
        else:
            print("✅ ServiceNow configuration found")
            print(f"   Enabled: {servicenow_config.get('enabled', False)}")
            print(f"   Fetch Interval: {servicenow_config.get('fetch_interval_minutes', 15)} minutes")
            print(f"   Auto Ingest: {servicenow_config.get('auto_ingest', True)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading system config: {e}")
        return False

def test_servicenow_connection():
    """Test connection to ServiceNow"""
    print_step(3, "Testing ServiceNow Connection")
    
    try:
        # Import ServiceNow connector
        sys.path.insert(0, str(Path("rag-system/src").resolve()))
        from integrations.servicenow.connector import ServiceNowConnector
        
        print("Creating ServiceNow connector...")
        connector = ServiceNowConnector()
        
        print("Testing connection...")
        if connector.test_connection():
            print("✅ ServiceNow connection successful!")
            
            # Try to fetch a small number of incidents
            print("Testing incident retrieval...")
            incidents = connector.get_incidents(limit=2)
            print(f"✅ Successfully retrieved {len(incidents)} incidents")
            
            if incidents:
                incident = incidents[0]
                print(f"   Sample incident: {incident.get('number')} - {incident.get('short_description', '')[:50]}...")
            
            return True
        else:
            print("❌ ServiceNow connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ServiceNow connection: {e}")
        return False

def test_rag_integration():
    """Test if RAG system is running and accessible"""
    print_step(4, "Testing RAG System Integration")
    
    try:
        # Test basic health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ RAG system is running and accessible")
            
            # Test ServiceNow API endpoints
            try:
                response = requests.get("http://localhost:8000/api/servicenow/status", timeout=5)
                if response.status_code == 200:
                    print("✅ ServiceNow API endpoints are available")
                    status = response.json()
                    print(f"   Initialized: {status.get('initialized', False)}")
                    print(f"   Connection Healthy: {status.get('connection_healthy', False)}")
                    return True
                else:
                    print(f"⚠️ ServiceNow API endpoints returned status {response.status_code}")
                    return False
            except Exception as e:
                print(f"⚠️ ServiceNow API endpoints not available: {e}")
                return False
                
        else:
            print(f"❌ RAG system health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to RAG system (http://localhost:8000)")
        print("   Make sure the RAG system is running: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error testing RAG integration: {e}")
        return False

def initialize_integration():
    """Initialize the ServiceNow integration"""
    print_step(5, "Initializing ServiceNow Integration")
    
    try:
        # Initialize integration
        response = requests.post("http://localhost:8000/api/servicenow/initialize", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✅ ServiceNow integration initialized successfully")
                return True
            else:
                print(f"❌ Initialization failed: {result.get('message')}")
                return False
        else:
            print(f"❌ Initialization request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing integration: {e}")
        return False

def run_test_sync():
    """Run a test synchronization"""
    print_step(6, "Running Test Synchronization")
    
    try:
        # Run manual sync with limited scope
        sync_filters = {
            "priority_filter": ["1", "2"],  # Critical and High only
            "days_back": 1,                 # Last 1 day only
            "limit": 5                      # Max 5 incidents
        }
        
        print("Starting test sync (limited scope)...")
        response = requests.post(
            "http://localhost:8000/api/servicenow/sync",
            json=sync_filters,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test synchronization completed successfully")
            print(f"   Incidents Fetched: {result.get('incidents_fetched', 0)}")
            print(f"   Incidents Processed: {result.get('incidents_processed', 0)}")
            print(f"   Incidents Ingested: {result.get('incidents_ingested', 0)}")
            print(f"   Duration: {result.get('duration', 0):.2f} seconds")
            return True
        else:
            print(f"❌ Test sync failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error running test sync: {e}")
        return False

def main():
    """Main setup function"""
    print_header("ServiceNow Integration Setup")
    print("This script will help you configure and test ServiceNow integration")
    
    # Run all checks
    checks = [
        check_environment,
        check_system_config,
        test_servicenow_connection,
        test_rag_integration,
        initialize_integration,
        run_test_sync
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
            if not result:
                print(f"\n⚠️ Check failed. Please resolve the issue before continuing.")
                break
        except KeyboardInterrupt:
            print("\n\n⚠️ Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            results.append(False)
            break
    
    # Summary
    print_header("Setup Summary")
    
    if all(results):
        print("🎉 ServiceNow integration setup completed successfully!")
        print("\nNext steps:")
        print("1. Enable automated sync: POST /api/servicenow/start")
        print("2. Monitor integration: GET /api/servicenow/status")
        print("3. Query ServiceNow data through regular RAG API")
        print("\nDocumentation: docs/SERVICENOW_INTEGRATION.md")
    else:
        print("❌ Setup incomplete. Please resolve the issues above.")
        print("\nFor help:")
        print("1. Check the documentation: docs/SERVICENOW_INTEGRATION.md")
        print("2. Verify your ServiceNow credentials")
        print("3. Ensure the RAG system is running")
    
    print(f"\nSetup completed with {sum(results)}/{len(results)} checks passed")

if __name__ == "__main__":
    main() 