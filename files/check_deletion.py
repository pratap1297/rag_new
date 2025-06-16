#!/usr/bin/env python3
"""Check Deletion Status"""

import requests

def check_deletion_status():
    print("Checking deletion status...")
    
    # Get all documents
    response = requests.get('http://localhost:8000/manage/documents')
    docs = response.json()
    
    # Find Phoenix documents
    phoenix_docs = []
    for doc in docs:
        doc_id = doc.get('doc_id', '')
        metadata = doc.get('metadata', {})
        if 'Phoenix' in doc_id or 'Phoenix' in str(metadata):
            phoenix_docs.append(doc)
    
    print(f"Found {len(phoenix_docs)} Phoenix documents:")
    for doc in phoenix_docs[:10]:  # Show first 10
        doc_id = doc.get('doc_id', '')
        deleted = doc.get('metadata', {}).get('deleted', False)
        print(f"  {doc_id}: deleted={deleted}")
    
    # Also check vectors directly
    print("\nChecking vectors...")
    response = requests.get('http://localhost:8000/manage/vectors?text_search=Phoenix')
    vectors = response.json()
    print(f"Found {len(vectors)} Phoenix vectors:")
    for vector in vectors[:5]:  # Show first 5
        vector_id = vector.get('vector_id', '')
        doc_id = vector.get('doc_id', '')
        deleted = vector.get('metadata', {}).get('deleted', False)
        print(f"  Vector {vector_id} (doc: {doc_id}): deleted={deleted}")

if __name__ == "__main__":
    check_deletion_status() 