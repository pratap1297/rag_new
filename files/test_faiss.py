#!/usr/bin/env python3
"""
Test FAISS Store
"""
import sys
import os
sys.path.append('.')

try:
    print("1. Importing FAISS store...")
    from src.storage.faiss_store import FAISSStore
    print("   ✅ Import successful")
    
    print("2. Creating FAISS store...")
    store = FAISSStore('data/vectors/faiss_index.bin', 1024)
    print("   ✅ FAISS store created")
    
    print("3. Getting stats...")
    stats = store.get_stats()
    print(f"   ✅ Stats: {stats}")
    
    print("4. Testing search...")
    if stats['vector_count'] > 0:
        # Create a dummy query vector
        import numpy as np
        query_vector = np.random.random(1024).tolist()
        results = store.search(query_vector, k=2)
        print(f"   ✅ Search results: {len(results)} found")
    else:
        print("   ℹ️  No vectors to search")
    
    print("\n🎉 All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 