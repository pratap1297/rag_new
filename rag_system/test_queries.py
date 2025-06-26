#!/usr/bin/env python3
"""
Test queries to see what data is available
"""

import json
import os

def test_queries():
    """Test various queries to see what data is available"""
    
    print("🔍 Testing Queries and Data Availability")
    print("=" * 60)
    
    # Check chunks metadata
    chunks_path = 'data/metadata/chunks_metadata.json'
    if os.path.exists(chunks_path):
        with open(chunks_path, 'r') as f:
            chunks = json.load(f)
        
        print(f"📊 Total chunks: {len(chunks)}")
        
        # Check for content
        total_content_length = 0
        chunks_with_content = 0
        
        for chunk_id, chunk_info in chunks.items():
            content = chunk_info.get('content', '')
            content_length = len(content)
            total_content_length += content_length
            
            if content_length > 0:
                chunks_with_content += 1
                print(f"\n📄 Chunk with content: {chunk_id}")
                print(f"   Source: {chunk_info.get('source', 'unknown')}")
                print(f"   Content length: {content_length}")
                print(f"   Content preview: {content[:200]}...")
        
        print(f"\n📋 Summary:")
        print(f"   Chunks with content: {chunks_with_content}/{len(chunks)}")
        print(f"   Total content length: {total_content_length} characters")
        
        if chunks_with_content == 0:
            print(f"\n⚠️  No chunks have content - vector database may be empty")
        else:
            print(f"\n✅ Found {chunks_with_content} chunks with content")
    
    # Check files metadata
    files_path = 'data/metadata/files_metadata.json'
    if os.path.exists(files_path):
        with open(files_path, 'r') as f:
            files = json.load(f)
        
        print(f"\n📁 Files in metadata: {len(files)}")
        
        # Show some file names
        file_names = []
        for file_info in files.values():
            name = file_info.get('original_filename', file_info.get('filename', 'unknown'))
            file_names.append(name)
        
        print(f"📄 Sample files:")
        for name in file_names[:10]:  # Show first 10
            print(f"   - {name}")
        
        if len(file_names) > 10:
            print(f"   ... and {len(file_names) - 10} more files")

if __name__ == "__main__":
    test_queries() 