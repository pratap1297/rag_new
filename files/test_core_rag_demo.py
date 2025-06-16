#!/usr/bin/env python3
"""
Core RAG Functionality Demonstration
Demonstrates the 3 core RAG capabilities with unique documents containing information
that LLMs would not have in their training data.

Test Cases:
1. Add Document → Query Unique Info → Verify Response
2. Update Document → Query Changed Info → Verify Updated Response  
3. Delete Document → Query Info → Verify Info No Longer Available
"""
import requests
import json
import time
import tempfile
import os
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def upload_document(content: str, title: str, description: str = "") -> dict:
    """Upload a document to the RAG system"""
    try:
        # Create temporary file
        temp_file = f"temp_{int(time.time())}.md"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Prepare metadata
        metadata = {
            "title": title,
            "description": description,
            "test_document": True,
            "created_at": datetime.now().isoformat()
        }
        
        # Upload file
        with open(temp_file, 'rb') as f:
            files = {'file': (f"{title}.md", f, 'text/markdown')}
            data = {'metadata': json.dumps(metadata)}
            
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                timeout=120
            )
        
        # Clean up temp file
        os.unlink(temp_file)
        
        if response.status_code == 200:
            result = response.json()
            return {
                'file_id': result.get('file_id'),
                'title': title,
                'chunks_created': result.get('chunks_created', 0),
                'upload_response': result
            }
        else:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        raise Exception(f"Document upload error: {str(e)}")

def query_system(query: str) -> dict:
    """Query the RAG system"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query, "max_results": 5},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'response': result.get('response'),
                'sources': result.get('sources', []),
                'context_used': result.get('context_used', 0)
            }
        else:
            raise Exception(f"Query failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        raise Exception(f"Query error: {str(e)}")

def delete_all_test_documents():
    """Delete all test documents"""
    try:
        response = requests.get(f"{API_BASE_URL}/manage/documents", params={"limit": 100})
        if response.status_code == 200:
            docs = response.json()
            test_doc_ids = []
            for doc in docs:
                if 'Zephyr' in doc.get('title', '') or 'test_document' in str(doc.get('metadata', {})):
                    test_doc_ids.append(doc.get('doc_id'))
            
            if test_doc_ids:
                delete_response = requests.delete(f"{API_BASE_URL}/manage/documents", json=test_doc_ids)
                if delete_response.status_code == 200:
                    print(f"   Deleted {len(test_doc_ids)} test documents")
                    return True
        return False
    except Exception as e:
        print(f"   Delete error: {e}")
        return False

def main():
    """Run the core RAG functionality demonstration"""
    print("🧪 CORE RAG FUNCTIONALITY DEMONSTRATION")
    print("="*80)
    print("Demonstrating RAG system's ability to:")
    print("1. Learn from unique documents")
    print("2. Update knowledge when documents change") 
    print("3. Forget information when documents are deleted")
    print("="*80)
    
    try:
        # Check if API is available
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code != 200:
            print("❌ RAG system API is not available. Please start the system first.")
            return
        
        print("✅ RAG system API is available")
        
        # Clean up any existing test documents
        print("\n🧹 Cleaning up any existing test documents...")
        delete_all_test_documents()
        time.sleep(2)
        
        # TEST CASE 1: Add Document and Query Unique Information
        print("\n" + "="*60)
        print("TEST CASE 1: Add Document and Query Unique Information")
        print("="*60)
        
        unique_content = """
# Project Quantum-Phoenix-9Z Documentation

## Overview
Project Quantum-Phoenix-9Z is a top-secret neural encryption protocol developed by Dr. Elena Vasquez 
at the Aurora Labs facility in 2024. This protocol uses a revolutionary 923-bit neural key 
exchange mechanism called "Synaptic Flux Encryption" (SFE).

