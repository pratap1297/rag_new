#!/usr/bin/env python3
"""Test Vector Deletion Directly"""

import requests
import time

def test_vector_deletion():
    print("Testing Vector Deletion Directly...")
    
    # Get Phoenix vectors
    response = requests.get('http://localhost:8000/manage/vectors?text_search=Phoenix')
    vectors = response.json()
    
    if not vectors:
        print("No Phoenix vectors found")
        return False
    
    print(f"Found {len(vectors)} Phoenix vectors")
    
    # Get vector IDs
    vector_ids = [v['vector_id'] for v in vectors]
    print(f"Vector IDs to delete: {vector_ids}")
    
    # Delete vectors directly
    response = requests.delete('http://localhost:8000/manage/vectors', json=vector_ids)
    print(f"Delete status: {response.status_code}")
    
    if response.status_code == 200:
        time.sleep(2)
        
        # Query again
        response = requests.post('http://localhost:8000/query', json={'query': 'Phoenix-9Z', 'k': 5})
        sources = response.json().get('sources', [])
        still_found = any('Phoenix-9Z' in s.get('text', '') for s in sources)
        
        if not still_found:
            print("SUCCESS: Vectors properly deleted!")
            return True
        else:
            print("FAILED: Vectors still found after deletion")
            return False
    else:
        print(f"Delete failed: {response.text}")
        return False

if __name__ == "__main__":
    success = test_vector_deletion()
    if success:
        print("\nVECTOR DELETION WORKS!")
    else:
        print("\nVECTOR DELETION FAILED!") 