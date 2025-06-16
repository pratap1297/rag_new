#!/usr/bin/env python3
"""
Simple ServiceNow Connection Test
This script helps debug connection issues by showing the configuration values.
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()

def test_env_variables():
    """Test and display environment variables"""
    print("🔍 CHECKING ENVIRONMENT VARIABLES")
    print("-" * 50)
    
    instance = os.getenv('SERVICENOW_INSTANCE')
    username = os.getenv('SERVICENOW_USERNAME')
    password = os.getenv('SERVICENOW_PASSWORD')
    
    print(f"SERVICENOW_INSTANCE: {instance}")
    print(f"SERVICENOW_USERNAME: {username}")
    print(f"SERVICENOW_PASSWORD: {'*' * len(password) if password else 'Not set'}")
    
    if not all([instance, username, password]):
        print("❌ Missing required environment variables!")
        return False
    
    # Check if instance has https:// prefix (it shouldn't)
    if instance.startswith('https://'):
        print("⚠️  WARNING: SERVICENOW_INSTANCE should not include 'https://'")
        print(f"   Current value: {instance}")
        print(f"   Should be: {instance.replace('https://', '')}")
        return False
    
    print("✅ Environment variables look good!")
    return True

def test_url_construction():
    """Test URL construction"""
    print("\n🔗 TESTING URL CONSTRUCTION")
    print("-" * 50)
    
    instance = os.getenv('SERVICENOW_INSTANCE')
    base_url = f"https://{instance}/api/now/table"
    test_url = f"{base_url}/incident"
    
    print(f"Instance: {instance}")
    print(f"Base URL: {base_url}")
    print(f"Test URL: {test_url}")
    
    return test_url

def test_basic_connection():
    """Test basic HTTP connection"""
    print("\n🌐 TESTING BASIC CONNECTION")
    print("-" * 50)
    
    if not test_env_variables():
        return False
    
    instance = os.getenv('SERVICENOW_INSTANCE')
    username = os.getenv('SERVICENOW_USERNAME')
    password = os.getenv('SERVICENOW_PASSWORD')
    
    # Clean up instance URL if needed
    if instance.startswith('https://'):
        instance = instance.replace('https://', '')
    if instance.startswith('http://'):
        instance = instance.replace('http://', '')
    
    url = f"https://{instance}/api/now/table/incident"
    auth = HTTPBasicAuth(username, password)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print(f"Attempting connection to: {url}")
    
    try:
        response = requests.get(
            url,
            auth=auth,
            headers=headers,
            params={'sysparm_limit': 1},
            timeout=30
        )
        
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Connection successful!")
            result = response.json()
            print(f"Retrieved {len(result.get('result', []))} incidents")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed - check username/password")
            return False
        elif response.status_code == 403:
            print("❌ Access forbidden - check user permissions")
            return False
        else:
            print(f"❌ Connection failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test function"""
    print("ServiceNow Connection Test")
    print("=" * 60)
    
    # Test environment variables
    if not test_env_variables():
        print("\n❌ Environment variable test failed!")
        print("\nPlease check your .env file and ensure:")
        print("1. SERVICENOW_INSTANCE is set (without https://)")
        print("2. SERVICENOW_USERNAME is set")
        print("3. SERVICENOW_PASSWORD is set")
        return
    
    # Test URL construction
    test_url_construction()
    
    # Test basic connection
    if test_basic_connection():
        print("\n🎉 All tests passed! ServiceNow integration is ready to use.")
    else:
        print("\n❌ Connection test failed. Please check your credentials and network connectivity.")

if __name__ == "__main__":
    main() 