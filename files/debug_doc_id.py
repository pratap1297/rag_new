#!/usr/bin/env python3
"""
Debug script to understand doc_id issue
"""
import requests
import json

def test_query():
    """Test query and show response structure"""
    try:
        response = requests.post('http://localhost:8000/query', 
                               json={'query': 'network security', 'max_results': 2})
        
        if response.status_code == 200:
            result = response.json()
            print("=== QUERY RESPONSE ===")
            print(json.dumps(result, indent=2))
            
            print("\n=== SOURCE ANALYSIS ===")
            for i, source in enumerate(result.get('sources', [])):
                print(f"\nSource {i+1}:")
                print(f"  doc_id: {source.get('doc_id', 'NOT FOUND')}")
                print(f"  score: {source.get('score', 'NOT FOUND')}")
                print(f"  text preview: {source.get('text', 'NOT FOUND')[:100]}...")
                
                metadata = source.get('metadata', {})
                print(f"  metadata keys: {list(metadata.keys())}")
                
                # Check for various possible doc_id fields
                possible_doc_fields = ['doc_id', 'document_id', 'file_id', 'filename', 'title', 'source']
                for field in possible_doc_fields:
                    if field in metadata:
                        print(f"  metadata.{field}: {metadata[field]}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_stats():
    """Test stats to understand data structure"""
    try:
        response = requests.get('http://localhost:8000/stats')
        if response.status_code == 200:
            stats = response.json()
            print("\n=== SYSTEM STATS ===")
            print(json.dumps(stats, indent=2))
        else:
            print(f"Stats Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Stats Error: {e}")

if __name__ == "__main__":
    test_query()
    test_stats() 