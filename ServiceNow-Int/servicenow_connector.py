# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ServiceNow Connector
Handles connection and operations with ServiceNow instance.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
root_env_path = Path(__file__).parent.parent.parent / '.env'
if root_env_path.exists():
    load_dotenv(root_env_path)

class ServiceNowConnector:
    """ServiceNow API connector for incident management"""
    
    def __init__(self):
        """Initialize ServiceNow connector with credentials from environment"""
        
        # Get ServiceNow credentials from environment
        self.instance = os.getenv('SERVICENOW_INSTANCE')
        self.username = os.getenv('SERVICENOW_USERNAME')
        self.password = os.getenv('SERVICENOW_PASSWORD')
        
        # Validate required credentials
        if not all([self.instance, self.username, self.password]):
            missing = []
            if not self.instance: missing.append('SERVICENOW_INSTANCE')
            if not self.username: missing.append('SERVICENOW_USERNAME')
            if not self.password: missing.append('SERVICENOW_PASSWORD')
            
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Build base URL
        if not self.instance.startswith('https://'):
            if not self.instance.endswith('.service-now.com'):
                self.base_url = f"https://{self.instance}.service-now.com"
            else:
                self.base_url = f"https://{self.instance}"
        else:
            self.base_url = self.instance
        
        # API endpoints
        self.incident_endpoint = f"{self.base_url}/api/now/table/incident"
        
        # Session setup
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_connection(self):
        """Test connection to ServiceNow instance"""
        try:
            # Try to get a single incident to test connection
            response = self.session.get(
                self.incident_endpoint,
                params={'sysparm_limit': 1}
            )
            
            if response.status_code == 200:
                print(f"Successfully connected to ServiceNow: {self.base_url}")
                return True
            else:
                print(f"Connection failed. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False
    
    def create_incident(self, incident_data):
        """Create a new incident in ServiceNow"""
        try:
            # Add timestamp if not present
            if 'opened_at' not in incident_data:
                incident_data['opened_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Make API call to create incident
            response = self.session.post(
                self.incident_endpoint,
                json=incident_data
            )
            
            if response.status_code == 201:
                result = response.json()['result']
                return {
                    'number': result.get('number'),
                    'sys_id': result.get('sys_id'),
                    'priority': result.get('priority'),
                    'state': result.get('state'),
                    'short_description': result.get('short_description')
                }
            else:
                print(f"Failed to create incident. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating incident: {str(e)}")
            return None
    
    def get_incidents(self, filters=None, limit=100):
        """Get incidents from ServiceNow with optional filters"""
        try:
            params = {
                'sysparm_limit': limit,
                'sysparm_offset': 0
            }
            
            if filters:
                # Add filters as query parameters
                if 'priority' in filters:
                    params['priority'] = filters['priority']
                if 'state' in filters:
                    params['state'] = filters['state']
                if 'category' in filters:
                    params['category'] = filters['category']
            
            response = self.session.get(
                self.incident_endpoint,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()['result']
            else:
                print(f"Failed to get incidents. Status: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting incidents: {str(e)}")
            return []

def main():
    """Test the ServiceNow connector"""
    try:
        connector = ServiceNowConnector()
        
        print("Testing ServiceNow Connection...")
        if connector.test_connection():
            print("Connection successful!")
            
            # Test getting recent incidents
            print("\nGetting recent incidents...")
            incidents = connector.get_incidents(limit=5)
            print(f"Found {len(incidents)} incidents")
            
            for incident in incidents[:3]:
                print(f"  • {incident.get('number')} - {incident.get('short_description', 'No description')[:50]}...")
        else:
            print("Connection failed!")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 