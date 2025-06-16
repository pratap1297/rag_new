#!/usr/bin/env python3
"""
Final Verification Test
Check if vector-metadata linking is working properly after ingestion
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_final_verification():
    print("🔍 Final Verification: Vector-Metadata Linking")
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
        faiss_stats = faiss_store.get_stats()
        
        print(f"   Files: {len(files)}")
        print(f"   Chunks: {len(chunks)}")
        print(f"   FAISS vectors: {faiss_stats.get('vector_count', 0)}")
        
        if len(files) > 0:
            sample_file = files[0]
            print(f"   Sample file: {sample_file.get('filename', 'unknown')}")
        
        # Test a query
        print("\n🧪 Testing Query:")
        test_query = "What are the cost savings from Hugging Face embeddings?"
        print(f"   Query: {test_query}")
        
        result = query_engine.process_query(test_query, top_k=3)
        
        if result:
            print(f"   ✅ Query processed successfully")
            
            # Check sources
            sources = result.get('sources', [])
            print(f"   📚 Sources found: {len(sources)}")
            
            for i, source in enumerate(sources, 1):
                metadata = source.get('metadata', {})
                filename = metadata.get('filename', 'unknown')
                doc_id = metadata.get('doc_id', 'unknown')
                score = source.get('similarity_score', 0)
                
                print(f"     Source {i}:")
                print(f"       Filename: {filename}")
                print(f"       Doc ID: {doc_id}")
                print(f"       Score: {score:.3f}")
                
                # Check if document is properly identified
                if 'unknown' not in filename and 'unknown' not in doc_id:
                    print(f"       ✅ Document properly identified!")
                else:
                    print(f"       ⚠️ Document still showing as unknown")
            
            # Check response
            response = result.get('response', '')
            if response and len(response) > 20:
                print(f"\n   🤖 Response: {response[:150]}...")
                print(f"   ✅ LLM response generated successfully")
            else:
                print(f"\n   ⚠️ No proper response generated")
        else:
            print(f"   ❌ Query failed")
        
        # Direct FAISS test
        print(f"\n🔧 Direct FAISS Test:")
        
        # Get embedder and test direct search
        embedder = container.get('embedder')
        query_embedding = embedder.embed_text(test_query)
        
        # Direct FAISS search
        direct_results = faiss_store.search_with_metadata(query_embedding, k=3)
        print(f"   Direct FAISS results: {len(direct_results)}")
        
        for i, result in enumerate(direct_results, 1):
            doc_id = result.get('doc_id', 'unknown')
            filename = result.get('filename', 'unknown')
            content = result.get('content', '')[:100] + "..."
            score = result.get('similarity_score', 0)
            
            print(f"     Result {i}:")
            print(f"       Doc ID: {doc_id}")
            print(f"       Filename: {filename}")
            print(f"       Score: {score:.3f}")
            print(f"       Content: {content}")
            
            if 'unknown' not in doc_id and 'unknown' not in filename:
                print(f"       ✅ Properly linked!")
            else:
                print(f"       ❌ Still unknown")
        
        # Final assessment
        print(f"\n📋 Final Assessment:")
        
        has_vectors = faiss_stats.get('vector_count', 0) > 0
        has_metadata = len(files) > 0 or len(chunks) > 0
        has_proper_linking = any('unknown' not in r.get('doc_id', 'unknown') for r in direct_results)
        
        print(f"   • Has vectors: {'✅' if has_vectors else '❌'}")
        print(f"   • Has metadata: {'✅' if has_metadata else '❌'}")
        print(f"   • Proper linking: {'✅' if has_proper_linking else '❌'}")
        
        if has_vectors and has_metadata and has_proper_linking:
            print(f"\n🎉 SUCCESS: Vector-metadata linking is working!")
            print(f"   • Documents are properly identified")
            print(f"   • No more 'doc_unknown' issues")
            print(f"   • System ready for production")
        elif has_vectors and has_metadata:
            print(f"\n⚠️ PARTIAL: System has data but linking needs improvement")
            print(f"   • Vectors and metadata exist")
            print(f"   • But linking may not be perfect")
        else:
            print(f"\n❌ ISSUES: System needs attention")
            print(f"   • Missing vectors or metadata")
            print(f"   • Check ingestion process")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_verification() 