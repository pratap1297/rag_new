#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def diagnose_system():
    try:
        print("🔍 RAG System Diagnostic Report")
        print("=" * 50)
        
        # Initialize system
        from src.core.system_init import initialize_system
        container = initialize_system()
        print("✅ System initialized successfully")
        
        # Check metadata store
        metadata_store = container.get('metadata_store')
        files = metadata_store.get_all_files()
        chunks = metadata_store.get_all_chunks()
        
        print(f"\n📊 Metadata Store Status:")
        print(f"   Files: {len(files)}")
        print(f"   Chunks: {len(chunks)}")
        
        if files:
            print(f"\n📁 Files in system:")
            for i, file_info in enumerate(files, 1):
                print(f"   {i}. {file_info['filename']} ({file_info['chunk_count']} chunks)")
        
        if chunks:
            print(f"\n📄 Sample chunks:")
            for i, chunk in enumerate(chunks[:3], 1):
                content_preview = chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                print(f"   {i}. File: {chunk.get('filename', 'UNKNOWN')} | Content: {content_preview}")
        
        # Check FAISS store
        try:
            faiss_store = container.get('faiss_store')
            vector_count = faiss_store.get_vector_count() if hasattr(faiss_store, 'get_vector_count') else "Unknown"
            print(f"\n🔢 FAISS Vector Store:")
            print(f"   Vectors: {vector_count}")
            
            # Try to get some metadata from FAISS
            if hasattr(faiss_store, 'index') and faiss_store.index.ntotal > 0:
                print(f"   Index size: {faiss_store.index.ntotal}")
                print(f"   Dimension: {faiss_store.index.d}")
        except Exception as e:
            print(f"❌ FAISS store error: {e}")
        
        # Test a simple query
        print(f"\n🧪 Testing simple query...")
        try:
            query_engine = container.get('query_engine')
            result = query_engine.query("test", max_results=1)
            if result and 'results' in result:
                print(f"   Query returned {len(result['results'])} results")
                if result['results']:
                    first_result = result['results'][0]
                    print(f"   First result doc_id: {first_result.get('doc_id', 'MISSING')}")
                    print(f"   First result content preview: {first_result.get('content', '')[:100]}...")
            else:
                print("   No results returned")
        except Exception as e:
            print(f"❌ Query test failed: {e}")
            
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_system() 