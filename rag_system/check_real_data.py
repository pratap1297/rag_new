#!/usr/bin/env python3
"""
Check real data in chunks using the correct 'text' field
"""

import json
import os

def check_real_data():
    """Check real data in chunks"""
    
    print("🔍 Checking Real Data in Chunks")
    print("=" * 60)
    
    chunks_path = 'data/metadata/chunks_metadata.json'
    if not os.path.exists(chunks_path):
        print(f"❌ Chunks metadata not found: {chunks_path}")
        return
    
    try:
        with open(chunks_path, 'r') as f:
            chunks = json.load(f)
        
        print(f"📊 Total chunks: {len(chunks)}")
        
        # Check for content in 'text' field
        total_text_length = 0
        chunks_with_text = 0
        
        for chunk_id, chunk_info in chunks.items():
            text = chunk_info.get('text', '')
            text_length = len(text)
            total_text_length += text_length
            
            if text_length > 0:
                chunks_with_text += 1
                print(f"\n📄 Chunk with text: {chunk_id}")
                print(f"   Source: {chunk_info.get('doc_id', 'unknown')}")
                print(f"   Text length: {text_length}")
                print(f"   Text preview: {text[:300]}...")
                
                # Check for ServiceNow incidents
                if 'INC' in text:
                    inc_count = text.count('INC')
                    print(f"   🔍 ServiceNow incidents found: {inc_count}")
                
                # Check for employee references
                if 'EMP' in text:
                    emp_count = text.count('EMP')
                    print(f"   👥 Employee references found: {emp_count}")
        
        print(f"\n📋 Summary:")
        print(f"   Chunks with text: {chunks_with_text}/{len(chunks)}")
        print(f"   Total text length: {total_text_length} characters")
        
        if chunks_with_text == 0:
            print(f"\n⚠️  No chunks have text - vector database may be empty")
        else:
            print(f"\n✅ Found {chunks_with_text} chunks with real data!")
            
            # Count total ServiceNow incidents
            total_incidents = 0
            for chunk_info in chunks.values():
                text = chunk_info.get('text', '')
                if 'INC' in text:
                    total_incidents += text.count('INC')
            
            print(f"📊 Total ServiceNow incidents across all chunks: {total_incidents}")
        
    except Exception as e:
        print(f"❌ Error checking chunks: {e}")

if __name__ == "__main__":
    check_real_data() 