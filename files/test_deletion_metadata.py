#!/usr/bin/env python3
"""Test Deletion Metadata"""

import requests
import time

def test_deletion_metadata():
    print("Testing Deletion Metadata...")
    
    # Upload test document
    response = requests.post('http://localhost:8000/ingest', json={
        'text': 'Phoenix-9Z-UNIQUE-TEST-12345 test document for deletion testing', 
        'metadata': {'title': 'Unique Phoenix Test Doc'}
    })
    print(f"Upload status: {response.status_code}")
    
    if response.status_code == 200:
        time.sleep(2)
        
        # Get all vectors and find our test vectors
        response = requests.get('http://localhost:8000/manage/vectors?limit=1000')
        all_vectors = response.json()
        
        test_vectors = []
        for vector in all_vectors:
            if 'Phoenix-9Z-UNIQUE-TEST-12345' in vector.get('text_preview', ''):
                test_vectors.append(vector)
        
        print(f"Found {len(test_vectors)} test vectors before deletion")
        
        if test_vectors:
            vector_ids = [v['vector_id'] for v in test_vectors]
            print(f"Test vector IDs: {vector_ids}")
            
            # Delete vectors
            response = requests.delete('http://localhost:8000/manage/vectors', json=vector_ids)
            print(f"Delete status: {response.status_code}")
            
            time.sleep(2)
            
            # Check if vectors are still listed (they shouldn't be)
            response = requests.get('http://localhost:8000/manage/vectors?limit=1000')
            all_vectors_after = response.json()
            
            test_vectors_after = []
            for vector in all_vectors_after:
                if 'Phoenix-9Z-UNIQUE-TEST-12345' in vector.get('text_preview', ''):
                    test_vectors_after.append(vector)
            
            print(f"Found {len(test_vectors_after)} test vectors after deletion in management API")
            
            # Now check if they appear in search results
            response = requests.post('http://localhost:8000/query', json={
                'query': 'Phoenix-9Z-UNIQUE-TEST-12345', 
                'k': 10
            })
            search_results = response.json().get('sources', [])
            
            test_in_search = []
            for source in search_results:
                if 'Phoenix-9Z-UNIQUE-TEST-12345' in source.get('text', ''):
                    test_in_search.append(source)
            
            print(f"Found {len(test_in_search)} test vectors in search results")
            
            if len(test_vectors_after) == 0 and len(test_in_search) == 0:
                print("SUCCESS: Vectors properly deleted from both management API and search!")
                return True
            elif len(test_vectors_after) == 0 and len(test_in_search) > 0:
                print("PARTIAL: Vectors deleted from management API but still in search results")
                print("This suggests the server needs to be restarted for search changes to take effect")
                return False
            else:
                print("FAILED: Vectors still found in management API")
                return False
        else:
            print("No test vectors found")
            return False
    else:
        print(f"Upload failed: {response.text}")
        return False

if __name__ == "__main__":
    success = test_deletion_metadata()
    if success:
        print("\nDELETION FIX VERIFIED!")
    else:
        print("\nDELETION NEEDS SERVER RESTART OR HAS OTHER ISSUES!") 