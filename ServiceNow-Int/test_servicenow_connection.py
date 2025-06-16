#!/usr/bin/env python3
"""
ServiceNow Connection Test and Setup Guide
Tests ServiceNow connection and guides through credential setup.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
root_env_path = Path(__file__).parent.parent.parent / '.env'
if root_env_path.exists():
    load_dotenv(root_env_path)

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    
    if not env_path.exists():
        print("❌ .env file not found in root directory")
        print("\n📋 SETUP INSTRUCTIONS:")
        print("1. Copy 'env_template_root.txt' to '.env' in the root directory")
        print("2. Edit the .env file and fill in your ServiceNow credentials:")
        print("   - SERVICENOW_INSTANCE=your-instance.service-now.com")
        print("   - SERVICENOW_USERNAME=your_username") 
        print("   - SERVICENOW_PASSWORD=your_password")
        print("\n💡 Example .env content:")
        print("SERVICENOW_INSTANCE=dev12345.service-now.com")
        print("SERVICENOW_USERNAME=admin")
        print("SERVICENOW_PASSWORD=your_password")
        return False
    
    # Check required variables
    required_vars = ['SERVICENOW_INSTANCE', 'SERVICENOW_USERNAME', 'SERVICENOW_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_') or value.startswith('your-'):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or incomplete ServiceNow credentials in .env file:")
        for var in missing_vars:
            current_value = os.getenv(var, 'NOT SET')
            print(f"   {var}={current_value}")
        print("\n📝 Please edit your .env file and set the correct values.")
        return False
    
    print("✅ .env file found with ServiceNow credentials")
    return True

def test_servicenow_connection():
    """Test ServiceNow connection"""
    try:
        from servicenow_connector import ServiceNowConnector
        
        print("\n🔗 Testing ServiceNow connection...")
        connector = ServiceNowConnector()
        
        # Show connection details (without password)
        instance = os.getenv('SERVICENOW_INSTANCE')
        username = os.getenv('SERVICENOW_USERNAME')
        print(f"   Instance: {instance}")
        print(f"   Username: {username}")
        print(f"   URL: {connector.base_url}")
        
        # Test connection
        if connector.test_connection():
            print("✅ ServiceNow connection successful!")
            
            # Get recent incidents to verify access
            print("\n📋 Testing incident access...")
            incidents = connector.get_incidents(limit=3)
            
            if incidents:
                print(f"✅ Successfully retrieved {len(incidents)} incidents")
                print("\n📊 Recent incidents:")
                for i, incident in enumerate(incidents[:3], 1):
                    number = incident.get('number', 'N/A')
                    desc = incident.get('short_description', 'No description')[:50]
                    priority = incident.get('priority', 'N/A')
                    print(f"   {i}. {number} - Priority {priority} - {desc}...")
                return True
            else:
                print("⚠️  Connection successful but no incidents found")
                print("   This might be normal if your instance has no incidents")
                return True
        else:
            print("❌ ServiceNow connection failed")
            print("\n🔧 Troubleshooting tips:")
            print("1. Verify your instance URL is correct")
            print("2. Check username and password")
            print("3. Ensure your user has incident read/write permissions")
            print("4. Check if your ServiceNow instance is accessible")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def create_test_tickets():
    """Create test tickets in ServiceNow"""
    try:
        from create_sample_tickets import WarehouseNetworkTicketGenerator
        
        print("\n🎫 Creating test tickets in ServiceNow...")
        generator = WarehouseNetworkTicketGenerator()
        
        # Create 3 test tickets
        created_tickets = generator.create_sample_tickets(3)
        
        if created_tickets:
            print(f"\n✅ Successfully created {len(created_tickets)} test tickets!")
            print("\n📋 Created tickets:")
            for ticket in created_tickets:
                print(f"   • {ticket['number']} - Priority {ticket.get('priority', 'Unknown')}")
            return True
        else:
            print("❌ Failed to create test tickets")
            return False
            
    except Exception as e:
        print(f"❌ Error creating tickets: {str(e)}")
        return False

def main():
    """Main function"""
    print("🔧 ServiceNow Connection Test and Setup")
    print("=" * 50)
    
    # Step 1: Check .env file
    if not check_env_file():
        print("\n❌ Setup incomplete. Please configure your .env file first.")
        return
    
    # Step 2: Test connection
    if not test_servicenow_connection():
        print("\n❌ Connection failed. Please check your credentials.")
        return
    
    # Step 3: Ask if user wants to create test tickets
    print("\n" + "=" * 50)
    create_tickets = input("Would you like to create test tickets in ServiceNow? (y/n): ").strip().lower()
    
    if create_tickets in ['y', 'yes']:
        if create_test_tickets():
            print("\n🎉 Test completed successfully!")
            print("\n📝 Next steps:")
            print("1. Check your ServiceNow instance for the created tickets")
            print("2. Use 'python create_sample_tickets.py' to create more tickets")
            print("3. Use the ServiceNow scheduler to automatically fetch tickets")
        else:
            print("\n❌ Test ticket creation failed")
    else:
        print("\n✅ Connection test completed successfully!")
        print("\n📝 You can now use:")
        print("• python create_sample_tickets.py - Create warehouse network tickets")
        print("• python servicenow_scheduler.py - Start automatic ticket fetching")

if __name__ == "__main__":
    main() 