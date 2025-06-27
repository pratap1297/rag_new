#!/usr/bin/env python3
"""
Test Network Layout Queries
Tests that PDF content is now properly searchable
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "rag_system"))

def test_network_queries():
    """Test queries related to network layouts"""
    print("🧪 Testing Network Layout Queries")
    print("=" * 50)
    
    try:
        # Import required components
        from src.core.system_init import initialize_system
        
        # Initialize the system
        print("🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get query engine
        query_engine = container.get('query_engine')
        
        # Test queries
        test_queries = [
            "What buildings are covered in the network layout documents?",
            "What floors are mentioned in the network layouts?", 
            "What signal strength information is available?",
            "What is the RSSI data in Building A?",
            "What network equipment is mentioned in the documents?"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 Query {i}: {query}")
            try:
                # Use process_query method
                response = query_engine.process_query(query)
                
                if hasattr(response, 'answer'):
                    answer = response.answer
                elif hasattr(response, 'response'):
                    answer = response.response
                else:
                    answer = str(response)[:500] + "..." if len(str(response)) > 500 else str(response)
                
                print(f"✅ Answer: {answer}")
                
                # Show sources if available
                if hasattr(response, 'sources') and response.sources:
                    print(f"📄 Sources: {len(response.sources)} documents")
                    for source in response.sources[:2]:  # Show first 2 sources
                        if hasattr(source, 'source'):
                            print(f"   - {source.source}")
                        
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        print(f"\n🎉 Network query testing completed!")
        
    except Exception as e:
        print(f"❌ Failed to test queries: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_network_queries() 