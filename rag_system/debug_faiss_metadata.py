#!/usr/bin/env python3
"""
Debug script to examine FAISS store metadata
"""

import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.storage.faiss_store import FAISSStore

def debug_faiss_metadata():
    """Debug the metadata stored in FAISS"""
    
    print("🔍 Debugging FAISS Metadata")
    print("=" * 50)
    
    # Initialize components
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Initialize FAISS store
    faiss_store = FAISSStore(
        index_path="data/vectors/index.faiss",
        dimension=config.embedding.dimension
    )
    
    # Get all metadata
    all_metadata = faiss_store.get_all_metadata()
    
    print(f"📊 Total vectors in FAISS: {len(all_metadata)}")
    
    for vector_id, metadata in all_metadata.items():
        print(f"\n🔗 Vector {vector_id}:")
        print(f"    doc_id: {metadata.get('doc_id', 'N/A')}")
        print(f"    original_filename: {metadata.get('original_filename', 'N/A')}")
        print(f"    filename: {metadata.get('filename', 'N/A')}")
        print(f"    file_path: {metadata.get('file_path', 'N/A')}")
        print(f"    text preview: {metadata.get('text', 'N/A')[:100]}...")
        
        # Check if this is our test data
        if 'Maria Garcia' in metadata.get('text', ''):
            print(f"    🎯 This is our test data!")
            if metadata.get('original_filename') == 'Manager_Roster_2024.txt':
                print(f"    ✅ Original filename is correct!")
            else:
                print(f"    ❌ Original filename is wrong: {metadata.get('original_filename')}")

if __name__ == "__main__":
    debug_faiss_metadata() 