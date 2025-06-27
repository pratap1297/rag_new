#!/usr/bin/env python3
"""
Check PDF Content and Metadata
Verifies what content was actually extracted from PDFs
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "rag_system"))

def check_pdf_content():
    """Check what content was extracted from PDFs"""
    print("🔍 Checking PDF Content and Metadata")
    print("=" * 50)
    
    try:
        # Import required components
        from src.core.system_init import initialize_system
        
        # Initialize the system
        print("🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get components
        metadata_store = container.get('metadata_store')
        faiss_store = container.get('faiss_store')
        
        stats = faiss_store.get_stats()
        print(f"\n📊 Total vectors in FAISS: {stats.get('total_vectors', 0)}")
        
        # Get all documents
        print("\n📄 Checking all documents in metadata store...")
        all_files = metadata_store.get_all_files()
        
        pdf_docs = []
        for doc in all_files:
            if 'pdf' in doc.get('file_path', '').lower():
                pdf_docs.append(doc)
        
        print(f"Found {len(pdf_docs)} PDF documents:")
        
        for i, doc in enumerate(pdf_docs, 1):
            print(f"\n📋 PDF {i}: {doc.get('file_path', 'Unknown')}")
            print(f"   📝 Title: {doc.get('title', 'No title')}")
            print(f"   🏢 Building: {doc.get('building', 'Unknown')}")
            print(f"   📄 Document Type: {doc.get('document_type', 'Unknown')}")
            print(f"   🔧 Extraction Method: {doc.get('extraction_method', 'Unknown')}")
            
            # Get chunks for this document
            chunks = metadata_store.get_file_chunks(doc['file_id'])
            print(f"   📦 Chunks: {len(chunks)}")
            
            for j, chunk in enumerate(chunks, 1):
                text = chunk.get('text', '')
                print(f"      🧩 Chunk {j}: {len(text)} characters")
                if text:
                    # Show first 200 characters
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"         Preview: {preview}")
                else:
                    print(f"         ⚠️  Empty chunk!")
        
        # Check similarity threshold
        print(f"\n🎯 Current similarity threshold: {container.get('config_manager').get_config().retrieval.similarity_threshold}")
        
        # Test a simple search manually
        print(f"\n🧪 Testing manual search...")
        embedder = container.get('embedder')
        
        test_query = "Building A"
        query_embedding = embedder.embed_text(test_query)
        search_results = faiss_store.search_with_metadata(
            query_vector=query_embedding,
            k=10
        )
        
        print(f"📋 Manual search for '{test_query}' found {len(search_results)} results:")
        for i, result in enumerate(search_results[:5], 1):
            similarity = result.get('similarity_score', 0)
            source = result.get('source', 'Unknown')
            text_preview = result.get('text', '')[:100] + "..." if result.get('text') else "No text"
            print(f"   {i}. Score: {similarity:.3f} | Source: {source}")
            print(f"      Text: {text_preview}")
        
        print(f"\n🎉 Content check completed!")
        
    except Exception as e:
        print(f"❌ Failed to check content: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_pdf_content() 