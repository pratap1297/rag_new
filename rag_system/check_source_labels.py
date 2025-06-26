#!/usr/bin/env python3
"""
Check source labels and identify why generic names are shown
"""

import json
import os

def check_source_labels():
    """Check how sources are labeled"""
    
    print("🔍 Checking Source Labels")
    print("=" * 50)
    
    # Check chunks metadata
    chunks_path = 'data/metadata/chunks_metadata.json'
    if os.path.exists(chunks_path):
        with open(chunks_path, 'r') as f:
            chunks = json.load(f)
        
        print(f"📊 Total chunks: {len(chunks)}")
        print("\n📄 Chunk source information:")
        
        for chunk_id, chunk_info in chunks.items():
            doc_id = chunk_info.get('doc_id', 'N/A')
            source = chunk_info.get('source', 'N/A')
            file_id = chunk_info.get('file_id', 'N/A')
            
            print(f"  Chunk {chunk_id}:")
            print(f"    doc_id: {doc_id}")
            print(f"    source: {source}")
            print(f"    file_id: {file_id}")
            print()
    
    # Check files metadata to see actual file names
    files_path = 'data/metadata/files_metadata.json'
    if os.path.exists(files_path):
        with open(files_path, 'r') as f:
            files = json.load(f)
        
        print(f"📁 Files metadata ({len(files)} files):")
        
        for file_id, file_info in files.items():
            original_filename = file_info.get('original_filename', 'N/A')
            filename = file_info.get('filename', 'N/A')
            vector_ids = file_info.get('vector_ids', [])
            
            print(f"  File ID {file_id}:")
            print(f"    original_filename: {original_filename}")
            print(f"    filename: {filename}")
            print(f"    vector_ids: {vector_ids}")
            print()
    
    # Check vector mappings
    mappings_path = 'data/metadata/vector_mappings.json'
    if os.path.exists(mappings_path):
        with open(mappings_path, 'r') as f:
            mappings = json.load(f)
        
        print(f"🔗 Vector mappings ({len(mappings)} mappings):")
        
        for vector_id, mapping in mappings.items():
            doc_id = mapping.get('doc_id', 'N/A')
            filename = mapping.get('filename', 'N/A')
            chunk_id = mapping.get('chunk_id', 'N/A')
            
            print(f"  Vector {vector_id}:")
            print(f"    doc_id: {doc_id}")
            print(f"    filename: {filename}")
            print(f"    chunk_id: {chunk_id}")
            print()

if __name__ == "__main__":
    check_source_labels() 