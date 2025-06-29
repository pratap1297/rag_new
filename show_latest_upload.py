#!/usr/bin/env python3
"""
Show Latest Upload Content
Display the extracted content from the most recently uploaded file
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "rag_system"))

def show_latest_upload_content():
    """Show content from the most recently uploaded file"""
    print("📄 Latest Upload Content Analysis")
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
        
        # Get all files and find the most recent
        all_files = metadata_store.get_all_files()
        
        if not all_files:
            print("❌ No files found in the system")
            return
        
        # Sort by file path to find temp files (most recent uploads)
        temp_files = [f for f in all_files if 'tmp' in f.get('file_path', '').lower()]
        
        if temp_files:
            latest_file = temp_files[-1]  # Get the last temp file
        else:
            latest_file = all_files[-1]  # Get the last file overall
        
        print(f"\n📋 Most Recent Upload:")
        print(f"   📄 File: {Path(latest_file['file_path']).name}")
        print(f"   📁 Full Path: {latest_file['file_path']}")
        print(f"   📊 Chunk Count: {latest_file.get('chunk_count', 0)}")
        print(f"   📏 File Size: {latest_file.get('file_size', 'Unknown')} bytes")
        
        # Get all chunks for this file
        all_chunks = metadata_store.get_all_chunks()
        file_chunks = [chunk for chunk in all_chunks 
                      if chunk.get('file_path') == latest_file['file_path'] or 
                         chunk.get('doc_path') == latest_file['file_path']]
        
        print(f"\n🔍 Found {len(file_chunks)} chunks for this file:")
        
        if not file_chunks:
            print("❌ No chunks found for this file")
            
            # Try to search in FAISS store directly
            print("\n🔎 Searching FAISS store for recent content...")
            stats = faiss_store.get_stats()
            print(f"   📊 Total vectors in FAISS: {stats.get('total_vectors', 0)}")
            
            # Search for content related to the filename
            filename = Path(latest_file['file_path']).stem
            try:
                # Get embedder to search
                embedder = container.get('embedder')
                query_embedding = embedder.embed_text(f"content from {filename}")
                
                search_results = faiss_store.search_with_metadata(query_embedding, k=5)
                
                print(f"\n📋 Search results for '{filename}':")
                for i, result in enumerate(search_results[:3], 1):
                    similarity = result.get('similarity_score', 0)
                    content = result.get('text', result.get('content', 'No content'))
                    source = result.get('filename', result.get('source', 'Unknown'))
                    
                    print(f"\n   {i}. Similarity: {similarity:.3f}")
                    print(f"      Source: {source}")
                    print(f"      Content: {content[:300]}{'...' if len(content) > 300 else ''}")
                    
            except Exception as e:
                print(f"   ❌ Search error: {e}")
            
            return
        
        # Display chunks content
        for i, chunk in enumerate(file_chunks[:5], 1):  # Show first 5 chunks
            content = chunk.get('text', chunk.get('content', 'No content available'))
            chunk_index = chunk.get('chunk_index', i-1)
            
            print(f"\n📄 Chunk {chunk_index + 1}:")
            print(f"   📏 Length: {len(content)} characters")
            print(f"   📝 Content Preview:")
            print(f"   {'-' * 40}")
            
            # Show content with line breaks preserved
            preview = content[:500] + "..." if len(content) > 500 else content
            for line in preview.split('\n')[:10]:  # Show first 10 lines
                print(f"   {line}")
            
            if len(content) > 500:
                print(f"   ... (showing first 500 of {len(content)} characters)")
            
            print(f"   {'-' * 40}")
            
            # Show metadata
            print(f"   📊 Metadata:")
            metadata_keys = ['doc_id', 'filename', 'chunk_size', 'embedding_model', 'chunking_method']
            for key in metadata_keys:
                if key in chunk:
                    print(f"      {key}: {chunk[key]}")
        
        if len(file_chunks) > 5:
            print(f"\n... and {len(file_chunks) - 5} more chunks")
        
        # Show full content summary
        total_content = ' '.join([chunk.get('text', chunk.get('content', '')) for chunk in file_chunks])
        print(f"\n📊 Content Summary:")
        print(f"   📏 Total characters: {len(total_content)}")
        print(f"   📝 Total words: {len(total_content.split())}")
        print(f"   📄 Total chunks: {len(file_chunks)}")
        
        # Show content type analysis
        if total_content:
            content_lower = total_content.lower()
            content_indicators = {
                'Technical Document': ['api', 'configuration', 'system', 'network', 'server'],
                'Business Document': ['policy', 'procedure', 'process', 'business', 'management'],
                'Code/Programming': ['function', 'class', 'import', 'def', 'return'],
                'Data/Numbers': any(char.isdigit() for char in total_content[:100]),
                'PDF Content': 'pdf' in content_lower
            }
            
            print(f"\n🔍 Content Type Analysis:")
            for content_type, indicators in content_indicators.items():
                if isinstance(indicators, list):
                    matches = sum(1 for indicator in indicators if indicator in content_lower)
                    if matches > 0:
                        print(f"   📋 {content_type}: {matches} indicators found")
                elif indicators:
                    print(f"   📋 {content_type}: Detected")
        
        print(f"\n✅ Content analysis completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_latest_upload_content() 