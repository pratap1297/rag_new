#!/usr/bin/env python3
"""
Simple debug script to check vector database
"""

import json
import os

def check_vector_database():
    """Check what's in the vector database"""
    
    print("🔍 Checking Vector Database Contents")
    print("=" * 50)
    
    # Check vector mappings
    mappings_path = 'data/metadata/vector_mappings.json'
    if os.path.exists(mappings_path):
        with open(mappings_path, 'r') as f:
            mappings = json.load(f)
        
        print(f"📊 Total vector mappings: {len(mappings)}")
        
        # Find ServiceNow related mappings
        servicenow_mappings = []
        for vector_id, mapping in mappings.items():
            doc_id = mapping.get('doc_id', '')
            if 'ServiceNow' in doc_id:
                servicenow_mappings.append((vector_id, mapping))
        
        print(f"🔍 ServiceNow mappings found: {len(servicenow_mappings)}")
        
        for vector_id, mapping in servicenow_mappings:
            doc_id = mapping.get('doc_id', '')
            chunk_id = mapping.get('chunk_id', '')
            created_at = mapping.get('created_at', '')
            print(f"  Vector ID {vector_id}: {doc_id}")
            print(f"    Chunk ID: {chunk_id}")
            print(f"    Created: {created_at}")
            print()
    
    # Check chunks metadata
    chunks_path = 'data/metadata/chunks_metadata.json'
    if os.path.exists(chunks_path):
        with open(chunks_path, 'r') as f:
            chunks = json.load(f)
        
        print(f"📋 Total chunks: {len(chunks)}")
        
        # Find ServiceNow related chunks
        servicenow_chunks = []
        for chunk_id, chunk_info in chunks.items():
            source = chunk_info.get('source', '')
            if 'ServiceNow' in source:
                servicenow_chunks.append((chunk_id, chunk_info))
        
        print(f"🔍 ServiceNow chunks found: {len(servicenow_chunks)}")
        
        for chunk_id, chunk_info in servicenow_chunks:
            source = chunk_info.get('source', '')
            content = chunk_info.get('content', '')
            print(f"  Chunk {chunk_id}")
            print(f"    Source: {source}")
            print(f"    Content preview: {content[:200]}...")
            print()
    
    # Check if FAISS index exists
    faiss_path = 'data/vectors/faiss_index.bin'
    if os.path.exists(faiss_path):
        size = os.path.getsize(faiss_path)
        print(f"✅ FAISS index exists: {size} bytes")
    else:
        print("❌ FAISS index not found")

if __name__ == "__main__":
    check_vector_database() 