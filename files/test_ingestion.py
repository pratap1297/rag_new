#!/usr/bin/env python3
"""
Test ingestion with proper metadata
"""
import requests
import json

def test_ingestion_with_title():
    """Test ingesting text with proper title"""
    print("=== Testing ingestion with title ===")
    
    response = requests.post('http://localhost:8000/ingest', json={
        'text': 'This is a test document about network security protocols and best practices.',
        'metadata': {
            'title': 'Test Security Doc',
            'author': 'Test User',
            'category': 'security'
        }
    })
    
    if response.status_code == 200:
        result = response.json()
        print("Ingestion successful:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Ingestion failed: {response.status_code} - {response.text}")

def test_ingestion_without_title():
    """Test ingesting text without title"""
    print("\n=== Testing ingestion without title ===")
    
    response = requests.post('http://localhost:8000/ingest', json={
        'text': 'This is another test document without a title.',
        'metadata': {
            'author': 'Test User',
            'category': 'test'
        }
    })
    
    if response.status_code == 200:
        result = response.json()
        print("Ingestion successful:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Ingestion failed: {response.status_code} - {response.text}")

def test_query_after_ingestion():
    """Test query to see the new documents"""
    print("\n=== Testing query after ingestion ===")
    
    response = requests.post('http://localhost:8000/query', json={
        'query': 'test document security',
        'max_results': 3
    })
    
    if response.status_code == 200:
        result = response.json()
        print("Query results:")
        for i, source in enumerate(result.get('sources', [])):
            print(f"\nSource {i+1}:")
            print(f"  doc_id: {source.get('doc_id')}")
            print(f"  text: {source.get('text')}")
            print(f"  metadata title: {source.get('metadata', {}).get('title', 'NO TITLE')}")
    else:
        print(f"Query failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_ingestion_with_title()
    test_ingestion_without_title()
    test_query_after_ingestion() 