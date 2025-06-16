#!/usr/bin/env python3
"""
Test improved doc_id generation with various metadata scenarios
"""
import requests
import json

def test_scenarios():
    """Test different metadata scenarios"""
    
    scenarios = [
        {
            'name': 'With Title',
            'data': {
                'text': 'Document with title about cloud security.',
                'metadata': {'title': 'Cloud Security Guide', 'author': 'John Doe'}
            }
        },
        {
            'name': 'With Filename (no title)',
            'data': {
                'text': 'Document with filename but no title.',
                'metadata': {'filename': 'network_config.txt', 'author': 'Jane Smith'}
            }
        },
        {
            'name': 'With Description (no title/filename)',
            'data': {
                'text': 'Document with description only.',
                'metadata': {'description': 'Important security procedures for network administrators', 'category': 'security'}
            }
        },
        {
            'name': 'Minimal Metadata (fallback to hash)',
            'data': {
                'text': 'Document with minimal metadata.',
                'metadata': {'author': 'Anonymous'}
            }
        }
    ]
    
    print("=== Testing Improved Doc ID Generation ===\n")
    
    for scenario in scenarios:
        print(f"--- {scenario['name']} ---")
        
        # Ingest document
        response = requests.post('http://localhost:8000/ingest', json=scenario['data'])
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ingestion successful: {result['chunks_created']} chunks created")
        else:
            print(f"❌ Ingestion failed: {response.status_code} - {response.text}")
            continue
        
        print()
    
    # Query to see all the new documents
    print("=== Query Results ===")
    response = requests.post('http://localhost:8000/query', json={
        'query': 'document security network',
        'max_results': 6
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result.get('sources', []))} sources:")
        
        for i, source in enumerate(result.get('sources', [])):
            print(f"\nSource {i+1}:")
            print(f"  doc_id: {source.get('doc_id')}")
            print(f"  text: {source.get('text')[:60]}...")
            
            metadata = source.get('metadata', {})
            print(f"  title: {metadata.get('title', 'N/A')}")
            print(f"  filename: {metadata.get('filename', 'N/A')}")
            print(f"  description: {metadata.get('description', 'N/A')[:50]}{'...' if len(metadata.get('description', '')) > 50 else ''}")
    else:
        print(f"❌ Query failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_scenarios() 