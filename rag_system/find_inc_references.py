#!/usr/bin/env python3
"""
Find INC references in loaded chunks
"""

import json
import re

def find_inc_references():
    """Find INC references in loaded chunks"""
    
    try:
        with open('data/metadata/chunks_metadata.json', 'r') as f:
            chunks = json.load(f)
        
        print(f"📊 Total chunks: {len(chunks)}")
        
        # Find chunks with INC references
        inc_chunks = []
        for chunk_id, chunk_info in chunks.items():
            content = chunk_info.get('content', '')
            if 'INC' in content:
                inc_chunks.append((chunk_id, chunk_info))
        
        print(f"🔍 Chunks with INC references: {len(inc_chunks)}")
        
        for chunk_id, chunk_info in inc_chunks:
            source = chunk_info.get('source', 'unknown')
            content = chunk_info.get('content', '')
            
            # Find all INC numbers
            inc_numbers = re.findall(r'INC\d+', content)
            
            print(f"\n📄 Chunk: {chunk_id}")
            print(f"   Source: {source}")
            print(f"   INC numbers found: {inc_numbers}")
            print(f"   Content preview: {content[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_inc_references() 