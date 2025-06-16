#!/usr/bin/env python3
"""
Demo: Warehouse Network Ticket Creation
Shows what tickets would be created for ServiceNow without requiring actual credentials.
"""

import random
from datetime import datetime, timedelta

class DemoWarehouseNetworkTicketGenerator:
    """Demo version that shows ticket data without creating actual ServiceNow tickets"""
    
    def __init__(self):
        # Warehouse locations
        self.warehouses = [
            "Distribution Center North - Chicago, IL",
            "Fulfillment Center East - Atlanta, GA", 
            "Regional Warehouse West - Phoenix, AZ",
            "Central Distribution Hub - Dallas, TX",
            "Logistics Center South - Miami, FL",
            "Processing Facility - Denver, CO"
        ]
        
        # Cisco router models commonly used in warehouses
        self.cisco_models = [
            "Cisco ISR 4331", "Cisco ISR 4351", "Cisco ISR 4431",
            "Cisco ASR 1001-X", "Cisco ISR 1100-4G", "Cisco ISR 900 Series",
            "Cisco Catalyst 8300", "Cisco ISR 4321"
        ]
        
        # Network issues common in warehouse environments
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
            },
            {
                "type": "security",
                "short_desc": "Network security incident",
                "symptoms": ["unauthorized access attempts", "suspicious traffic", "firewall alerts"]
            }
        ]
        
        # Business impact scenarios
        self.business_impacts = [
            "Warehouse operations halted - unable to process shipments",
            "Inventory management system offline - stock tracking disabled", 
            "Barcode scanners disconnected - manual processing required",
            "WMS (Warehouse Management System) inaccessible",
            "RFID tracking system down - package visibility lost",
            "Automated sorting system offline - manual sorting required",
            "Loading dock systems disconnected - shipping delays",
            "Temperature monitoring system offline - cold storage at risk"
        ]
    
    def generate_ticket_data(self, priority="2", category="Network"):
        """Generate realistic ticket data"""
        
        # Select random components
        warehouse = random.choice(self.warehouses)
        cisco_model = random.choice(self.cisco_models)
        issue = random.choice(self.network_issues)
        business_impact = random.choice(self.business_impacts)
        
        # Generate IP addresses and hostnames
        subnet = f"10.{random.randint(1, 254)}.{random.randint(1, 254)}"
        router_ip = f"{subnet}.1"
        hostname = f"WH-RTR-{warehouse.split()[0][:3].upper()}-{random.randint(1, 99):02d}"
        
        # Create detailed description
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
        
        # Create ticket data
        ticket_data = {
            "short_description": f"{issue['short_desc']} - {cisco_model} at {warehouse.split('-')[0].strip()}",
            "description": description.strip(),
            "priority": priority,
            "category": category,
            "subcategory": "Router",
            "state": "1",  # New
            "location": warehouse,
            "business_service": "Warehouse Operations",
            "cmdb_ci": hostname,
            "assignment_group": "Network Operations"
        }
        
        return ticket_data
    
    def _get_priority_justification(self, priority):
        """Get priority justification text"""
        justifications = {
            "1": "CRITICAL - Complete warehouse operations shutdown. Revenue impact >$10K/hour.",
            "2": "HIGH - Significant operational impact. Multiple systems affected.",
            "3": "MODERATE - Partial service degradation. Workarounds available.", 
            "4": "LOW - Minor impact. Normal business operations continue."
        }
        return justifications.get(priority, justifications["3"])
    
    def demo_sample_tickets(self, count=5):
        """Demo: Show what tickets would be created"""
        
        print(f"DEMO: Showing {count} sample warehouse network tickets that would be created")
        print("=" * 80)
        
        created_tickets = []
        
        # Priority distribution (more high/critical for realism)
        priorities = ["1"] * 2 + ["2"] * 3 + ["3"] * 2 + ["4"] * 1
        
        for i in range(count):
            # Select priority
            priority = priorities[i % len(priorities)] if i < len(priorities) else random.choice(["2", "3"])
            
            print(f"\nTICKET {i+1}/{count} (Priority {priority}):")
            print("-" * 50)
            
            # Generate ticket data
            ticket_data = self.generate_ticket_data(priority=priority)
            
            # Simulate ticket creation
            mock_ticket_number = f"INC{random.randint(1000000, 9999999)}"
            
            created_tickets.append({
                'number': mock_ticket_number,
                'priority': priority,
                'short_description': ticket_data['short_description']
            })
            
            priority_label = {"1": "Critical", "2": "High", "3": "Moderate", "4": "Low"}
            
            print(f"Title: {ticket_data['short_description']}")
            print(f"Priority: {priority_label.get(priority, 'Unknown')}")
            print(f"Location: {ticket_data['location']}")
            print(f"Equipment: {ticket_data['cmdb_ci']}")
            print(f"Category: {ticket_data['category']} > {ticket_data['subcategory']}")
            print(f"Assigned to: {ticket_data['assignment_group']}")
            print(f"Would create ticket: {mock_ticket_number}")
            
            # Show partial description
            desc_lines = ticket_data['description'].split('\n')
            print(f"\nDescription Preview:")
            for line in desc_lines[:8]:  # Show first 8 lines
                print(f"   {line}")
            if len(desc_lines) > 8:
                print(f"   ... ({len(desc_lines) - 8} more lines)")
        
        print(f"\nDEMO SUMMARY:")
        print(f"   Would create {len(created_tickets)} tickets in ServiceNow")
        print(f"\nTickets by Priority:")
        
        priority_counts = {}
        for ticket in created_tickets:
            p = ticket['priority']
            priority_counts[p] = priority_counts.get(p, 0) + 1
        
        priority_labels = {"1": "Critical", "2": "High", "3": "Moderate", "4": "Low"}
        for priority, count in sorted(priority_counts.items()):
            print(f"   {priority_labels.get(priority, priority)}: {count} tickets")
        
        print(f"\nAll Ticket Numbers:")
        for ticket in created_tickets:
            print(f"   • {ticket['number']} - {ticket['short_description'][:60]}...")
        
        return created_tickets

def main():
    """Main demo function"""
    print("DEMO: Warehouse Network Incident Generator for ServiceNow")
    print("=" * 80)
    print("This demo shows what tickets would be created without requiring ServiceNow credentials.")
    print()
    
    generator = DemoWarehouseNetworkTicketGenerator()
    
    # Menu options
    print("Select a demo option:")
    print("1. Demo: 5 random warehouse network tickets")
    print("2. Demo: 10 random warehouse network tickets") 
    print("3. Demo: Custom number of tickets")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            generator.demo_sample_tickets(5)
        elif choice == "2":
            generator.demo_sample_tickets(10)
        elif choice == "3":
            count = int(input("Enter number of tickets to demo: "))
            generator.demo_sample_tickets(count)
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nDemo cancelled by user")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 