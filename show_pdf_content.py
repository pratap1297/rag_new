#!/usr/bin/env python3
"""
Show PDF Upload Content
Display the extracted content from the recently uploaded PDF file
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def show_pdf_content():
    """Show content from the recently uploaded PDF"""
    print("📄 PDF Upload Content Analysis")
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
        
        # Look for the specific PDF file mentioned in logs
        target_pdf = "tmp9q60s497.pdf"
        
        # Get all files
        all_files = metadata_store.get_all_files()
        
        # Find the PDF file
        pdf_file = None
        for file_info in all_files:
            if target_pdf in file_info.get('file_path', ''):
                pdf_file = file_info
                break
        
        if not pdf_file:
            print(f"❌ PDF file '{target_pdf}' not found in metadata store")
            print(f"📋 Available files:")
            for i, file_info in enumerate(all_files, 1):
                filename = Path(file_info['file_path']).name
                print(f"   {i}. {filename}")
            return
        
        print(f"\n📋 Found PDF File:")
        print(f"   📄 File: {Path(pdf_file['file_path']).name}")
        print(f"   📁 Full Path: {pdf_file['file_path']}")
        print(f"   📊 Chunk Count: {pdf_file.get('chunk_count', 0)}")
        print(f"   📏 File Size: {pdf_file.get('file_size', 'Unknown')} bytes")
        
        # Search for content in FAISS store
        print(f"\n🔎 Searching FAISS store for PDF content...")
        stats = faiss_store.get_stats()
        print(f"   📊 Total vectors in FAISS: {stats.get('total_vectors', 0)}")
        
        # Try multiple search approaches
        embedder = container.get('embedder')
        
        # Search 1: By filename
        print(f"\n🔍 Search 1: Looking for content by filename...")
        query_embedding = embedder.embed_text(target_pdf)
        search_results = faiss_store.search_with_metadata(query_embedding, k=10)
        
        pdf_results = []
        for result in search_results:
            filename = result.get('filename', result.get('source', ''))
            if target_pdf in str(filename) or 'tmp' in str(filename).lower():
                pdf_results.append(result)
        
        if pdf_results:
            print(f"   ✅ Found {len(pdf_results)} results by filename")
            for i, result in enumerate(pdf_results[:3], 1):
                content = result.get('text', result.get('content', 'No content'))
                similarity = result.get('similarity_score', 0)
                source = result.get('filename', result.get('source', 'Unknown'))
                
                print(f"\n   📄 Result {i}:")
                print(f"      📊 Similarity: {similarity:.3f}")
                print(f"      📁 Source: {source}")
                print(f"      📏 Length: {len(content)} characters")
                print(f"      📝 Content:")
                print(f"      {'-' * 40}")
                
                # Show content with proper formatting
                preview = content[:800] if len(content) > 800 else content
                for line in preview.split('\n'):
                    if line.strip():
                        print(f"      {line}")
                
                if len(content) > 800:
                    print(f"      ... (showing first 800 of {len(content)} characters)")
                print(f"      {'-' * 40}")
        else:
            print(f"   ❌ No results found by filename")
        
        # Search 2: By content type
        print(f"\n🔍 Search 2: Looking for PDF content...")
        query_embedding = embedder.embed_text("PDF document content")
        search_results = faiss_store.search_with_metadata(query_embedding, k=10)
        
        print(f"   📋 Top 5 results by content similarity:")
        for i, result in enumerate(search_results[:5], 1):
            content = result.get('text', result.get('content', 'No content'))
            similarity = result.get('similarity_score', 0)
            source = result.get('filename', result.get('source', 'Unknown'))
            
            print(f"\n   📄 Result {i}:")
            print(f"      📊 Similarity: {similarity:.3f}")
            print(f"      📁 Source: {source}")
            print(f"      📝 Content Preview: {content[:150]}{'...' if len(content) > 150 else ''}")
        
        # Search 3: Get all chunks and look for recent ones
        print(f"\n🔍 Search 3: Looking through all chunks...")
        all_chunks = metadata_store.get_all_chunks()
        
        recent_chunks = []
        for chunk in all_chunks:
            chunk_path = chunk.get('file_path', chunk.get('doc_path', ''))
            if target_pdf in str(chunk_path) or 'tmp' in str(chunk_path).lower():
                recent_chunks.append(chunk)
        
        if recent_chunks:
            print(f"   ✅ Found {len(recent_chunks)} chunks in metadata store")
            for i, chunk in enumerate(recent_chunks[:3], 1):
                content = chunk.get('text', chunk.get('content', 'No content'))
                
                print(f"\n   📄 Chunk {i}:")
                print(f"      📏 Length: {len(content)} characters")
                print(f"      📊 Metadata keys: {list(chunk.keys())}")
                print(f"      📝 Content:")
                print(f"      {'-' * 40}")
                
                # Show content
                preview = content[:500] if len(content) > 500 else content
                for line in preview.split('\n'):
                    if line.strip():
                        print(f"      {line}")
                
                if len(content) > 500:
                    print(f"      ... (showing first 500 of {len(content)} characters)")
                print(f"      {'-' * 40}")
        else:
            print(f"   ❌ No chunks found in metadata store")
        
        print(f"\n✅ PDF content analysis completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_pdf_content() 