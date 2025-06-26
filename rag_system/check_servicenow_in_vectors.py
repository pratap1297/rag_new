#!/usr/bin/env python3
"""
Check if ServiceNow incidents are in the vector database
"""

import json
import os

def check_servicenow_in_vectors():
    """Check if ServiceNow incidents are in the vector database"""
    
    # Check files metadata
    metadata_path = 'data/metadata/files_metadata.json'
    if not os.path.exists(metadata_path):
        print(f"❌ Metadata file not found: {metadata_path}")
        return
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        print(f"📊 Total files in metadata: {len(data)}")
        
        # Find ServiceNow related files
        servicenow_files = []
        for file_id, file_info in data.items():
            filename = file_info.get('original_filename', file_info.get('filename', ''))
            if 'ServiceNow' in filename or 'servicenow' in filename.lower():
                servicenow_files.append((file_id, file_info))
        
        print(f"🔍 ServiceNow files found: {len(servicenow_files)}")
        
        for file_id, file_info in servicenow_files:
            filename = file_info.get('original_filename', file_info.get('filename', ''))
            vector_ids = file_info.get('vector_ids', [])
            chunk_count = file_info.get('chunk_count', 0)
            print(f"  📄 {filename}")
            print(f"     File ID: {file_id}")
            print(f"     Vector IDs: {vector_ids}")
            print(f"     Chunk Count: {chunk_count}")
            print()
        
        # Check chunks metadata
        chunks_path = 'data/metadata/chunks_metadata.json'
        if os.path.exists(chunks_path):
            with open(chunks_path, 'r') as f:
                chunks_data = json.load(f)
            
            print(f"📋 Total chunks in metadata: {len(chunks_data)}")
            
            # Find ServiceNow related chunks
            servicenow_chunks = []
            for chunk_id, chunk_info in chunks_data.items():
                source = chunk_info.get('source', '')
                if 'ServiceNow' in source or 'servicenow' in source.lower():
                    servicenow_chunks.append((chunk_id, chunk_info))
            
            print(f"🔍 ServiceNow chunks found: {len(servicenow_chunks)}")
            
            for chunk_id, chunk_info in servicenow_chunks:
                source = chunk_info.get('source', '')
                content_preview = chunk_info.get('content', '')[:100] + '...'
                print(f"  📄 Chunk {chunk_id}")
                print(f"     Source: {source}")
                print(f"     Content: {content_preview}")
                print()
        
    except Exception as e:
        print(f"❌ Error checking vector database: {e}")

if __name__ == "__main__":
    check_servicenow_in_vectors() 