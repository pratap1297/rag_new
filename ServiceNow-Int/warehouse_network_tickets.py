#!/usr/bin/env python3
"""
Warehouse Network Issues - ServiceNow Ticket Creation
This script creates and pushes realistic warehouse network and Cisco router connectivity tickets.
"""

from servicenow_connector import ServiceNowConnector
from datetime import datetime
import random

def create_warehouse_network_tickets():
    """Create realistic warehouse network and Cisco router tickets"""
    
    # Warehouse locations
    warehouses = [
        "Dallas Distribution Center", "Chicago Warehouse", "Atlanta Regional Hub",
        "Phoenix Distribution Center", "Seattle Warehouse", "Miami Distribution Hub",
        "Denver Regional Center", "Boston Warehouse", "Los Angeles Distribution",
        "Houston Regional Hub"
    ]
    
    # Network equipment types
    equipment_types = [
        "Cisco ASR 1001-X Router", "Cisco Catalyst 9300 Switch", "Cisco ISR 4331 Router",
        "Cisco Nexus 3548 Switch", "Cisco ASR 920 Router", "Cisco Catalyst 9200 Switch",
        "Cisco ISR 4451 Router", "Cisco Nexus 9000 Switch"
    ]
    
    # Define warehouse network tickets
    warehouse_tickets = [
        {
            'short_description': f'Complete Network Outage - {random.choice(warehouses)}',
            'description': f'''CRITICAL: Complete network connectivity loss at {random.choice(warehouses)}.
            
Issue Details:
- All network services down since {datetime.now().strftime("%H:%M")} today
- Cisco ASR 1001-X primary router not responding to ping
- Secondary router also unreachable
- Warehouse operations completely halted
- Unable to process shipments or receive inventory
- Estimated impact: 500+ employees affected
- Business impact: $50,000+ per hour in lost productivity

Troubleshooting attempted:
- Power cycle of primary router - no response
- Checked physical connections - all appear secure
- Console access attempted - no response
- ISP connectivity verified - working normally

URGENT: Need immediate on-site network engineer dispatch.''',
            'priority': '1',  # Critical
            'urgency': '1',   # High
            'impact': '1',    # High
            'category': 'Network',
            'subcategory': 'Router',
            'caller_id': 'warehouse.manager',
            'assignment_group': 'Network Operations',
            'location': random.choice(warehouses),
            'configuration_item': random.choice(equipment_types)
        },
        
        {
            'short_description': f'Cisco Router Intermittent Connectivity - {random.choice(warehouses)}',
            'description': f'''Intermittent network connectivity issues at {random.choice(warehouses)}.
            
Issue Details:
- Cisco ISR 4331 router experiencing packet loss (15-20%)
- Connection drops every 10-15 minutes
- WMS (Warehouse Management System) timeouts frequent
- Barcode scanners losing connection intermittently
- Pick/pack operations slowed by 40%
- Estimated impact: 150 warehouse staff affected

Network Symptoms:
- Ping tests show 15% packet loss to gateway
- Interface errors increasing on GigabitEthernet0/0/1
- CPU utilization spiking to 85% during drops
- Memory usage at 78% (normally 45%)
- BGP neighbor flapping detected

Business Impact:
- Order fulfillment delays
- Inventory accuracy issues
- Customer shipment delays expected

Requires network engineer review and potential router replacement.''',
            'priority': '2',  # High
            'urgency': '2',   # Medium
            'impact': '2',    # Medium
            'category': 'Network',
            'subcategory': 'Router',
            'caller_id': 'it.support',
            'assignment_group': 'Network Operations',
            'location': random.choice(warehouses),
            'configuration_item': 'Cisco ISR 4331 Router'
        },
        
        {
            'short_description': f'Switch Port Failures - {random.choice(warehouses)}',
            'description': f'''Multiple switch port failures affecting warehouse operations at {random.choice(warehouses)}.
            
Issue Details:
- Cisco Catalyst 9300 switch - 8 ports down in shipping area
- Ports 1/0/12 through 1/0/19 showing error-disabled state
- Shipping stations unable to connect to network
- Handheld scanners in affected area non-functional
- Print servers for shipping labels offline

Affected Systems:
- 6 shipping workstations
- 2 label printers
- 4 handheld barcode scanners
- 1 scale integration system

Error Messages:
- "err-disable" on affected ports
- "Input errors" incrementing rapidly
- "CRC errors" detected on multiple interfaces

Business Impact:
- Shipping department productivity down 60%
- Manual processes required for affected stations
- Potential shipping delays for customer orders

Need immediate switch port diagnostics and potential line card replacement.''',
            'priority': '2',  # High
            'urgency': '2',   # Medium
            'impact': '3',    # Low
            'category': 'Network',
            'subcategory': 'Switch',
            'caller_id': 'shipping.supervisor',
            'assignment_group': 'Network Operations',
            'location': random.choice(warehouses),
            'configuration_item': 'Cisco Catalyst 9300 Switch'
        },
        
        {
            'short_description': f'WAN Link Degradation - {random.choice(warehouses)}',
            'description': f'''WAN link performance degradation between {random.choice(warehouses)} and corporate headquarters.
            
Issue Details:
- Primary MPLS circuit showing high latency (250ms+)
- Normal latency should be <50ms
- Backup internet circuit also experiencing issues
- ERP system synchronization failing
- Real-time inventory updates delayed by 15+ minutes

Network Metrics:
- Bandwidth utilization: 95% (normally 60%)
- Jitter: 45ms (normally <5ms)
- Packet loss: 8% (normally <1%)
- Round-trip time: 280ms (normally 35ms)

Affected Applications:
- SAP ERP system - timeout errors
- Warehouse Management System - sync failures
- Email system - delayed message delivery
- VoIP phones - poor call quality

Business Impact:
- Inventory discrepancies between systems
- Delayed reporting to headquarters
- Communication issues with corporate teams
- Potential compliance reporting delays

ISP escalation required for circuit investigation.''',
            'priority': '2',  # High
            'urgency': '3',   # Low
            'impact': '2',    # Medium
            'category': 'Network',
            'subcategory': 'WAN',
            'caller_id': 'network.admin',
            'assignment_group': 'Network Operations',
            'location': random.choice(warehouses),
            'configuration_item': 'MPLS Circuit'
        },
        
        {
            'short_description': f'WiFi Access Point Failures - {random.choice(warehouses)}',
            'description': f'''Multiple WiFi access points down in warehouse floor at {random.choice(warehouses)}.
            
Issue Details:
- 12 Cisco Aironet access points offline in main warehouse area
- Mobile devices unable to connect to wireless network
- Handheld RF scanners losing connectivity
- Forklift-mounted terminals disconnected
- Warehouse floor coverage reduced by 70%

Affected Areas:
- Receiving dock (4 APs down)
- Main storage aisles (6 APs down)
- Shipping area (2 APs down)
- Break room area (1 AP down - low priority)

Device Impact:
- 45 handheld RF scanners affected
- 12 forklift-mounted terminals
- 25+ mobile devices (phones, tablets)
- Wireless barcode printers in affected zones

Symptoms:
- Power LED indicators off on affected APs
- No response to ping from wireless controller
- Controller showing APs as "down" status
- PoE switch ports showing normal power delivery

Business Impact:
- Mobile workforce productivity severely impacted
- Manual paper-based processes required
- Inventory tracking accuracy compromised
- Safety concerns with forklift navigation systems offline

Requires immediate investigation of wireless infrastructure and potential AP replacement.''',
            'priority': '3',  # Moderate
            'urgency': '2',   # Medium
            'impact': '3',    # Low
            'category': 'Network',
            'subcategory': 'Wireless',
            'caller_id': 'warehouse.operations',
            'assignment_group': 'Network Operations',
            'location': random.choice(warehouses),
            'configuration_item': 'Cisco Aironet Access Points'
        },
        
        {
            'short_description': f'Firewall Configuration Issue - {random.choice(warehouses)}',
            'description': f'''Firewall blocking legitimate warehouse traffic at {random.choice(warehouses)}.
            
Issue Details:
- New security policy blocking WMS database connections
- Warehouse Management System unable to reach database server
- Pick/pack operations halted due to system unavailability
- Error messages indicating "connection refused"

Firewall Details:
- Cisco ASA 5516-X firewall
- Recent security policy update deployed yesterday
- Policy appears to be blocking TCP port 1433 (SQL Server)
- Database server IP: 10.50.100.25
- WMS application servers affected: 10.50.10.15-20

Affected Systems:
- Primary WMS application
- Inventory management system
- Order processing system
- Reporting dashboard

Error Messages:
- "Database connection timeout"
- "Unable to establish connection to SQL Server"
- "Network path not found"

Business Impact:
- All warehouse operations on hold
- Cannot process incoming shipments
- Cannot fulfill customer orders
- Staff idle waiting for system restoration

Requires immediate firewall rule review and correction.''',
            'priority': '1',  # Critical
            'urgency': '1',   # High
            'impact': '1',    # High
            'category': 'Network',
            'subcategory': 'Firewall',
            'caller_id': 'wms.admin',
            'assignment_group': 'Network Security',
            'location': random.choice(warehouses),
            'configuration_item': 'Cisco ASA 5516-X Firewall'
        },
        
        {
            'short_description': f'Network Cable Infrastructure Damage - {random.choice(warehouses)}',
            'description': f'''Physical network cable damage affecting multiple warehouse zones at {random.choice(warehouses)}.
            
Issue Details:
- Forklift accident damaged overhead cable tray
- Multiple Cat6 cables severed in main aisle
- 15+ network drops affected across 3 warehouse zones
- Backup cable paths also compromised

Damage Assessment:
- Primary cable tray: 40% damaged
- Estimated 25 network cables need replacement
- Fiber optic backbone cable also damaged
- Conduit system partially collapsed

Affected Equipment:
- Fixed workstations in damaged zones
- Wall-mounted barcode scanners
- Network printers
- Security cameras in affected area
- Access control card readers

Zones Affected:
- Zone A: Receiving area (8 drops)
- Zone B: Main storage (12 drops)
- Zone C: Quality control (5 drops)

Business Impact:
- Affected zones operating at 30% capacity
- Manual processes required for inventory
- Security system gaps in damaged areas
- Potential safety compliance issues

Requires:
- Emergency cable installation team
- Temporary cable routing
- Infrastructure repair coordination
- Safety assessment of damaged area

Estimated repair time: 2-3 days for full restoration.''',
            'priority': '2',  # High
            'urgency': '2',   # Medium
            'impact': '2',    # Medium
            'category': 'Network',
            'subcategory': 'Infrastructure',
            'caller_id': 'facilities.manager',
            'assignment_group': 'Network Infrastructure',
            'location': random.choice(warehouses),
            'configuration_item': 'Network Cabling Infrastructure'
        },
        
        {
            'short_description': f'DHCP Server Failure - {random.choice(warehouses)}',
            'description': f'''DHCP server failure causing IP address assignment issues at {random.choice(warehouses)}.
            
Issue Details:
- Primary DHCP server (Windows Server 2019) unresponsive
- New devices unable to obtain IP addresses
- Existing leases expiring without renewal
- Mobile devices losing network connectivity as leases expire

Server Details:
- Primary DHCP: 10.50.1.10 (DOWN)
- Secondary DHCP: 10.50.1.11 (responding slowly)
- DHCP scope: 10.50.100.0/24 (warehouse devices)
- Lease duration: 8 hours

Affected Device Types:
- Handheld RF scanners (30+ devices)
- Tablet computers (15 devices)
- Wireless printers (8 devices)
- Mobile workstations (12 devices)
- Guest devices (variable)

Symptoms:
- "Unable to obtain IP address" errors
- Devices showing 169.254.x.x addresses (APIPA)
- Intermittent connectivity as devices lose leases
- New device deployments failing

Business Impact:
- Mobile workforce productivity declining
- New equipment deployment on hold
- Visitor/contractor device access unavailable
- Potential for complete mobile device outage as leases expire

Immediate Actions Required:
- Investigate primary DHCP server failure
- Optimize secondary DHCP server performance
- Consider emergency DHCP scope expansion
- Plan for server replacement if hardware failure confirmed

Timeline: Critical - must resolve within 4 hours before mass lease expiration.''',
            'priority': '2',  # High
            'urgency': '1',   # High
            'impact': '2',    # Medium
            'category': 'Network',
            'subcategory': 'DHCP',
            'caller_id': 'network.admin',
            'assignment_group': 'Network Operations',
            'location': random.choice(warehouses),
            'configuration_item': 'DHCP Server'
        }
    ]
    
    return warehouse_tickets

