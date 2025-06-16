#!/usr/bin/env python3
"""
Test Document Deletion Fix
Tests that documents are properly deleted and no longer appear in query results
"""

import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_document_deletion_fix():
    """Test that document deletion properly removes documents from query results"""
    
    print("🧪 Testing Document Deletion Fix")
    print("=" * 50)
    
    # Test document with unique content
    test_doc_content = """
    Project Quantum-Phoenix-9Z is a top-secret neural encryption protocol developed by Dr. Elena Vasquez 
    at Aurora Labs. The protocol uses a unique 923-bit neural key length and requires specialized 
    Neural Flux Processors (NFP-2024) costing $3.7 million each. The emergency protocol activation 
    code is PHOENIX-NINE-Z-GAMMA-TWELVE-TWELVE-FIVE and requires Level-9 security clearance.
    """
    
    try:
        # Step 1: Add the test document
        print("\n📝 Step 1: Adding test document...")
        upload_data = {
            "text": test_doc_content,
            "metadata": {
                "title": "Project Quantum-Phoenix-9Z Documentation",
                "source": "deletion_test",
                "test_id": "deletion_fix_test"
            }
        }
        
        response = requests.post(f"{API_BASE_URL}/ingest/text", json=upload_data)
        if response.status_code != 200:
            print(f"❌ Failed to upload document: {response.status_code}")
            print(response.text)
            return False
        
        upload_result = response.json()
        print(f"✅ Document uploaded successfully: {upload_result}")
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Step 2: Query for the document to confirm it exists
        print("\n🔍 Step 2: Querying for the document...")
        query_data = {
            "query": "What is Project Quantum-Phoenix-9Z and who developed it?",
            "k": 5
        }
        
        response = requests.post(f"{API_BASE_URL}/query", json=query_data)
        if response.status_code != 200:
            print(f"❌ Query failed: {response.status_code}")
            return False
        
        query_result = response.json()
        print(f"📊 Query result: Found {len(query_result.get('sources', []))} sources")
        
        # Check if our test document is in the results
        found_phoenix = False
        doc_ids_to_delete = set()
        
        for source in query_result.get('sources', []):
            if 'Phoenix-9Z' in source.get('text', '') or 'Elena Vasquez' in source.get('text', ''):
                found_phoenix = True
                doc_ids_to_delete.add(source.get('doc_id'))
                print(f"✅ Found Phoenix-9Z document: {source.get('doc_id')}")
        
        if not found_phoenix:
            print("❌ Test document not found in query results")
            return False
        
        # Step 3: Delete the document(s)
        print(f"\n🗑️ Step 3: Deleting documents: {list(doc_ids_to_delete)}")
        
        delete_data = list(doc_ids_to_delete)
        response = requests.delete(f"{API_BASE_URL}/manage/documents", json=delete_data)
        
        if response.status_code != 200:
            print(f"❌ Delete failed: {response.status_code}")
            print(response.text)
            return False
        
        delete_result = response.json()
        print(f"✅ Delete result: {delete_result}")
        
        # Wait a moment for deletion to take effect
        time.sleep(2)
        
        # Step 4: Query again to verify document is gone
        print("\n🔍 Step 4: Querying again to verify deletion...")
        
        response = requests.post(f"{API_BASE_URL}/query", json=query_data)
        if response.status_code != 200:
            print(f"❌ Post-deletion query failed: {response.status_code}")
            return False
        
        post_delete_result = response.json()
        print(f"📊 Post-deletion query result: Found {len(post_delete_result.get('sources', []))} sources")
        
        # Check if our test document is still in the results
        still_found_phoenix = False
        
        for source in post_delete_result.get('sources', []):
            if 'Phoenix-9Z' in source.get('text', '') or 'Elena Vasquez' in source.get('text', ''):
                still_found_phoenix = True
                print(f"❌ Phoenix-9Z document still found: {source.get('doc_id')}")
                print(f"   Text preview: {source.get('text', '')[:100]}...")
        
        if still_found_phoenix:
            print("❌ DELETION BUG STILL EXISTS: Document still appears in query results after deletion")
            return False
        else:
            print("✅ SUCCESS: Document properly deleted and no longer appears in query results")
            return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_additional_queries():
    """Test additional queries to make sure deletion is complete"""
    
    print("\n🔍 Additional Verification Queries")
    print("-" * 30)
    
    test_queries = [
        "What is the neural key length used in the Phoenix-9Z protocol?",
        "What is the emergency protocol activation code for Phoenix-9Z?",
        "Who is Dr. Elena Vasquez?",
        "What are Neural Flux Processors NFP-2024?"
    ]
    
    all_clean = True
    
    for query in test_queries:
        print(f"\n🔍 Testing query: {query}")
        
        query_data = {"query": query, "k": 5}
        response = requests.post(f"{API_BASE_URL}/query", json=query_data)
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get('sources', [])
            
            phoenix_found = False
            for source in sources:
                if any(keyword in source.get('text', '').lower() for keyword in 
                      ['phoenix-9z', 'elena vasquez', 'neural flux processor', 'gamma-twelve']):
                    phoenix_found = True
                    print(f"❌ Still found Phoenix-9Z content in: {source.get('doc_id')}")
                    all_clean = False
                    break
            
            if not phoenix_found:
                print("✅ No Phoenix-9Z content found")
        else:
            print(f"❌ Query failed: {response.status_code}")
    
    return all_clean

if __name__ == "__main__":
    print("🚀 Starting Document Deletion Fix Test")
    print("Make sure the RAG system is running on http://localhost:8000")
    print()
    
    # Test the main deletion functionality
    main_test_passed = test_document_deletion_fix()
    
    if main_test_passed:
        # Test additional queries to be thorough
        additional_tests_passed = test_additional_queries()
        
        if additional_tests_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Document deletion bug has been successfully fixed!")
        else:
            print("\n⚠️ Main test passed but additional queries still found traces")
            print("❌ Deletion may not be completely effective")
    else:
        print("\n❌ MAIN TEST FAILED")
        print("🐛 Document deletion bug still exists")
    
    print("\n" + "=" * 50)
    print("Test completed.") 