## Key Specifications
- Protocol Version: Phoenix-9Z-Alpha-7.1.3
- Neural Key Length: 923 bits (proprietary length for maximum security)
- Encryption Algorithm: SFE-Neural-Hybrid-2024
- Maximum Throughput: 18.9 Gbps under optimal conditions
- Security Rating: OMEGA-CLASSIFIED (beyond top secret)

## Unique Features
1. Synaptic Flux Mechanism: Uses neural pattern displacement to generate keys
2. Vasquez Cipher: Named after its inventor, uses neural network sequences based on 
   brain wave patterns multiplied by the golden ratio to 52 decimal places
3. Authentication Code: QP-9Z-ELENA-2024-AURORA

## Implementation Details
The protocol requires specialized hardware called "Neural Flux Processors" (NFP-2024)
manufactured exclusively by Aurora Technologies. Each NFP unit costs $3.7 million and 
has a unique serial number starting with "NFP-QP9Z-".

## Security Clearance
Access to this protocol requires OMEGA-CLASSIFIED clearance level 12 or higher.
Only 8 individuals worldwide currently have this clearance level.

## Contact Information
For technical support, contact Dr. Elena Vasquez at e.vasquez@aurora-labs.secure
Emergency protocol activation code: PHOENIX-NINE-Z-GAMMA-TWELVE-TWELVE-FIVE
"""
        
        print("📤 Uploading unique document...")
        doc_info = upload_document(
            content=unique_content,
            title="Project Quantum-Phoenix-9Z",
            description="Top-secret neural encryption protocol documentation"
        )
        
        print(f"   Document uploaded successfully!")
        print(f"   File ID: {doc_info['file_id']}")
        print(f"   Chunks created: {doc_info['chunks_created']}")
        
        # Wait for indexing
        print("⏳ Waiting for document indexing...")
        time.sleep(3)
        
        # Test queries with unique information
        print("\n🔍 Testing queries with unique information...")
        
        query1 = "What is Project Quantum-Phoenix-9Z and who developed it?"
        result1 = query_system(query1)
        print(f"\nQuery: {query1}")
        print(f"Response: {result1['response'][:300]}...")
        print(f"Sources used: {result1['context_used']}")
        
        query2 = "What is the neural key length used in the Phoenix-9Z protocol?"
        result2 = query_system(query2)
        print(f"\nQuery: {query2}")
        print(f"Response: {result2['response'][:300]}...")
        print(f"Sources used: {result2['context_used']}")
        
        query3 = "What is the emergency protocol activation code for Phoenix-9Z?"
        result3 = query_system(query3)
        print(f"\nQuery: {query3}")
        print(f"Response: {result3['response'][:300]}...")
        print(f"Sources used: {result3['context_used']}")
        
        # Check if unique information was found
        test1_success = ("Phoenix-9Z" in result1['response'] and "Elena Vasquez" in result1['response'])
        test2_success = ("923 bits" in result2['response'] or "923-bit" in result2['response'])
        test3_success = ("PHOENIX-NINE-Z-GAMMA-TWELVE-TWELVE-FIVE" in result3['response'])
        
        print(f"\n✅ Test Case 1 Results:")
        print(f"   Basic info query: {'✅ PASS' if test1_success else '❌ FAIL'}")
        print(f"   Technical detail query: {'✅ PASS' if test2_success else '❌ FAIL'}")
        print(f"   Specific code query: {'✅ PASS' if test3_success else '❌ FAIL'}")
        
        # TEST CASE 2: Update Document and Verify Changes
        print("\n" + "="*60)
        print("TEST CASE 2: Update Document and Verify Changes")
        print("="*60)
        
        # Delete the original document first
        print("🗑️ Deleting original document...")
        delete_all_test_documents()
        time.sleep(2)
        
        updated_content = """
# Project Quantum-Phoenix-9Z Documentation (MAJOR UPDATE)

## Overview
Project Quantum-Phoenix-9Z is a top-secret neural encryption protocol developed by Dr. Elena Vasquez 
at the Aurora Labs facility in 2024. This protocol has been UPGRADED to use a new 
1536-bit neural key exchange mechanism called "Advanced Synaptic Flux Encryption" (ASFE).

