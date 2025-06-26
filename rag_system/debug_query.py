#!/usr/bin/env python3
"""
Debug query to understand why ServiceNow incidents aren't being found
"""

import sys
import os
sys.path.append('src')

from src.retrieval.query_engine import QueryEngine
from src.core.dependency_container import DependencyContainer
from src.core.config_manager import ConfigManager

def debug_servicenow_query():
    """Debug why ServiceNow incidents aren't being found"""
    
    print("🔍 Debugging ServiceNow Query Issue")
    print("=" * 50)
    
    try:
        # Initialize the system
        config_manager = ConfigManager()
        container = DependencyContainer(config_manager)
        
        # Get query engine
        query_engine = container.get_query_engine()
        if not query_engine:
            print("❌ Query engine not available")
            return
        
        print("✅ Query engine initialized")
        
        # Test queries
        test_queries = [
            "INC030004",
            "ServiceNow incidents",
            "How many ServiceNow incidents",
            "INC030001 INC030002",
            "WiFi coverage Building A"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            print("-" * 30)
            
            try:
                # Process query with lower threshold for debugging
                result = query_engine.process_query(
                    query=query,
                    top_k=10,  # Get more results for debugging
                    conversation_context={'bypass_threshold': True}  # Bypass threshold
                )
                
                sources = result.get('sources', [])
                print(f"📊 Found {len(sources)} sources")
                
                for i, source in enumerate(sources[:5]):  # Show top 5
                    score = source.get('similarity_score', 0)
                    metadata = source.get('metadata', {})
                    doc_id = metadata.get('doc_id', 'Unknown')
                    content_preview = source.get('text', '')[:100] + '...'
                    
                    print(f"  {i+1}. Score: {score:.3f}")
                    print(f"     Doc ID: {doc_id}")
                    print(f"     Content: {content_preview}")
                    print()
                
                if not sources:
                    print("  ❌ No sources found")
                    
            except Exception as e:
                print(f"  ❌ Error processing query: {e}")
        
        # Test direct vector search
        print(f"\n🔍 Testing direct vector search for ServiceNow")
        print("-" * 30)
        
        try:
            # Get FAISS store
            faiss_store = container.get_faiss_store()
            if faiss_store:
                # Test embedding for "ServiceNow"
                embedder = container.get_embedder()
                if embedder:
                    query_embedding = embedder.embed_text("ServiceNow incidents")
                    
                    # Search directly
                    results = faiss_store.search_with_metadata(
                        query_vector=query_embedding,
                        k=10
                    )
                    
                    print(f"📊 Direct search found {len(results)} results")
                    
                    for i, result in enumerate(results[:5]):
                        score = result.get('similarity_score', 0)
                        metadata = result.get('metadata', {})
                        doc_id = metadata.get('doc_id', 'Unknown')
                        content_preview = result.get('text', '')[:100] + '...'
                        
                        print(f"  {i+1}. Score: {score:.3f}")
                        print(f"     Doc ID: {doc_id}")
                        print(f"     Content: {content_preview}")
                        print()
                        
        except Exception as e:
            print(f"  ❌ Error in direct search: {e}")
            
    except Exception as e:
        print(f"❌ Error initializing system: {e}")

if __name__ == "__main__":
    debug_servicenow_query() 