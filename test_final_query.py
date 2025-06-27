#!/usr/bin/env python3
"""
Final Test of Azure Vision PDF Content
Tests actual queries with lower thresholds to see if content is accessible
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "rag_system"))

def test_final_queries():
    """Test final queries with different thresholds"""
    print("🔍 Final Test: Azure Vision PDF Content")
    print("=" * 60)
    
    try:
        # Import required components
        from src.core.system_init import initialize_system
        
        # Initialize the system
        print("🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get query engine
        query_engine = container.get('query_engine')
        
        # Test queries
        queries = [
            "network layout Building A",
            "signal map",
            "RSSI",
            "coverage quality",
            "distribution center"
        ]
        
        print(f"\n🧪 Testing {len(queries)} queries:")
        
        for i, query in enumerate(queries, 1):
            print(f"\n📋 Query {i}: '{query}'")
            print("-" * 40)
            
            try:
                # Use process_query method with debug info
                response = query_engine.process_query(query)
                
                print(f"✅ Query processed successfully")
                print(f"📝 Response length: {len(response)} characters")
                
                if response and len(response) > 50:
                    print(f"📄 Response preview: {response[:200]}...")
                    
                    # Check if response contains our PDF content keywords
                    keywords = ['building', 'network', 'layout', 'signal', 'rssi', 'coverage']
                    found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]
                    if found_keywords:
                        print(f"🎯 Contains keywords: {found_keywords}")
                    else:
                        print("⚠️  No network-related keywords found")
                else:
                    print("❌ No relevant content found or very short response")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        # Get more detailed search results
        print(f"\n🔍 Testing with FAISS direct search...")
        faiss_store = container.get('faiss_store')
        embedder = container.get('embedder')
        
        test_query = "Building A network layout"
        query_vector = embedder.embed_text(test_query)
        
        # Search with low threshold
        search_results = faiss_store.search(query_vector, k=10)
        
        print(f"📊 Direct FAISS search results for '{test_query}':")
        for i, result in enumerate(search_results, 1):
            score = result.get('score', 0)
            text = result.get('text', '')
            source = result.get('source', 'Unknown')
            
            print(f"   {i}. Score: {score:.3f} | Source: {source}")
            print(f"      Text: {text[:100]}..." if text else "      (No text)")
        
        print(f"\n✅ Final test completed!")
        
    except Exception as e:
        print(f"❌ Final test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_queries() 