## Key Specifications (UPDATED)
- Protocol Version: Phoenix-9Z-Beta-8.0.0 (MAJOR UPGRADE)
- Neural Key Length: 1536 bits (UPGRADED from 923 bits)
- Encryption Algorithm: ASFE-Neural-Hybrid-2024-PLUS (NEW VERSION)
- Maximum Throughput: 37.8 Gbps under optimal conditions (DOUBLED)
- Security Rating: OMEGA-CLASSIFIED-PLUS (NEW HIGHEST LEVEL)

## Unique Features (UPDATED)
1. Advanced Synaptic Flux Mechanism: Uses quantum neural pattern displacement with time-lock security
2. Enhanced Vasquez Cipher: Now uses neural sequences based on quantum brain patterns to 78 decimal places
3. NEW Authentication Code: QP-9Z-ELENA-2024-AURORA-ULTRA

## Implementation Details (UPDATED)
The protocol now requires NEW specialized hardware called "Advanced Neural Flux Processors" (ANFP-2024)
manufactured exclusively by Aurora Technologies. Each ANFP unit costs $7.4 million (PRICE DOUBLED) and 
has a unique serial number starting with "ANFP-QP9Z-" (NEW FORMAT).

## Security Clearance (UPDATED)
Access to this protocol now requires OMEGA-CLASSIFIED-PLUS clearance level 15 or higher (INCREASED).
Only 4 individuals worldwide currently have this clearance level (REDUCED from 8).

