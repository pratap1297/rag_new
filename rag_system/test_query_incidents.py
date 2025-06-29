#!/usr/bin/env python3
"""
Test querying ServiceNow incidents
"""

import sys
import os
sys.path.append('src')

from src.core.dependency_container import DependencyContainer, register_core_services

def main():
    print("🔍 Testing ServiceNow Incidents Query")
    print("=" * 50)
    
    try:
        # Initialize the system
        container = DependencyContainer()
        register_core_services(container)
        
        # Get query engine
        query_engine = container.get('query_engine')
        if not query_engine:
            print("❌ Query engine not available")
            return
        
        print("✅ Query engine initialized")
        
        # Test queries
        test_queries = [
            "all ServiceNow incidents",
            "INC030001 INC030002 INC030003 INC030004 INC030005",
            "how many incidents in the system",
            "Building B Freezer Zone2",
            "Building C Conveyor System",
            "unauthorized access attempt",
            "network equipment failure"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            print("-" * 40)
            
            try:
                result = query_engine.process_query(query)
                
                if 'answer' in result:
                    print(f"📝 Answer: {result['answer'][:300]}...")
                
                if 'sources' in result:
                    print(f"📚 Sources found: {len(result['sources'])}")
                    for i, source in enumerate(result['sources'][:3], 1):
                        metadata = source.get('metadata', {})
                        if 'ticket_number' in metadata:
                            print(f"  {i}. {metadata.get('ticket_number', 'N/A')} - {metadata.get('title', 'N/A')[:50]}...")
                        elif 'record_id' in metadata:
                            print(f"  {i}. {metadata.get('record_id', 'N/A')} - {source.get('text', '')[:50]}...")
                        else:
                            print(f"  {i}. {source.get('text', '')[:50]}...")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 