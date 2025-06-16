#!/usr/bin/env python3
"""
Check ServiceNow Incidents Count
Simple script to check how many incidents are currently in ServiceNow
"""

import os
import sys
from dotenv import load_dotenv
from servicenow_connector import ServiceNowConnector

def main():
    # Load environment variables
    load_dotenv()
    
    print("🔍 Checking ServiceNow Incidents...")
    print("=" * 50)
    
    # Initialize connector
    try:
        sn = ServiceNowConnector()
        
        # Test connection first
        print("📡 Testing connection to ServiceNow...")
        if not sn.test_connection():
            print("❌ Failed to connect to ServiceNow")
            return
        
        print("✅ Connection successful!")
        print()
        
        # Get all incidents (with a reasonable limit)
        print("📊 Retrieving incident statistics...")
        
        # Get total count by retrieving with a high limit
        all_incidents = sn.get_incidents(limit=1000)
        total_count = len(all_incidents)
        
        print(f"📈 Total Incidents: {total_count}")
        print()
        
        # Get breakdown by priority
        print("🎯 Breakdown by Priority:")
        priority_counts = {}
        priority_names = {
            '1': 'Critical',
            '2': 'High', 
            '3': 'Moderate',
            '4': 'Low',
            '5': 'Planning'
        }
        
        for priority in ['1', '2', '3', '4', '5']:
            priority_incidents = sn.get_incidents_by_priority(priority)
            count = len(priority_incidents)
            priority_counts[priority] = count
            print(f"   {priority_names[priority]} (Priority {priority}): {count}")
        
        print()
        
        # Get breakdown by state
        print("📋 Breakdown by State:")
        state_counts = {}
        state_names = {
            '1': 'New',
            '2': 'In Progress',
            '3': 'On Hold',
            '6': 'Resolved',
            '7': 'Closed'
        }
        
        for state in ['1', '2', '3', '6', '7']:
            state_incidents = sn.get_incidents_by_state(state)
            count = len(state_incidents)
            state_counts[state] = count
            print(f"   {state_names[state]} (State {state}): {count}")
        
        print()
        
        # Get breakdown by category
        print("🏷️  Breakdown by Category:")
        categories = {}
        for incident in all_incidents:
            category = incident.get('category', 'Unknown')
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
        
        # Sort categories by count
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories:
            print(f"   {category}: {count}")
        
        print()
        
        # Show recent incidents (last 5)
        print("🕒 Recent Incidents (Last 5):")
        recent_incidents = all_incidents[-5:] if len(all_incidents) >= 5 else all_incidents
        for incident in recent_incidents:
            number = incident.get('number', 'N/A')
            short_desc = incident.get('short_description', 'No description')
            priority = incident.get('priority', 'N/A')
            state = incident.get('state', 'N/A')
            
            priority_text = priority_names.get(priority, f'Priority {priority}')
            state_text = state_names.get(state, f'State {state}')
            
            print(f"   {number}: {short_desc}")
            print(f"      Priority: {priority_text}, State: {state_text}")
            print()
        
        print("=" * 50)
        print("✅ Incident check completed successfully!")
        
    except Exception as e:
        print(f"❌ Error checking incidents: {str(e)}")
        return

if __name__ == "__main__":
    main() 