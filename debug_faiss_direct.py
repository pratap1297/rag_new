#!/usr/bin/env python3
"""
Debug FAISS Direct
Direct test of the FAISS index to see if vectors are actually stored and searchable
"""
import sys
import os
sys.path.append('rag_system/src')

import numpy as np
from storage.faiss_store import FAISSStore
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_faiss_direct():
    """Debug FAISS store directly"""
    print("🔍 Direct FAISS Index Debug")
    print("=" * 50)
    
    try:
        # Initialize FAISS store with the correct path and dimension
        print("1. 📊 Initializing FAISS store...")
        faiss_store = FAISSStore(
            index_path="rag_system/data/vectors/faiss_index.bin",
            dimension=1024  # Cohere-embed-v3-english dimension
        )
        
        # Get index info
        print("\n2. 📈 FAISS Index Information:")
        index_info = faiss_store.get_index_info()
        
        for key, value in index_info.items():
            print(f"   {key}: {value}")
        
        # Get stats
        print("\n3. 📊 FAISS Store Statistics:")
        stats = faiss_store.get_stats()
        
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Check if index has vectors
        total_vectors = index_info.get('total_vectors', 0)
        print(f"\n4. 🔍 Vector Analysis:")
        print(f"   Total vectors in index: {total_vectors}")
        
        if total_vectors == 0:
            print("   ❌ No vectors found in FAISS index!")
            print("   This explains why queries return no results.")
            print("   The vectors may not have been properly saved to the index.")
            return False
        
        # Test direct search
        print(f"\n5. 🧪 Direct Search Test:")
        
        # Create a random query vector (1024 dimensions for Cohere)
        query_vector = np.random.random(1024).tolist()
        
        print(f"   Testing with random query vector (dimension: {len(query_vector)})")
        
        # Perform search
        results = faiss_store.search_with_metadata(query_vector, k=10)
        
        print(f"   📚 Search results: {len(results)} found")
        
        if results:
            print(f"   ✅ SUCCESS: FAISS search is working!")
            
            # Show first few results
            for i, result in enumerate(results[:3], 1):
                print(f"\n   📄 Result {i}:")
                print(f"      Vector ID: {result.get('vector_id', 'Unknown')}")
                print(f"      Doc ID: {result.get('doc_id', 'Unknown')}")
                print(f"      Similarity: {result.get('similarity_score', 0):.6f}")
                print(f"      Content preview: {result.get('content', '')[:100]}...")
            
            return True
        else:
            print(f"   ❌ No results from direct search")
            print(f"   This indicates an issue with the search mechanism itself")
            return False
            
    except Exception as e:
        print(f"❌ Error during FAISS debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_faiss_files():
    """Check FAISS files directly"""
    print("\n6. 📁 FAISS File Analysis:")
    
    faiss_files = [
        "rag_system/data/vectors/faiss_index.bin",
        "rag_system/data/vectors/vector_metadata.pkl"
    ]
    
    for file_path in faiss_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {file_path}: {file_size:,} bytes")
        else:
            print(f"   ❌ {file_path}: NOT FOUND")
    
    # Try to load the pickle file directly
    try:
        import pickle
        with open("rag_system/data/vectors/vector_metadata.pkl", 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"\n   📊 Metadata analysis:")
        print(f"      Type: {type(metadata)}")
        
        if isinstance(metadata, dict):
            print(f"      Keys: {list(metadata.keys())}")
            
            if 'id_to_metadata' in metadata:
                id_to_metadata = metadata['id_to_metadata']
                print(f"      Total metadata entries: {len(id_to_metadata)}")
                
                # Show a few entries
                for i, (vector_id, meta) in enumerate(list(id_to_metadata.items())[:3]):
                    print(f"      Entry {i+1}: ID={vector_id}, metadata keys={list(meta.keys()) if meta else 'None'}")
                    
    except Exception as e:
        print(f"   ❌ Error reading metadata: {e}")

if __name__ == "__main__":
    print("🔧 Starting Direct FAISS Debug...")
    
    success = debug_faiss_direct()
    debug_faiss_files()
    
    if success:
        print(f"\n✅ FAISS index is working correctly!")
        print(f"   The issue may be in the query processing pipeline or embedding generation.")
    else:
        print(f"\n❌ FAISS index has issues!")
        print(f"   Either no vectors are stored or the search mechanism is broken.")
    
    print(f"\n💡 Summary:")
    print(f"   - Check if vectors were properly ingested and saved")
    print(f"   - Verify embedding model consistency")
    print(f"   - Ensure FAISS index is being loaded correctly by the query engine") 