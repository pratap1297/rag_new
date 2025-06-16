#!/usr/bin/env python3
"""
Ingest Sample Document
This script ingests one of your markdown documents to test the fixed RAG system
"""
import sys
import os
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def ingest_sample_doc():
    print("📚 Ingesting Sample Document")
    print("=" * 50)
    
    try:
        # Initialize system
        print("🔧 Initializing RAG system...")
        from src.core.system_init import initialize_system
        container = initialize_system()
        
        ingestion_engine = container.get('ingestion_engine')
        metadata_store = container.get('metadata_store')
        
        # Choose a sample document
        sample_doc = "../DETAILED_BRD_HUGGINGFACE_IMPLEMENTATION.md"
        if not os.path.exists(sample_doc):
            print(f"❌ Sample document not found: {sample_doc}")
            return
        
        print(f"📄 Ingesting: {sample_doc}")
        
        # Copy to uploads directory
        uploads_dir = "data/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        dest_path = os.path.join(uploads_dir, "DETAILED_BRD_HUGGINGFACE_IMPLEMENTATION.md")
        shutil.copy2(sample_doc, dest_path)
        
        # Ingest the document
        print("🔄 Processing document...")
        result = ingestion_engine.ingest_file(dest_path)
        
        if result.get('success'):
            print(f"✅ Document ingested successfully!")
            print(f"   File ID: {result.get('file_id')}")
            print(f"   Chunks created: {result.get('chunk_count', 0)}")
            print(f"   Vectors added: {result.get('vector_count', 0)}")
        else:
            print(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")
            return
        
        # Verify the ingestion
        print("\n🔍 Verifying ingestion...")
        files = metadata_store.get_all_files()
        chunks = metadata_store.get_all_chunks()
        
        print(f"   Files in system: {len(files)}")
        print(f"   Chunks in system: {len(chunks)}")
        
        if files:
            file_info = files[0]
            print(f"   Sample file: {file_info.get('filename', 'unknown')}")
            print(f"   Chunk count: {file_info.get('chunk_count', 0)}")
        
        # Test a query
        print("\n🧪 Testing query...")
        query_engine = container.get('query_engine')
        
        test_query = "What are the cost savings from switching to Hugging Face embeddings?"
        result = query_engine.query(test_query, max_results=3)
        
        if result and 'results' in result:
            print(f"   Query: {test_query}")
            print(f"   Results found: {len(result['results'])}")
            
            for i, res in enumerate(result['results'][:2], 1):
                doc_id = res.get('doc_id', 'unknown')
                content_preview = res.get('content', '')[:100] + "..."
                score = res.get('score', 0)
                print(f"   {i}. Doc: {doc_id} | Score: {score:.3f}")
                print(f"      Content: {content_preview}")
        else:
            print("   ❌ Query failed or no results")
        
        print("\n✅ Sample document ingestion completed!")
        print("\n🎯 Now you can test these questions:")
        print("   • 'What are the cost savings from switching to Hugging Face embeddings?'")
        print("   • 'How does the migration from Cohere to Hugging Face work?'")
        print("   • 'What embedding models are supported?'")
        print("   • 'What are the business benefits of local processing?'")
        
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ingest_sample_doc() 