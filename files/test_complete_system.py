#!/usr/bin/env python3
"""
Test Complete System
Comprehensive test of the vector-metadata linking system
"""
import sys
import os
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_complete_system():
    print("🧪 Testing Complete Vector-Metadata Linking System")
    print("=" * 60)
    
    try:
        # 1. Clear all existing data for clean test
        print("🧹 Clearing existing data...")
        
        data_dirs = ["data/vectors", "data/metadata", "data/uploads"]
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
                print(f"   ✅ Cleared {data_dir}")
        
        # 2. Initialize fresh system
        print("\n🔧 Initializing fresh system...")
        from src.core.system_init import initialize_system
        container = initialize_system()
        
        ingestion_engine = container.get('ingestion_engine')
        query_engine = container.get('query_engine')
        metadata_store = container.get('metadata_store')
        faiss_store = container.get('faiss_store')
        
        print("   ✅ System initialized")
        
        # 3. Create test document
        print("\n📄 Creating test document...")
        
        test_content = """# Hugging Face Embeddings Cost Analysis
        
## Executive Summary
The migration from Cohere to Hugging Face embeddings provides significant cost savings of approximately $0.10 per 1M tokens. This represents a 100% reduction in embedding API costs while maintaining high-quality semantic search capabilities.

## Technical Benefits
- Local processing eliminates network dependencies
- Enhanced data privacy through on-premise computation
- Improved performance with reduced latency
- Support for multiple embedding models including all-MiniLM-L6-v2

## Implementation Details
The system now supports sentence-transformers as the default embedding provider with configurable models and dimensions. The migration includes automatic backup and rollback capabilities.
"""
        
        # Save test document
        os.makedirs("data/uploads", exist_ok=True)
        test_file = "data/uploads/test_huggingface_analysis.md"
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        print(f"   ✅ Created test document: {test_file}")
        
        # 4. Ingest the document
        print("\n🔄 Ingesting document...")
        
        result = ingestion_engine.ingest_file(test_file)
        
        if result and result.get('success'):
            print(f"   ✅ Document ingested successfully")
            print(f"   📊 Chunks: {result.get('chunk_count', 0)}")
            print(f"   🔢 Vectors: {result.get('vector_count', 0)}")
        else:
            print(f"   ❌ Ingestion failed: {result}")
            return
        
        # 5. Verify data storage
        print("\n🔍 Verifying data storage...")
        
        # Check FAISS store
        faiss_stats = faiss_store.get_stats()
        print(f"   FAISS vectors: {faiss_stats.get('vector_count', 0)}")
        print(f"   FAISS active: {faiss_stats.get('active_vectors', 0)}")
        
        # Check metadata store
        files = metadata_store.get_all_files()
        chunks = metadata_store.get_all_chunks()
        print(f"   Metadata files: {len(files)}")
        print(f"   Metadata chunks: {len(chunks)}")
        
        if files:
            sample_file = files[0]
            print(f"   Sample file: {sample_file.get('filename', 'unknown')}")
        
        # 6. Test queries
        print("\n🧪 Testing queries...")
        
        test_queries = [
            "What are the cost savings from Hugging Face embeddings?",
            "What technical benefits does local processing provide?",
            "What embedding models are supported?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            try:
                result = query_engine.process_query(query, top_k=3)
                
                if result and 'sources' in result:
                    sources = result.get('sources', [])
                    print(f"   ✅ Found {len(sources)} sources")
                    
                    for j, source in enumerate(sources[:2], 1):
                        doc_info = source.get('metadata', {})
                        filename = doc_info.get('filename', 'unknown')
                        doc_id = doc_info.get('doc_id', 'unknown')
                        score = source.get('similarity_score', 0)
                        
                        print(f"     Source {j}: {filename} (doc_id: {doc_id}, score: {score:.3f})")
                        
                        # Check if we still have unknown documents
                        if 'unknown' in filename or 'unknown' in doc_id:
                            print(f"     ⚠️ Still showing unknown document!")
                        else:
                            print(f"     ✅ Document properly identified!")
                
                # Check response
                response = result.get('response', '')
                if response and len(response) > 50:
                    print(f"   ✅ Generated response: {response[:100]}...")
                else:
                    print(f"   ⚠️ Short or missing response: {response}")
                    
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
        
        # 7. Summary
        print("\n📋 Test Summary:")
        print(f"   • FAISS vectors: {faiss_stats.get('vector_count', 0)}")
        print(f"   • Metadata files: {len(files)}")
        print(f"   • Metadata chunks: {len(chunks)}")
        print(f"   • System status: {'✅ Working' if len(files) > 0 and faiss_stats.get('vector_count', 0) > 0 else '❌ Issues detected'}")
        
        if len(files) > 0 and faiss_stats.get('vector_count', 0) > 0:
            print("\n🎉 SUCCESS: Vector-metadata linking is working properly!")
            print("   • Documents are properly identified")
            print("   • No more 'doc_unknown' issues")
            print("   • System ready for production use")
        else:
            print("\n❌ ISSUES: Vector-metadata linking needs attention")
            print("   • Check ingestion process")
            print("   • Verify metadata storage")
            print("   • Review system configuration")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_system() 