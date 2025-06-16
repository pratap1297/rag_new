#!/usr/bin/env python3
"""Check Vector Deletion Status"""

import requests

def check_vectors():
    print("Checking vector deletion status...")
    
    # Get Phoenix vectors
    response = requests.get('http://localhost:8000/manage/vectors?text_search=Phoenix')
    vectors = response.json()
    
    print(f"Found {len(vectors)} Phoenix vectors:")
    for vector in vectors[:5]:
        vector_id = vector.get('vector_id')
        deleted = vector.get('metadata', {}).get('deleted', False)
        text_preview = vector.get('text_preview', '')[:50]
        print(f"  Vector {vector_id}: deleted={deleted}, text='{text_preview}...'")

if __name__ == "__main__":
    check_vectors() 