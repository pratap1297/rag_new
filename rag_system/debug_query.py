#!/usr/bin/env python3
"""
Debug query processing for ServiceNow incidents
"""

import sys
import os
sys.path.append('src')

from src.core.dependency_container import DependencyContainer, register_core_services

def main():
    print("🔍 Debugging ServiceNow Query Processing")
    print("=" * 50)
    
    try:
        # Initialize the system
        container = DependencyContainer()
        register_core_services(container)
        
        # Get components
        faiss_store = container.get('faiss_store')
        embedder = container.get('embedder')
        config_manager = container.get('config_manager')
        
        print("✅ Components initialized")
        
        # Get config
        config = config_manager.get_config()
        similarity_threshold = config.retrieval.similarity_threshold
        print(f"📊 Similarity threshold: {similarity_threshold}")
        
        # Test queries
        test_queries = [
            "all ServiceNow incidents",
            "INC030003 INC030005",
            "Building B Freezer Zone2",
            "Building C Conveyor System",
            "unauthorized access attempt",
            "network equipment failure",
            "incident"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            print("-" * 40)
            
            try:
                # Generate embedding
                query_embedding = embedder.embed_text(query)
                
                # Search with different k values
                for k in [5, 10, 15]:
                    search_results = faiss_store.search_with_metadata(
                        query_vector=query_embedding,
                        k=k
                    )
                    
                    print(f"📊 Top {k} results:")
                    if search_results:
                        above_threshold = [r for r in search_results if r.get('similarity_score', 0) >= similarity_threshold]
                        print(f"  - Total results: {len(search_results)}")
                        print(f"  - Above threshold ({similarity_threshold}): {len(above_threshold)}")
                        
                        # Show top 3 results with details
                        for i, result in enumerate(search_results[:3], 1):
                            score = result.get('similarity_score', 0)
                            text = result.get('text', '')
                            metadata = result.get('metadata', {})
                            
                            # Check if this looks like a ServiceNow incident
                            is_incident = 'INC' in text or 'Incident:' in text
                            
                            print(f"    {i}. Score: {score:.3f} {'✅' if score >= similarity_threshold else '❌'} {'🎫' if is_incident else ''}")
                            print(f"       Text: {text[:100]}...")
                            if is_incident:
                                # Extract incident number
                                if 'INC' in text:
                                    lines = text.split('\n')
                                    incident_line = next((line for line in lines if 'INC' in line), '')
                                    print(f"       Incident: {incident_line.strip()}")
                            print()
                    else:
                        print(f"  - No results found")
                    
                    if k == 5:  # Only show detailed breakdown for k=5
                        print()
                
            except Exception as e:
                print(f"❌ Search failed: {e}")
        
        # Summary of all incidents in the system
        print(f"\n📋 Summary - Searching for all incidents:")
        all_results = faiss_store.search_with_metadata(
            query_vector=embedder.embed_text("incident ServiceNow INC030"),
            k=25  # Get more results
        )
        
        incidents_found = []
        for result in all_results:
            text = result.get('text', '')
            if 'INC030' in text:
                # Extract incident number
                lines = text.split('\n')
                incident_line = next((line for line in lines if 'Incident:' in line and 'INC030' in line), '')
                if incident_line:
                    incident_num = incident_line.split(':')[1].strip().split()[0]
                    score = result.get('similarity_score', 0)
                    incidents_found.append((incident_num, score))
        
        print(f"🎫 All ServiceNow incidents found in index:")
        incidents_found.sort()
        for incident_num, score in incidents_found:
            print(f"  - {incident_num}: similarity score {score:.3f}")
        
        print(f"\n📊 Total unique incidents: {len(set(inc[0] for inc in incidents_found))}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 