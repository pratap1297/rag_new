#!/usr/bin/env python3
"""
ServiceNow Integration Example
This script demonstrates how to:
1. Connect to ServiceNow
2. Push (create) tickets
3. Pull (retrieve) tickets with various filters
"""

from servicenow_connector import ServiceNowConnector
import json
from datetime import datetime

def print_separator(title):
    """Print a formatted separator for better output readability"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_incident_summary(incident):
    """Print a formatted summary of an incident"""
    print(f"Number: {incident.get('number', 'N/A')}")
    print(f"Short Description: {incident.get('short_description', 'N/A')}")
    print(f"Priority: {incident.get('priority', 'N/A')} ({get_priority_text(incident.get('priority', '0'))})")
    print(f"State: {incident.get('state', 'N/A')} ({get_state_text(incident.get('state', '0'))})")
    print(f"Created: {incident.get('sys_created_on', 'N/A')}")
    print(f"Sys ID: {incident.get('sys_id', 'N/A')}")
    print("-" * 40)

def get_priority_text(priority):
    """Convert priority number to text"""
    priority_map = {
        '1': 'Critical',
        '2': 'High', 
        '3': 'Moderate',
        '4': 'Low',
        '5': 'Planning'
    }
    return priority_map.get(priority, 'Unknown')

def get_state_text(state):
    """Convert state number to text"""
    state_map = {
        '1': 'New',
        '2': 'In Progress',
        '3': 'On Hold',
        '6': 'Resolved',
        '7': 'Closed'
    }
    return state_map.get(state, 'Unknown')

def create_sample_tickets(sn_connector):
    """Create sample tickets in ServiceNow"""
    print_separator("CREATING SAMPLE TICKETS")
    
    # Define sample incidents with different priorities and categories
    sample_incidents = [
        {
            'short_description': 'Critical Database Server Outage',
            'description': 'Primary database server is completely down. All applications are affected. Users cannot access any systems.',
            'priority': '1',  # Critical
            'urgency': '1',   # High
            'impact': '1',    # High
            'category': 'Hardware',
            'subcategory': 'Database',
            'caller_id': 'admin',
            'assignment_group': 'Database Team'
        },
        {
            'short_description': 'Email Service Performance Issues',
            'description': 'Users are reporting slow email response times and intermittent connection issues with the email server.',
            'priority': '2',  # High
            'urgency': '2',   # Medium
            'impact': '2',    # Medium
            'category': 'Software',
            'subcategory': 'Email',
            'caller_id': 'user1',
            'assignment_group': 'IT Support'
        },
        {
            'short_description': 'Printer Not Working in Conference Room A',
            'description': 'The network printer in Conference Room A is not responding. Users cannot print documents for meetings.',
            'priority': '3',  # Moderate
            'urgency': '3',   # Low
            'impact': '3',    # Low
            'category': 'Hardware',
            'subcategory': 'Printer',
            'caller_id': 'user2',
            'assignment_group': 'Hardware Support'
        },
        {
            'short_description': 'Password Reset Request',
            'description': 'User account locked due to multiple failed login attempts. User needs password reset to regain access.',
            'priority': '4',  # Low
            'urgency': '3',   # Low
            'impact': '4',    # Low
            'category': 'Access',
            'subcategory': 'Password',
            'caller_id': 'user3',
            'assignment_group': 'Service Desk'
        },
        {
            'short_description': 'Software License Renewal Planning',
            'description': 'Annual software license renewal is due in 3 months. Need to plan and budget for renewal.',
            'priority': '5',  # Planning
            'urgency': '4',   # Low
            'impact': '4',    # Low
            'category': 'Software',
            'subcategory': 'License',
            'caller_id': 'admin',
            'assignment_group': 'IT Management'
        }
    ]
    
    print(f"Creating {len(sample_incidents)} sample incidents...")
    created_incidents = sn_connector.bulk_create_incidents(sample_incidents)
    
    print(f"\nSuccessfully created {len(created_incidents)} incidents:")
    for incident in created_incidents:
        print(f"- {incident['number']}: {incident['short_description']}")
    
    return created_incidents

def retrieve_tickets_examples(sn_connector):
    """Demonstrate various ways to retrieve tickets"""
    
    # Example 1: Get all incidents (limited)
    print_separator("RETRIEVING ALL INCIDENTS (Limited to 10)")
    all_incidents = sn_connector.get_incidents(limit=10)
    print(f"Found {len(all_incidents)} incidents:")
    for incident in all_incidents[:5]:  # Show first 5
        print_incident_summary(incident)
    
    # Example 2: Get incidents by priority
    print_separator("RETRIEVING CRITICAL INCIDENTS (Priority 1)")
    critical_incidents = sn_connector.get_incidents_by_priority('1')
    print(f"Found {len(critical_incidents)} critical incidents:")
    for incident in critical_incidents:
        print_incident_summary(incident)
    
    # Example 3: Get incidents by state
    print_separator("RETRIEVING NEW INCIDENTS (State 1)")
    new_incidents = sn_connector.get_incidents_by_state('1')
    print(f"Found {len(new_incidents)} new incidents:")
    for incident in new_incidents[:3]:  # Show first 3
        print_incident_summary(incident)
    
    # Example 4: Get incidents with custom filters
    print_separator("RETRIEVING HARDWARE-RELATED HIGH PRIORITY INCIDENTS")
    custom_filters = {
        'category': 'Hardware',
        'priority': ['1', '2']  # Critical or High priority
    }
    filtered_incidents = sn_connector.get_incidents(filters=custom_filters)
    print(f"Found {len(filtered_incidents)} hardware-related high priority incidents:")
    for incident in filtered_incidents:
        print_incident_summary(incident)
    
    # Example 5: Get incidents by multiple states
    print_separator("RETRIEVING ACTIVE INCIDENTS (New or In Progress)")
    active_filters = {
        'state': ['1', '2']  # New or In Progress
    }
    active_incidents = sn_connector.get_incidents(filters=active_filters)
    print(f"Found {len(active_incidents)} active incidents:")
    for incident in active_incidents[:5]:  # Show first 5
        print_incident_summary(incident)

def search_specific_ticket(sn_connector, ticket_number=None):
    """Search for a specific ticket by number"""
    if not ticket_number:
        print_separator("SEARCHING FOR SPECIFIC TICKET")
        print("No ticket number provided. Skipping specific ticket search.")
        return
    
    print_separator(f"SEARCHING FOR TICKET: {ticket_number}")
    incident = sn_connector.get_incident_by_number(ticket_number)
    
    if incident:
        print("Ticket found:")
        print_incident_summary(incident)
        
        # Show full details
        print("\nFull ticket details:")
        print(json.dumps(incident, indent=2))
    else:
        print(f"Ticket {ticket_number} not found.")

def demonstrate_advanced_queries(sn_connector):
    """Demonstrate advanced query capabilities"""
    print_separator("ADVANCED QUERY EXAMPLES")
    
    # Query 1: Recent incidents (created today)
    print("1. Getting recent incidents...")
    today = datetime.now().strftime('%Y-%m-%d')
    recent_filters = {
        'sys_created_on': f'>={today}'
    }
    recent_incidents = sn_connector.get_incidents(filters=recent_filters, limit=5)
    print(f"Found {len(recent_incidents)} incidents created today")
    
    # Query 2: High impact incidents
    print("\n2. Getting high impact incidents...")
    high_impact_filters = {
        'impact': ['1', '2']  # High or Medium impact
    }
    high_impact_incidents = sn_connector.get_incidents(filters=high_impact_filters, limit=5)
    print(f"Found {len(high_impact_incidents)} high impact incidents")
    
    # Query 3: Software-related incidents
    print("\n3. Getting software-related incidents...")
    software_filters = {
        'category': 'Software'
    }
    software_incidents = sn_connector.get_incidents(filters=software_filters, limit=5)
    print(f"Found {len(software_incidents)} software-related incidents")
    
    for incident in software_incidents[:2]:  # Show first 2
        print_incident_summary(incident)

def main():
    """Main function to demonstrate ServiceNow integration"""
    print("ServiceNow Integration Demo")
    print("=" * 60)
    
    try:
        # Initialize ServiceNow connector
        print("Initializing ServiceNow connector...")
        sn = ServiceNowConnector()
        
        # Test connection
        print("Testing connection to ServiceNow...")
        if not sn.test_connection():
            print("❌ Failed to connect to ServiceNow. Please check your credentials and instance URL.")
            return
        
        print("✅ Successfully connected to ServiceNow!")
        
        # Create sample tickets
        created_incidents = create_sample_tickets(sn)
        
        # Wait a moment for tickets to be processed
        import time
        print("\nWaiting 2 seconds for tickets to be processed...")
        time.sleep(2)
        
        # Retrieve tickets with various methods
        retrieve_tickets_examples(sn)
        
        # Search for a specific ticket (use the first created ticket if available)
        if created_incidents:
            first_ticket_number = created_incidents[0]['number']
            search_specific_ticket(sn, first_ticket_number)
        
        # Demonstrate advanced queries
        demonstrate_advanced_queries(sn)
        
        print_separator("DEMO COMPLETED SUCCESSFULLY")
        print("✅ ServiceNow integration demo completed successfully!")
        print("\nSummary:")
        print(f"- Created {len(created_incidents)} sample tickets")
        print("- Demonstrated various retrieval methods")
        print("- Showed filtering and search capabilities")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file with your ServiceNow credentials")
        print("2. Set SERVICENOW_INSTANCE, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("Please check your ServiceNow configuration and network connectivity.")

if __name__ == "__main__":
    main() 