#!/usr/bin/env python3
"""
Check sources in chunks metadata
"""

import json

def check_sources():
    """Check what sources are referenced in chunks"""
    
    try:
        with open('data/metadata/chunks_metadata.json', 'r') as f:
            chunks = json.load(f)
        
        print(f"📊 Total chunks: {len(chunks)}")
        
        # Get unique sources
        sources = set()
        for chunk_info in chunks.values():
            sources.add(chunk_info.get('source', 'unknown'))
        
        print(f"🔍 Sources found: {len(sources)}")
        for source in sorted(sources):
            print(f"  - {source}")
        
        # Check for specific sources mentioned in the LLM response
        print(f"\n🔍 Looking for sources mentioned in LLM response:")
        target_sources = ['Source1', 'Source2', 'Source3', 'tmpy02u39wb.pdf']
        
        for target in target_sources:
            found = any(target in chunk_info.get('source', '') for chunk_info in chunks.values())
            print(f"  {target}: {'✅ Found' if found else '❌ Not found'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_sources() 