#!/usr/bin/env python3
"""Test Document Deletion Fix"""

import requests
import time

def test_deletion():
    print("Testing Document Deletion Fix...")
    
    # Upload test document
    response = requests.post('http://localhost:8000/ingest', json={
        'text': 'Phoenix-9Z test document for deletion testing', 
        'metadata': {'title': 'Test Phoenix Doc'}
    })
    print(f"Upload status: {response.status_code}")
    
    if response.status_code == 200:
        time.sleep(2)
        
        # Query for document
        response = requests.post('http://localhost:8000/query', json={'query': 'Phoenix-9Z', 'k': 5})
        sources = response.json().get('sources', [])
        docs = [s['doc_id'] for s in sources if 'Phoenix-9Z' in s.get('text', '')]
        print(f"Found docs before deletion: {docs}")
        
        if docs:
            # Delete documents
            response = requests.delete('http://localhost:8000/manage/documents', json=docs)
            print(f"Delete status: {response.status_code}")
            
            time.sleep(2)
            
            # Query again
            response = requests.post('http://localhost:8000/query', json={'query': 'Phoenix-9Z', 'k': 5})
            sources = response.json().get('sources', [])
            still_found = any('Phoenix-9Z' in s.get('text', '') for s in sources)
            
            if not still_found:
                print("SUCCESS: Document properly deleted!")
                return True
            else:
                print("FAILED: Document still found after deletion")
                return False
        else:
            print("No documents found to delete")
            return False
    else:
        print(f"Upload failed: {response.text}")
        return False

if __name__ == "__main__":
    success = test_deletion()
    if success:
        print("\nDELETION FIX VERIFIED!")
    else:
        print("\nDELETION BUG STILL EXISTS!") 