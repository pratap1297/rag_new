#!/usr/bin/env python3
"""
Simple ServiceNow Push/Pull Tickets Script
This script demonstrates the core functionality:
1. Push tickets to ServiceNow
2. Pull tickets from ServiceNow based on key values
"""

from servicenow_connector import ServiceNowConnector

def push_tickets():
    """Push sample tickets to ServiceNow"""
    print("🚀 PUSHING TICKETS TO SERVICENOW")
    print("-" * 50)
    
    # Initialize connector
    sn = ServiceNowConnector()
    
    # Test connection first
    if not sn.test_connection():
        print("❌ Failed to connect to ServiceNow")
        return []
    
    # Define tickets to push
    tickets_to_push = [
        {
            'short_description': 'Production API Gateway Down',
            'description': 'The main API gateway is not responding, affecting all external integrations.',
            'priority': '1',  # Critical
            'category': 'Network',
            'subcategory': 'Gateway'
        },
        {
            'short_description': 'User Login Issues',
            'description': 'Multiple users reporting they cannot log into the system.',
            'priority': '2',  # High
            'category': 'Software',
            'subcategory': 'Authentication'
        },
        {
            'short_description': 'Backup Job Failed',
            'description': 'Nightly backup job failed with error code 500.',
            'priority': '3',  # Moderate
            'category': 'System',
            'subcategory': 'Backup'
        }
    ]
    
    # Push tickets
    print(f"Pushing {len(tickets_to_push)} tickets...")
    created_tickets = sn.bulk_create_incidents(tickets_to_push)
    
    print(f"\n✅ Successfully pushed {len(created_tickets)} tickets:")
    for ticket in created_tickets:
        print(f"  📋 {ticket['number']}: {ticket['short_description']}")
    
    return created_tickets

def pull_tickets():
    """Pull tickets from ServiceNow using various filters"""
    print("\n📥 PULLING TICKETS FROM SERVICENOW")
    print("-" * 50)
    
    # Initialize connector
    sn = ServiceNowConnector()
    
    # Example 1: Pull all critical tickets (Priority 1)
    print("1️⃣ Pulling CRITICAL tickets (Priority = 1):")
    critical_tickets = sn.get_incidents_by_priority('1')
    print(f"   Found {len(critical_tickets)} critical tickets")
    for ticket in critical_tickets[:3]:  # Show first 3
        print(f"   📋 {ticket['number']}: {ticket['short_description']}")
    
    # Example 2: Pull tickets by category
    print("\n2️⃣ Pulling NETWORK-related tickets:")
    network_tickets = sn.get_incidents(filters={'category': 'Network'})
    print(f"   Found {len(network_tickets)} network tickets")
    for ticket in network_tickets[:3]:  # Show first 3
        print(f"   📋 {ticket['number']}: {ticket['short_description']}")
    
    # Example 3: Pull new tickets (State 1)
    print("\n3️⃣ Pulling NEW tickets (State = 1):")
    new_tickets = sn.get_incidents_by_state('1')
    print(f"   Found {len(new_tickets)} new tickets")
    for ticket in new_tickets[:3]:  # Show first 3
        print(f"   📋 {ticket['number']}: {ticket['short_description']}")
    
    # Example 4: Pull tickets with multiple criteria
    print("\n4️⃣ Pulling HIGH PRIORITY SOFTWARE tickets:")
    complex_filter = {
        'priority': ['1', '2'],  # Critical or High
        'category': 'Software'
    }
    filtered_tickets = sn.get_incidents(filters=complex_filter)
    print(f"   Found {len(filtered_tickets)} high priority software tickets")
    for ticket in filtered_tickets[:3]:  # Show first 3
        print(f"   📋 {ticket['number']}: {ticket['short_description']}")
    
    return {
        'critical': critical_tickets,
        'network': network_tickets,
        'new': new_tickets,
        'high_priority_software': filtered_tickets
    }

def pull_specific_ticket(ticket_number):
    """Pull a specific ticket by its number"""
    print(f"\n🔍 PULLING SPECIFIC TICKET: {ticket_number}")
    print("-" * 50)
    
    sn = ServiceNowConnector()
    ticket = sn.get_incident_by_number(ticket_number)
    
    if ticket:
        print("✅ Ticket found:")
        print(f"   Number: {ticket['number']}")
        print(f"   Description: {ticket['short_description']}")
        print(f"   Priority: {ticket['priority']}")
        print(f"   State: {ticket['state']}")
        print(f"   Created: {ticket['sys_created_on']}")
        return ticket
    else:
        print(f"❌ Ticket {ticket_number} not found")
        return None

def main():
    """Main function to demonstrate push/pull operations"""
    print("ServiceNow Push/Pull Tickets Demo")
    print("=" * 60)
    
    try:
        # Step 1: Push tickets
        pushed_tickets = push_tickets()
        
        # Step 2: Pull tickets with various filters
        pulled_tickets = pull_tickets()
        
        # Step 3: Pull a specific ticket (if we created any)
        if pushed_tickets:
            first_ticket_number = pushed_tickets[0]['number']
            specific_ticket = pull_specific_ticket(first_ticket_number)
        
        # Summary
        print("\n📊 SUMMARY")
        print("-" * 50)
        print(f"✅ Pushed: {len(pushed_tickets)} tickets")
        print(f"📥 Pulled Critical: {len(pulled_tickets['critical'])} tickets")
        print(f"📥 Pulled Network: {len(pulled_tickets['network'])} tickets")
        print(f"📥 Pulled New: {len(pulled_tickets['new'])} tickets")
        print(f"📥 Pulled High Priority Software: {len(pulled_tickets['high_priority_software'])} tickets")
        
        print("\n🎉 Push/Pull operations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with your ServiceNow credentials")
        print("2. Installed required packages: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 