## Contact Information (UPDATED)
For technical support, contact Dr. Elena Vasquez at e.vasquez@aurora-labs.secure
NEW Emergency protocol activation code: PHOENIX-NINE-Z-DELTA-FIFTEEN-FIFTEEN-NINE (CHANGED)
"""
        
        print("📤 Uploading updated document...")
        updated_doc_info = upload_document(
            content=updated_content,
            title="Project Quantum-Phoenix-9Z Updated",
            description="UPDATED top-secret neural encryption protocol documentation"
        )
        
        print(f"   Updated document uploaded successfully!")
        print(f"   File ID: {updated_doc_info['file_id']}")
        print(f"   Chunks created: {updated_doc_info['chunks_created']}")
        
        # Wait for indexing
        print("⏳ Waiting for document indexing...")
        time.sleep(3)
        
        # Test queries to verify updated information
        print("\n🔍 Testing queries with updated information...")
        
        update_query1 = "What is the current neural key length in Phoenix-9Z protocol?"
        update_result1 = query_system(update_query1)
        print(f"\nQuery: {update_query1}")
        print(f"Response: {update_result1['response'][:300]}...")
        print(f"Sources used: {update_result1['context_used']}")
        
        update_query2 = "What is the current emergency protocol activation code for Phoenix-9Z?"
        update_result2 = query_system(update_query2)
        print(f"\nQuery: {update_query2}")
        print(f"Response: {update_result2['response'][:300]}...")
        print(f"Sources used: {update_result2['context_used']}")
        
        # Check if updated information is present and old information is absent
        new_key_found = ("1536 bits" in update_result1['response'] or "1536-bit" in update_result1['response'])
        old_key_found = ("923 bits" in update_result1['response'] or "923-bit" in update_result1['response'])
        new_code_found = ("PHOENIX-NINE-Z-DELTA-FIFTEEN-FIFTEEN-NINE" in update_result2['response'])
        old_code_found = ("PHOENIX-NINE-Z-GAMMA-TWELVE-TWELVE-FIVE" in update_result2['response'])
        
        print(f"\n✅ Test Case 2 Results:")
        print(f"   Updated key length (1536 bits): {'✅ FOUND' if new_key_found else '❌ NOT FOUND'}")
        print(f"   Old key length (923 bits): {'❌ STILL PRESENT' if old_key_found else '✅ REMOVED'}")
        print(f"   Updated activation code: {'✅ FOUND' if new_code_found else '❌ NOT FOUND'}")
        print(f"   Old activation code: {'❌ STILL PRESENT' if old_code_found else '✅ REMOVED'}")
        
        test2_success = new_key_found and not old_key_found and new_code_found and not old_code_found
        print(f"   Overall update test: {'✅ PASS' if test2_success else '❌ FAIL'}")
        
        # TEST CASE 3: Delete Document and Verify Information Removal
        print("\n" + "="*60)
        print("TEST CASE 3: Delete Document and Verify Information Removal")
        print("="*60)
        
        print("🗑️ Deleting all Phoenix-9Z documents...")
        delete_success = delete_all_test_documents()
        
        if delete_success:
            print("   Documents deleted successfully")
        else:
            print("   Warning: Document deletion may have failed")
        
        # Wait for deletion to process
        print("⏳ Waiting for deletion to process...")
        time.sleep(3)
        
        # Test queries to verify information is no longer available
        print("\n🔍 Testing queries after document deletion...")
        
        deletion_query1 = "What is Project Quantum-Phoenix-9Z and who developed it?"
        deletion_result1 = query_system(deletion_query1)
        print(f"\nQuery: {deletion_query1}")
        print(f"Response: {deletion_result1['response'][:300]}...")
        print(f"Sources used: {deletion_result1['context_used']}")
        
        deletion_query2 = "What is the emergency protocol activation code for Phoenix-9Z?"
        deletion_result2 = query_system(deletion_query2)
        print(f"\nQuery: {deletion_query2}")
        print(f"Response: {deletion_result2['response'][:300]}...")
        print(f"Sources used: {deletion_result2['context_used']}")
        
        # Check if specific information is absent
        phoenix_info_found = ("Phoenix-9Z" in deletion_result1['response'] or "Elena Vasquez" in deletion_result1['response'])
        code_info_found = ("PHOENIX-NINE-Z-DELTA-FIFTEEN-FIFTEEN-NINE" in deletion_result2['response'] or 
                          "PHOENIX-NINE-Z-GAMMA-TWELVE-TWELVE-FIVE" in deletion_result2['response'])
        
        print(f"\n✅ Test Case 3 Results:")
        print(f"   Phoenix-9Z specific info: {'❌ STILL PRESENT' if phoenix_info_found else '✅ REMOVED'}")
        print(f"   Activation codes: {'❌ STILL PRESENT' if code_info_found else '✅ REMOVED'}")
        
        test3_success = not phoenix_info_found and not code_info_found
        print(f"   Overall deletion test: {'✅ PASS' if test3_success else '❌ FAIL'}")
        
        # FINAL SUMMARY
        print("\n" + "="*80)
        print("FINAL DEMONSTRATION RESULTS")
        print("="*80)
        
        total_tests = 3
        passed_tests = sum([test1_success, test2_success, test3_success])
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nTest Case Results:")
        print(f"✅ Test Case 1 - Learn from unique documents: {'✅ PASS' if test1_success else '❌ FAIL'}")
        print(f"✅ Test Case 2 - Update knowledge when documents change: {'✅ PASS' if test2_success else '❌ FAIL'}")
        print(f"✅ Test Case 3 - Forget information when documents deleted: {'✅ PASS' if test3_success else '❌ FAIL'}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL CORE RAG FUNCTIONALITY TESTS PASSED!")
            print("✅ The RAG system successfully demonstrates:")
            print("   • Learning from unique documents with information LLMs don't know")
            print("   • Updating knowledge when documents are changed")
            print("   • Forgetting information when documents are deleted")
            print("\n🌟 The RAG system is working perfectly for core functionality!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} TEST(S) FAILED")
            print("❌ The RAG system has some issues with core functionality")
        
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to RAG system API")
        print("   Please ensure the system is running on http://localhost:8000")
        print("   Run: python main.py")
    except Exception as e:
        print(f"❌ Test suite error: {e}")

if __name__ == "__main__":
    main() 