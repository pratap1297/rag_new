#!/usr/bin/env python3
"""
Test Fixed System
Simple test to verify the unknown documents issue is resolved
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_system():
    print("🧪 Testing Fixed RAG System")
    print("=" * 50)
    
    try:
        # Initialize system
        from src.core.system_init import initialize_system
        container = initialize_system()
        
        query_engine = container.get('query_engine')
        metadata_store = container.get('metadata_store')
        faiss_store = container.get('faiss_store')
        
        # Check system state
        print("📊 System Status:")
        files = metadata_store.get_all_files()
        chunks = metadata_store.get_all_chunks()
        vector_count = faiss_store.index.ntotal if hasattr(faiss_store, 'index') else 0
        
        print(f"   Files: {len(files)}")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Vectors: {vector_count}")
        
        # Test query
        print("\n🔍 Testing Query:")
        test_query = "What are the cost savings from Hugging Face embeddings?"
        print(f"   Query: {test_query}")
        
        result = query_engine.query(test_query, max_results=3)
        
        if result and 'results' in result:
            print(f"   ✅ Found {len(result['results'])} results")
            
            for i, res in enumerate(result['results'][:2], 1):
                doc_id = res.get('doc_id', 'MISSING')
                content = res.get('content', '')[:150] + "..."
                score = res.get('score', 0)
                
                print(f"\n   Result {i}:")
                print(f"     Doc ID: {doc_id}")
                print(f"     Score: {score:.3f}")
                print(f"     Content: {content}")
                
                # Check if we still have "unknown" issue
                if doc_id == 'unknown' or 'unknown' in doc_id:
                    print(f"     ⚠️ Still showing unknown document!")
                else:
                    print(f"     ✅ Document properly identified!")
        else:
            print("   ❌ No results found")
        
        # Test with response generation
        print("\n🤖 Testing Full Response:")
        if result and 'response' in result:
            response = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
            print(f"   Response: {response}")
        else:
            print("   ❌ No response generated")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_system() 