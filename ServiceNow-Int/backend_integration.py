#!/usr/bin/env python3
"""
Backend Integration for ServiceNow Scheduler
Integrates ServiceNow incident data with the Router Rescue AI backend system.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from current directory and root
load_dotenv()
root_env_path = Path(__file__).parent.parent.parent / '.env'
if root_env_path.exists():
    load_dotenv(root_env_path)

from servicenow_scheduler import ServiceNowScheduler, IncidentData

class BackendIntegration:
    """Integration class for connecting ServiceNow with Router Rescue AI backend"""
    
    def __init__(self, backend_url: str = None):
        """Initialize the backend integration"""
        self.backend_url = backend_url or os.getenv('BACKEND_URL', 'http://localhost:8000')
        self.scheduler = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Network-related keywords for filtering
        self.network_keywords = [
            'network', 'router', 'switch', 'firewall', 'vpn', 'bgp', 'ospf', 'vlan',
            'ethernet', 'wifi', 'wireless', 'lan', 'wan', 'dns', 'dhcp', 'tcp',
            'ip', 'subnet', 'gateway', 'ping', 'traceroute', 'bandwidth',
            'latency', 'packet', 'cisco', 'juniper', 'arista', 'fortinet'
        ]
        
        self.logger.info("Backend Integration initialized")
    
    def is_network_related(self, incident: IncidentData) -> bool:
        """Check if incident is network-related"""
        text_to_check = (
            incident.short_description.lower() + " " +
            incident.description.lower() + " " +
            incident.category.lower() + " " +
            incident.configuration_item.lower()
        )
        
        return any(keyword in text_to_check for keyword in self.network_keywords)
    
    def format_incident_for_backend(self, incident: IncidentData) -> Dict[str, Any]:
        """Format incident data for backend processing"""
        document_content = f"""
Incident Number: {incident.number}
Priority: {incident.priority_label} ({incident.priority})
State: {incident.state_label} ({incident.state})
Category: {incident.category}

Short Description:
{incident.short_description}

Description:
{incident.description}

Configuration Item: {incident.configuration_item}
Assigned To: {incident.assigned_to_name}
Created: {incident.created_on}
Updated: {incident.updated_on}
"""
        
        return {
            'filename': f"servicenow_incident_{incident.number}.txt",
            'content': document_content,
            'metadata': {
                'source': 'ServiceNow',
                'incident_number': incident.number,
                'priority': incident.priority,
                'state': incident.state,
                'category': incident.category,
                'is_network_related': self.is_network_related(incident)
            }
        }
    
    async def send_incident_to_backend(self, incident: IncidentData) -> bool:
        """Send incident to backend for processing"""
        try:
            formatted_incident = self.format_incident_for_backend(incident)
            
            url = f"{self.backend_url}/api/documents/upload"
            
            files = {
                'file': (
                    formatted_incident['filename'],
                    formatted_incident['content'].encode('utf-8'),
                    'text/plain'
                )
            }
            
            data = {
                'metadata': json.dumps(formatted_incident['metadata'])
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"Successfully sent incident {incident.number} to backend")
                return True
            else:
                self.logger.error(f"Failed to send incident {incident.number}: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending incident {incident.number}: {str(e)}")
            return False
    
    def incident_callback(self, incidents: List[IncidentData]):
        """Callback function for processing incidents from scheduler"""
        try:
            # Filter for network-related incidents
            network_incidents = [inc for inc in incidents if self.is_network_related(inc)]
            
            if network_incidents:
                self.logger.info(f"Found {len(network_incidents)} network-related incidents")
                
                # Process incidents synchronously for simplicity
                for incident in network_incidents:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.send_incident_to_backend(incident))
                    loop.close()
            
        except Exception as e:
            self.logger.error(f"Error in incident callback: {str(e)}")
    
    def start_integration(self, config: Dict[str, Any] = None):
        """Start the ServiceNow integration"""
        self.logger.info("Starting ServiceNow integration...")
        
        self.scheduler = ServiceNowScheduler(config)
        self.scheduler.add_incident_callback(self.incident_callback)
        self.scheduler.start_scheduler()
        
        self.logger.info("ServiceNow integration started successfully")
    
    def stop_integration(self):
        """Stop the ServiceNow integration"""
        if self.scheduler:
            self.scheduler.stop_scheduler()
            self.logger.info("ServiceNow integration stopped")

# Main execution
if __name__ == "__main__":
    integration = BackendIntegration()
    
    try:
        integration.start_integration()
        
        # Keep running
        while True:
            import time
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("Shutting down integration...")
        integration.stop_integration() 