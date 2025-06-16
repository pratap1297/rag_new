import os
import sys
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
root_env_path = Path(__file__).parent.parent.parent / '.env'
if root_env_path.exists():
    load_dotenv(root_env_path)

from servicenow_connector import ServiceNowConnector

class WarehouseNetworkTicketGenerator:
    def __init__(self):
        self.connector = ServiceNowConnector()
        
        self.warehouses = [
            "Distribution Center North - Chicago, IL",
            "Fulfillment Center East - Atlanta, GA", 
            "Regional Warehouse West - Phoenix, AZ",
            "Central Distribution Hub - Dallas, TX",
            "Logistics Center South - Miami, FL",
            "Processing Facility - Denver, CO"
        ]
        
        self.cisco_models = [
            "Cisco ISR 4331", "Cisco ISR 4351", "Cisco ISR 4431",
            "Cisco ASR 1001-X", "Cisco ISR 1100-4G", "Cisco ISR 900 Series",
            "Cisco Catalyst 8300", "Cisco ISR 4321"
        ]
        
        self.network_issues = [
            {
                "type": "connectivity",
                "short_desc": "Cisco router connectivity failure",
                "symptoms": ["intermittent connection drops", "high packet loss", "timeout errors"]
            },
            {
                "type": "performance",
                "short_desc": "Network performance degradation", 
                "symptoms": ["slow data transfer", "high latency", "bandwidth bottleneck"]
            },
            {
                "type": "routing",
                "short_desc": "Routing protocol issues",
                "symptoms": ["route flapping", "convergence delays", "unreachable networks"]
            },
            {
                "type": "hardware",
                "short_desc": "Router hardware malfunction",
                "symptoms": ["device overheating", "memory errors", "interface failures"]
            }
        ]
        
        self.business_impacts = [
            "Warehouse operations halted - unable to process shipments",
            "Inventory management system offline - stock tracking disabled", 
            "Barcode scanners disconnected - manual processing required",
            "WMS (Warehouse Management System) inaccessible",
            "RFID tracking system down - package visibility lost"
        ]
    
    def generate_ticket_data(self, priority="2"):
        warehouse = random.choice(self.warehouses)
        cisco_model = random.choice(self.cisco_models)
        issue = random.choice(self.network_issues)
        business_impact = random.choice(self.business_impacts)
        
        subnet = f"10.{random.randint(1, 254)}.{random.randint(1, 254)}"
        router_ip = f"{subnet}.1"
        hostname = f"WH-RTR-{warehouse.split()[0][:3].upper()}-{random.randint(1, 99):02d}"
        
        description = f"""INCIDENT SUMMARY:
Network connectivity issues affecting {cisco_model} router in {warehouse}.

AFFECTED EQUIPMENT:
- Device: {cisco_model}
- Hostname: {hostname}
- Management IP: {router_ip}
- Location: {warehouse}

BUSINESS IMPACT:
{business_impact}

SYMPTOMS OBSERVED:
{' | '.join(random.sample(issue['symptoms'], random.randint(2, 3)))}

TROUBLESHOOTING PERFORMED:
• Verified physical connections and cable integrity
• Checked device status via console connection
• Reviewed system logs for error messages
• Tested connectivity from multiple source points

PRIORITY JUSTIFICATION:
{self._get_priority_justification(priority)}"""
        
        ticket_data = {
            "short_description": f"{issue['short_desc']} - {cisco_model} at {warehouse.split('-')[0].strip()}",
            "description": description.strip(),
            "priority": priority,
            "category": "Network",
            "subcategory": "Router",
            "state": "1",
            "location": warehouse,
            "business_service": "Warehouse Operations",
            "cmdb_ci": hostname,
            "assignment_group": "Network Operations"
        }
        
        return ticket_data
    
    def _get_priority_justification(self, priority):
        justifications = {
            "1": "CRITICAL - Complete warehouse operations shutdown. Revenue impact >$10K/hour.",
            "2": "HIGH - Significant operational impact. Multiple systems affected.",
            "3": "MODERATE - Partial service degradation. Workarounds available.", 
            "4": "LOW - Minor impact. Normal business operations continue."
        }
        return justifications.get(priority, justifications["3"])
    
    def create_sample_tickets(self, count=5):
        print(f"Creating {count} sample warehouse network tickets...")
        print("=" * 60)
        
        if not self.connector.test_connection():
            print("ServiceNow connection failed. Please check your credentials.")
            return []
        
        created_tickets = []
        priorities = ["1"] * 2 + ["2"] * 3 + ["3"] * 2 + ["4"] * 1
        
        for i in range(count):
            try:
                priority = priorities[i % len(priorities)] if i < len(priorities) else random.choice(["2", "3"])
                
                print(f"\nCreating ticket {i+1}/{count} (Priority {priority})...")
                
                ticket_data = self.generate_ticket_data(priority=priority)
                result = self.connector.create_incident(ticket_data)
                
                if result:
                    created_tickets.append(result)
                    priority_label = {"1": "Critical", "2": "High", "3": "Moderate", "4": "Low"}
                    print(f"Created: {result['number']} - {priority_label.get(priority, 'Unknown')} Priority")
                    print(f"   Location: {ticket_data['location']}")
                    print(f"   Equipment: {ticket_data['cmdb_ci']}")
                else:
                    print(f"Failed to create ticket {i+1}")
                    
            except Exception as e:
                print(f"Error creating ticket {i+1}: {str(e)}")
                continue
        
        print(f"\nSummary: Successfully created {len(created_tickets)}/{count} tickets")
        
        if created_tickets:
            print("\nCreated Tickets:")
            for ticket in created_tickets:
                print(f"   • {ticket['number']} - Priority {ticket.get('priority', 'Unknown')}")
        
        return created_tickets

def main():
    print("Warehouse Network Incident Generator for ServiceNow")
    print("=" * 60)
    
    generator = WarehouseNetworkTicketGenerator()
    
    print("\nSelect an option:")
    print("1. Create 5 random warehouse network tickets")
    print("2. Create 10 random warehouse network tickets") 
    print("3. Create custom number of tickets")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            generator.create_sample_tickets(5)
        elif choice == "2":
            generator.create_sample_tickets(10)
        elif choice == "3":
            count = int(input("Enter number of tickets to create: "))
            generator.create_sample_tickets(count)
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
