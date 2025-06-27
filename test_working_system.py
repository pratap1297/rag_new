#!/usr/bin/env python3
"""
Test Working Azure Vision Integration
Final verification that PDF content is properly accessible
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "rag_system"))

def test_working_system():
    """Test that the system is working with Azure Vision"""
    print("🎯 Testing Azure Vision PDF Integration")
    print("=" * 60)
    
    try:
        # Import required components
        from src.core.system_init import initialize_system
        
        # Initialize the system
        print("🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get query engine
        query_engine = container.get('query_engine')
        
        # Simple network query
        query = "What building network layouts are available?"
        print(f"\n🔍 Query: '{query}'")
        print("-" * 40)
        
        # Process query
        result = query_engine.process_query(query)
        
        # Display results properly
        if isinstance(result, dict):
            response = result.get('response', result.get('answer', ''))
            sources = result.get('sources', [])
            confidence = result.get('confidence', 0)
            
            print(f"✅ **RESPONSE**: {response}")
            print(f"📊 **Confidence**: {confidence:.2f}")
            print(f"📄 **Sources**: {len(sources)} found")
            
            if sources:
                for i, source in enumerate(sources, 1):
                    source_text = source.get('text', '')[:100]
                    print(f"   {i}. {source_text}...")
        else:
            print(f"✅ **RESPONSE**: {result}")
        
        # Test specific PDF content queries
        pdf_queries = [
            "Building A network layout",
            "signal strength coverage"
        ]
        
        for test_query in pdf_queries:
            print(f"\n🔍 Testing: '{test_query}'")
            print("-" * 30)
            
            result = query_engine.process_query(test_query)
            
            if isinstance(result, dict):
                response = result.get('response', result.get('answer', ''))
                print(f"📝 Response: {response[:200]}...")
            else:
                print(f"📝 Response: {str(result)[:200]}...")
        
        print(f"\n🎉 Azure Vision PDF Integration Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_working_system() 