def push_warehouse_tickets():
    """Push warehouse network tickets to ServiceNow"""
    print("🏭 WAREHOUSE NETWORK ISSUES - SERVICENOW TICKET CREATION")
    print("=" * 70)
    
    # Initialize ServiceNow connector
    try:
        sn = ServiceNowConnector()
        
        # Test connection
        print("Testing ServiceNow connection...")
        if not sn.test_connection():
            print("❌ Failed to connect to ServiceNow")
            return
        
        print("✅ Connected to ServiceNow successfully!")
        
        # Create warehouse tickets
        warehouse_tickets = create_warehouse_network_tickets()
        
        print(f"\n🎫 Creating {len(warehouse_tickets)} warehouse network tickets...")
        print("-" * 70)
        
        created_tickets = []
        for i, ticket in enumerate(warehouse_tickets, 1):
            print(f"\n📋 Creating Ticket {i}/{len(warehouse_tickets)}")
            print(f"   Title: {ticket['short_description']}")
            print(f"   Priority: {ticket['priority']} ({'Critical' if ticket['priority']=='1' else 'High' if ticket['priority']=='2' else 'Moderate'})")
            print(f"   Location: {ticket.get('location', 'N/A')}")
            print(f"   Equipment: {ticket.get('configuration_item', 'N/A')}")
            
            result = sn.create_incident(ticket)
            if result:
                created_tickets.append(result)
                print(f"   ✅ Created: {result['number']}")
            else:
                print(f"   ❌ Failed to create ticket")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 WAREHOUSE NETWORK TICKETS CREATION SUMMARY")
        print("=" * 70)
        print(f"✅ Successfully created: {len(created_tickets)} tickets")
        print(f"❌ Failed to create: {len(warehouse_tickets) - len(created_tickets)} tickets")
        
        if created_tickets:
            print("\n📋 Created Tickets:")
            for ticket in created_tickets:
                priority_text = "🔴 CRITICAL" if ticket.get('priority') == '1' else "🟠 HIGH" if ticket.get('priority') == '2' else "🟡 MODERATE"
                print(f"   {ticket['number']}: {ticket['short_description'][:60]}... [{priority_text}]")
        
        print(f"\n🎯 All warehouse network tickets have been pushed to ServiceNow!")
        print("You can now view and manage these tickets in your ServiceNow instance.")
        
        return created_tickets
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    """Main function"""
    created_tickets = push_warehouse_tickets()
    
    if created_tickets:
        print(f"\n🔍 Want to verify? Run this command to pull the tickets:")
        print("python backend/ServiceNow-Int/push_pull_tickets.py")

if __name__ == "__main__":
    main() 