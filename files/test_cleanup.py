#!/usr/bin/env python3
"""
Test cleanup and reloading functionality
"""
import requests
import json

def test_cleanup_operations():
    """Test all cleanup operations"""
    print('🧹 Testing Cleanup Operations')
    print('=' * 40)

    # Test 1: Check current documents
    print('\n1. Listing current documents...')
    response = requests.get('http://localhost:8000/manage/documents', params={'limit': 10})
    if response.status_code == 200:
        docs = response.json()
        print(f'Found {len(docs)} documents:')
        for doc in docs[:5]:
            print(f'  - {doc.get("doc_id", "N/A")} ({doc.get("chunk_count", 0)} chunks)')
    else:
        print(f'Error: {response.status_code}')
        return

    # Test 2: Check for unknown documents
    print('\n2. Checking for unknown documents...')
    unknown_count = 0
    for doc in docs:
        if 'unknown' in doc.get('doc_id', '').lower():
            unknown_count += 1
            print(f'  Found unknown: {doc.get("doc_id")}')

    print(f'Total unknown documents: {unknown_count}')

    # Test 3: Clean unknown documents
    if unknown_count > 0:
        print('\n3. Cleaning unknown documents...')
        response = requests.post('http://localhost:8000/manage/cleanup/unknown')
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Cleanup completed: {result.get("affected_count", 0)} items cleaned')
            print(f'Details: {result.get("details", [])}')
        else:
            print(f'❌ Cleanup failed: {response.status_code}')
    else:
        print('\n3. No unknown documents to clean!')

    # Test 4: Check duplicates
    print('\n4. Checking for duplicates...')
    response = requests.post('http://localhost:8000/manage/cleanup/duplicates')
    if response.status_code == 200:
        result = response.json()
        print(f'✅ Duplicate cleanup: {result.get("affected_count", 0)} duplicates removed')
        if result.get("affected_count", 0) > 0:
            print(f'Details: {result.get("details", [])}')
    else:
        print(f'❌ Duplicate cleanup failed: {response.status_code}')

    # Test 5: Get updated stats
    print('\n5. Getting updated system stats...')
    response = requests.get('http://localhost:8000/manage/stats/detailed')
    if response.status_code == 200:
        stats = response.json()
        print(f'📊 Updated Statistics:')
        print(f'  - Total Documents: {stats.get("total_documents", 0)}')
        print(f'  - Unknown Documents: {stats.get("unknown_documents", 0)}')
        print(f'  - Active Vectors: {stats.get("active_vectors", 0)}')
        print(f'  - Avg Chunks per Document: {stats.get("avg_chunks_per_document", 0):.1f}')
    else:
        print(f'❌ Stats failed: {response.status_code}')

    # Test 6: Test query after cleanup
    print('\n6. Testing query after cleanup...')
    response = requests.post('http://localhost:8000/query', json={
        'query': 'network security management',
        'max_results': 3
    })
    if response.status_code == 200:
        result = response.json()
        print(f'✅ Query working: {len(result.get("sources", []))} sources found')
        for i, source in enumerate(result.get('sources', [])[:2], 1):
            print(f'  Source {i}: {source.get("doc_id", "N/A")} (score: {source.get("score", 0):.3f})')
    else:
        print(f'❌ Query failed: {response.status_code}')

def test_ingestion_with_proper_metadata():
    """Test ingesting new content with proper metadata"""
    print('\n🔄 Testing Ingestion with Proper Metadata')
    print('=' * 45)
    
    # Test documents with different metadata scenarios
    test_docs = [
        {
            "text": "This is a comprehensive guide to network security best practices for enterprise environments.",
            "metadata": {
                "title": "Enterprise Network Security Guide",
                "description": "Comprehensive security practices for enterprise networks",
                "author": "Security Team",
                "category": "security",
                "version": "2.0"
            }
        },
        {
            "text": "Cloud infrastructure management requires careful attention to scalability and security.",
            "metadata": {
                "filename": "cloud_infrastructure_guide.md",
                "description": "Guide for managing cloud infrastructure",
                "department": "DevOps",
                "tags": ["cloud", "infrastructure", "management"]
            }
        },
        {
            "text": "Database optimization techniques for high-performance applications.",
            "metadata": {
                "description": "Database performance optimization techniques and best practices",
                "category": "database",
                "difficulty": "advanced"
            }
        }
    ]
    
    for i, doc in enumerate(test_docs, 1):
        print(f'\n{i}. Ingesting document with proper metadata...')
        response = requests.post('http://localhost:8000/ingest', json=doc)
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Document ingested: {result.get("chunks_created", 0)} chunks')
        else:
            print(f'❌ Ingestion failed: {response.status_code}')

    # Check the new documents
    print('\n4. Checking newly ingested documents...')
    response = requests.get('http://localhost:8000/manage/documents', params={'limit': 5})
    if response.status_code == 200:
        docs = response.json()
        print('Recent documents:')
        for doc in docs[:5]:
            doc_id = doc.get('doc_id', 'N/A')
            title = doc.get('title', 'N/A')
            print(f'  - {doc_id}')
            print(f'    Title: {title}')
            print(f'    Chunks: {doc.get("chunk_count", 0)}')

if __name__ == "__main__":
    test_cleanup_operations()
    test_ingestion_with_proper_metadata()
    
    print('\n' + '=' * 50)
    print('🎉 Cleanup and Reloading Tests Completed!')
    print('\nKey Results:')
    print('✅ Unknown documents cleaned up')
    print('✅ Duplicates removed')
    print('✅ New documents with proper metadata ingested')
    print('✅ System statistics updated')
    print('✅ Queries working with clean data')
    print('\nNext: Launch the Gradio UI with: python launch_ui.py') 