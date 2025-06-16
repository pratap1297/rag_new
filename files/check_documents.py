#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.system_init import initialize_system

def main():
    try:
        # Initialize the system to get proper dependencies
        container = initialize_system()
        metadata_store = container.get('metadata_store')
        files = metadata_store.get_all_files()
        
        print("=== INGESTED DOCUMENTS ===")
        if not files:
            print("No documents found in the system.")
            return
            
        for i, file_info in enumerate(files, 1):
            print(f"\n{i}. File: {file_info['filename']}")
            print(f"   Chunks: {file_info['chunk_count']}")
            print(f"   Size: {file_info['file_size']} bytes")
            print(f"   Upload Date: {file_info.get('upload_date', 'Unknown')}")
            
        print(f"\nTotal Files: {len(files)}")
        
        # Also check chunks for more details
        chunks = metadata_store.get_all_chunks()
        print(f"Total Chunks: {len(chunks)}")
        
        if chunks:
            print("\n=== SAMPLE CHUNK CONTENT ===")
            sample_chunk = chunks[0]
            content_preview = sample_chunk['content'][:200] + "..." if len(sample_chunk['content']) > 200 else sample_chunk['content']
            print(f"Sample from '{sample_chunk['filename']}': {content_preview}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 