#!/usr/bin/env python3
"""
Check loaded documents for ServiceNow incident references
"""

import json
import os

def check_loaded_documents():
    """Check which documents are loaded and contain ServiceNow incidents"""
    
    print("🔍 Checking Loaded Documents for ServiceNow Incidents")
    print("=" * 60)
    
    # Check files metadata
    metadata_path = 'data/metadata/files_metadata.json'
    if not os.path.exists(metadata_path):
        print(f"❌ Metadata file not found: {metadata_path}")
        return
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        print(f"📊 Total files in vector database: {len(data)}")
        
        # Find files that might contain ServiceNow incidents
        servicenow_files = []
        for file_id, file_info in data.items():
            filename = file_info.get('original_filename', file_info.get('filename', ''))
            if any(keyword in filename.lower() for keyword in ['servicenow', 'incident', 'ticket']):
                servicenow_files.append((file_id, file_info))
        
        print(f"🔍 ServiceNow-related files found: {len(servicenow_files)}")
        
        for file_id, file_info in servicenow_files:
            filename = file_info.get('original_filename', file_info.get('filename', ''))
            vector_ids = file_info.get('vector_ids', [])
            chunk_count = file_info.get('chunk_count', 0)
            print(f"  📄 {filename}")
            print(f"     File ID: {file_id}")
            print(f"     Vector IDs: {len(vector_ids)}")
            print(f"     Chunk Count: {chunk_count}")
            print()
        
        # Check chunks metadata for ServiceNow content
        chunks_path = 'data/metadata/chunks_metadata.json'
        if os.path.exists(chunks_path):
            with open(chunks_path, 'r') as f:
                chunks_data = json.load(f)
            
            print(f"📋 Total chunks in metadata: {len(chunks_data)}")
            
            # Find chunks with ServiceNow incident references
            servicenow_chunks = []
            for chunk_id, chunk_info in chunks_data.items():
                content = chunk_info.get('content', '')
                source = chunk_info.get('source', '')
                
                # Look for incident numbers
                if any(keyword in content for keyword in ['INC', 'incident', 'ServiceNow']):
                    servicenow_chunks.append((chunk_id, chunk_info))
            
            print(f"🔍 Chunks with ServiceNow references: {len(servicenow_chunks)}")
            
            for chunk_id, chunk_info in servicenow_chunks:
                source = chunk_info.get('source', '')
                content = chunk_info.get('content', '')
                
                # Count incident numbers in this chunk
                incident_count = content.count('INC')
                print(f"  📄 Chunk {chunk_id}")
                print(f"     Source: {source}")
                print(f"     Incident references: {incident_count}")
                print(f"     Content preview: {content[:200]}...")
                print()
        
    except Exception as e:
        print(f"❌ Error checking documents: {e}")

if __name__ == "__main__":
    check_loaded_documents() 