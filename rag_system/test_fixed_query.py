#!/usr/bin/env python3
"""
Test that all 5 ServiceNow incidents are now returned with the lower threshold
"""

import sys
import os
sys.path.append('src')

from src.core.dependency_container import DependencyContainer, register_core_services

def main():
    print("🎫 Testing ServiceNow Incidents with Lower Threshold")
    print("=" * 60)
    
    try:
        # Initialize the system
        container = DependencyContainer()
        register_core_services(container)
        
        # Get query engine
        query_engine = container.get('query_engine')
        config_manager = container.get('config_manager')
        
        # Check new threshold
        config = config_manager.get_config()
        similarity_threshold = config.retrieval.similarity_threshold
        print(f"📊 New similarity threshold: {similarity_threshold}")
        
        print("✅ Query engine initialized")
        
        # Test the main query about incidents
        query = "tell me about all the incidents in the system"
        print(f"\n🔍 Query: '{query}'")
        print("-" * 50)
        
        result = query_engine.process_query(query)
        
        if 'answer' in result:
            print(f"📝 Answer: {result['answer']}")
        
        if 'sources' in result:
            print(f"\n📚 Sources found: {len(result['sources'])}")
            
            # Count ServiceNow incidents
            servicenow_incidents = []
            for i, source in enumerate(result['sources'], 1):
                text = source.get('text', '')
                metadata = source.get('metadata', {})
                
                if 'INC030' in text:
                    # Extract incident info
                    lines = text.split('\n')
                    incident_line = next((line for line in lines if 'Incident:' in line and 'INC030' in line), '')
                    priority_line = next((line for line in lines if 'Priority:' in line), '')
                    category_line = next((line for line in lines if 'Category:' in line), '')
                    location_line = next((line for line in lines if 'Location:' in line), '')
                    
                    if incident_line:
                        incident_num = incident_line.split(':')[1].strip().split()[0]
                        priority = priority_line.split(':')[1].strip() if priority_line else 'N/A'
                        category = category_line.split(':')[1].strip() if category_line else 'N/A'
                        location = location_line.split(':')[1].strip() if location_line else 'N/A'
                        
                        servicenow_incidents.append({
                            'number': incident_num,
                            'priority': priority,
                            'category': category,
                            'location': location
                        })
                        
                        print(f"  {i}. {incident_num}")
                        print(f"     Priority: {priority}")
                        print(f"     Category: {category}")
                        print(f"     Location: {location}")
                        print()
            
            print(f"🎫 ServiceNow incidents found: {len(servicenow_incidents)}")
            
            # List all incident numbers
            incident_numbers = [inc['number'] for inc in servicenow_incidents]
            incident_numbers.sort()
            print(f"📋 Incident numbers: {', '.join(incident_numbers)}")
            
            # Check if we have all 5
            expected_incidents = ['INC030001', 'INC030002', 'INC030003', 'INC030004', 'INC030005']
            missing_incidents = [inc for inc in expected_incidents if inc not in incident_numbers]
            
            if not missing_incidents:
                print("✅ All 5 incidents found!")
            else:
                print(f"❌ Missing incidents: {', '.join(missing_incidents)}")
        
        # Test specific incident queries
        specific_queries = [
            "INC030003 INC030005",
            "Building B Freezer Zone2",
            "Building C Conveyor System",
            "unauthorized access attempt"
        ]
        
        for specific_query in specific_queries:
            print(f"\n🔍 Specific Query: '{specific_query}'")
            print("-" * 40)
            
            result = query_engine.process_query(specific_query)
            
            if 'sources' in result:
                incidents_in_result = []
                for source in result['sources']:
                    text = source.get('text', '')
                    if 'INC030' in text:
                        lines = text.split('\n')
                        incident_line = next((line for line in lines if 'Incident:' in line and 'INC030' in line), '')
                        if incident_line:
                            incident_num = incident_line.split(':')[1].strip().split()[0]
                            incidents_in_result.append(incident_num)
                
                print(f"📋 Incidents found: {', '.join(set(incidents_in_result))}")
            else:
                print("📋 No sources found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 