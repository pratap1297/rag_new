#!/usr/bin/env python3
"""
Check all chunks in the vector database
"""

import json
import os

def check_all_chunks():
    """Check all chunks in the vector database"""
    
    print("🔍 Checking All Chunks in Vector Database")
    print("=" * 60)
    
    chunks_path = 'data/metadata/chunks_metadata.json'
    if not os.path.exists(chunks_path):
        print(f"❌ Chunks metadata not found: {chunks_path}")
        return
    
    try:
        with open(chunks_path, 'r') as f:
            chunks = json.load(f)
        
        print(f"📊 Total chunks: {len(chunks)}")
        print()
        
        for i, (chunk_id, chunk_info) in enumerate(chunks.items(), 1):
            source = chunk_info.get('source', 'unknown')
            content = chunk_info.get('content', '')
            
            print(f"{i}. Chunk ID: {chunk_id}")
            print(f"   Source: {source}")
            print(f"   Content length: {len(content)} characters")
            print(f"   Content preview: {content[:150]}...")
            
            # Check for specific keywords
            keywords = ['ServiceNow', 'incident', 'INC', 'ticket', 'network']
            found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            if found_keywords:
                print(f"   Keywords found: {found_keywords}")
            
            print()
        
    except Exception as e:
        print(f"❌ Error checking chunks: {e}")

if __name__ == "__main__":
    check_all_chunks() 