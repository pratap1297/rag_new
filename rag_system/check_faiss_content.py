#!/usr/bin/env python3
"""
Check what content is actually stored in FAISS vector store
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from storage.faiss_store import FAISSStore

def check_faiss_content():
    """Check content stored in FAISS"""
    try:
        # Load the FAISS store
        store = FAISSStore('data/vectors/faiss_index.bin', dimension=1024)
        print(f'📊 Total vectors in FAISS: {store.optimized_index.index.ntotal}')
        
        print(f'\n📋 All stored content:')
        
        # Check all metadata
        for i, (vector_id, metadata) in enumerate(store.id_to_metadata.items()):
            print(f'\n📄 Vector {i+1} (ID: {vector_id}):')
            
            # Get text content
            text_content = metadata.get('text', '')
            print(f'   📝 Content length: {len(text_content)} characters')
            
            # Show preview
            if text_content:
                preview = text_content[:200] + '...' if len(text_content) > 200 else text_content
                print(f'   👀 Content preview: {preview}')
            else:
                print(f'   ❌ No text content found')
            
            # Show source info
            file_path = metadata.get('file_path', 'N/A')
            doc_path = metadata.get('doc_path', 'N/A')
            print(f'   📁 File path: {file_path}')
            print(f'   📂 Doc path: {doc_path}')
            
            # Show metadata keys
            print(f'   🔑 Metadata keys: {list(metadata.keys())}')
            
            # Check for recent temp files
            if 'tmp' in str(metadata):
                print(f'   🔥 Recent temp file detected!')
                
        return True
        
    except Exception as e:
        print(f'❌ Error checking FAISS content: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Checking FAISS vector store content...\n")
    check_faiss_content() 