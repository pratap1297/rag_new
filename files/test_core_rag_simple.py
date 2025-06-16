#!/usr/bin/env python3
"""
Simplified Core RAG Functionality Test Suite
Tests the fundamental RAG capabilities with unique documents containing information
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

class RAGTestSuite:
    def __init__(self):
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            print(f"   Details: {details}")
    
    def upload_document(self, content: str, title: str, description: str = "") -> dict:
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
                doc_info = {
                    'file_id': result.get('file_id'),
                    'title': title,
                    'chunks_created': result.get('chunks_created', 0),
                    'upload_response': result
                }
                return doc_info
            else:
                raise Exception(f"Upload failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Document upload error: {str(e)}")
    
    def query_system(self, query: str, expected_keywords: list = None) -> dict:
        """Query the RAG system and analyze response"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/query",
                json={"query": query, "max_results": 5},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Analyze response for expected keywords
                response_text = result.get('response', '').lower()
                sources = result.get('sources', [])
                
                keyword_found = False
                if expected_keywords:
                    keyword_found = any(keyword.lower() in response_text for keyword in expected_keywords)
                
                return {
                    'response': result.get('response'),
                    'sources': sources,
                    'context_used': result.get('context_used', 0),
                    'keyword_found': keyword_found,
                    'raw_result': result
                }
            else:
                raise Exception(f"Query failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Query error: {str(e)}")
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the system"""
        try:
            response = requests.delete(
                f"{API_BASE_URL}/manage/documents",
                json=[doc_id],
                timeout=60
            )
            
            if response.status_code == 200:
                return True
            else:
                raise Exception(f"Delete failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Delete error: {str(e)}")
    
    def get_document_id_by_title(self, title: str) -> str:
        """Get document ID by title"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/manage/documents",
                params={"limit": 100, "title_filter": title},
                timeout=30
            )
            
            if response.status_code == 200:
                documents = response.json()
                for doc in documents:
                    if doc.get('title') == title:
                        return doc.get('doc_id')
                raise Exception(f"Document with title '{title}' not found")
            else:
                raise Exception(f"Failed to get documents: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Error getting document ID: {str(e)}")

    def test_case_1_add_and_query(self):
        """Test Case 1: Add Document with Unique Information and Query"""
        print("\n" + "="*60)
        print("TEST CASE 1: Add Document and Query Unique Information")
        print("="*60)
        
        # Create document with unique, specific information
        unique_content = """
# Project Zephyr-7X Protocol Documentation

## Overview
Project Zephyr-7X is a classified quantum encryption protocol developed by Dr. Marina Volkov 
at the Nexus Research Institute in 2024. This protocol uses a unique 847-bit quantum key 
exchange mechanism called "Temporal Flux Encryption" (TFE).

## Key Specifications
- Protocol Version: Zephyr-7X-Rev3.2.1
- Quantum Key Length: 847 bits (non-standard length for security)
- Encryption Algorithm: TFE-AES-Hybrid-2024
- Maximum Throughput: 12.7 Gbps under optimal conditions
- Security Rating: COSMIC-ULTRA (highest classification)

## Unique Features
1. Temporal Flux Mechanism: Uses quantum temporal displacement to generate keys
2. Volkov Cipher: Named after its inventor, uses prime number sequences based on 
   the Fibonacci sequence multiplied by pi to 47 decimal places
3. Authentication Code: ZX-7-MARINA-2024-NEXUS

## Implementation Details
The protocol requires specialized hardware called "Quantum Flux Generators" (QFG-2024)
manufactured exclusively by Nexus Industries. Each QFG unit costs $2.3 million and 
has a unique serial number starting with "QFG-ZX7-".

## Security Clearance
Access to this protocol requires COSMIC-ULTRA clearance level 9 or higher.
Only 12 individuals worldwide currently have this clearance level.

## Contact Information
For technical support, contact Dr. Marina Volkov at m.volkov@nexus-research.institute
Emergency protocol activation code: ZEPHYR-SEVEN-X-ALPHA-NINE-NINE-SEVEN
"""
        
        try:
            # Upload the unique document
            print("📤 Uploading unique document...")
            doc_info = self.upload_document(
                content=unique_content,
                title="Project Zephyr-7X Protocol",
                description="Classified quantum encryption protocol documentation"
            )
            
            print(f"   Document uploaded successfully!")
            print(f"   File ID: {doc_info['file_id']}")
            print(f"   Chunks created: {doc_info['chunks_created']}")
            
            # Wait for indexing
            print("⏳ Waiting for document indexing...")
            time.sleep(3)
            
            # Test queries with unique information
            test_queries = [
                {
                    "query": "What is Project Zephyr-7X and who developed it?",
                    "expected_keywords": ["Zephyr-7X", "Marina Volkov", "quantum encryption", "Nexus Research Institute"],
                    "description": "Basic information about the project"
                },
                {
                    "query": "What is the quantum key length used in the Zephyr-7X protocol?",
                    "expected_keywords": ["847 bits", "847-bit", "quantum key"],
                    "description": "Specific technical detail"
                },
                {
                    "query": "What is the emergency protocol activation code for Zephyr-7X?",
                    "expected_keywords": ["ZEPHYR-SEVEN-X-ALPHA-NINE-NINE-SEVEN", "emergency protocol"],
                    "description": "Highly specific code information"
                }
            ]
            
            all_queries_passed = True
            for i, test_query in enumerate(test_queries, 1):
                print(f"\n🔍 Query {i}: {test_query['description']}")
                print(f"   Question: {test_query['query']}")
                
                result = self.query_system(test_query['query'], test_query['expected_keywords'])
                
                print(f"   Response: {result['response'][:200]}...")
                print(f"   Sources used: {result['context_used']}")
                print(f"   Keywords found: {result['keyword_found']}")
                
                if result['keyword_found'] and result['context_used'] > 0:
                    self.log_result(f"Query {i} - {test_query['description']}", True, "Unique information correctly retrieved")
                else:
                    self.log_result(f"Query {i} - {test_query['description']}", False, f"Expected keywords not found or no context used")
                    all_queries_passed = False
            
            # Overall test result
            if all_queries_passed:
                self.log_result("Test Case 1 - Add and Query", True, "All unique information queries successful")
            else:
                self.log_result("Test Case 1 - Add and Query", False, "Some queries failed to retrieve unique information")
                
            return doc_info
            
        except Exception as e:
            self.log_result("Test Case 1 - Add and Query", False, str(e))
            return None

    def test_case_2_update_and_verify(self, original_doc_info):
        """Test Case 2: Update Document and Verify Changed Information"""
        print("\n" + "="*60)
        print("TEST CASE 2: Update Document and Verify Changes")
        print("="*60)
        
        # Create updated document with changed information
        updated_content = """
# Project Zephyr-7X Protocol Documentation (UPDATED)

## Overview
Project Zephyr-7X is a classified quantum encryption protocol developed by Dr. Marina Volkov 
at the Nexus Research Institute in 2024. This protocol has been UPGRADED to use a new 
1024-bit quantum key exchange mechanism called "Advanced Temporal Flux Encryption" (ATFE).

## Key Specifications (UPDATED)
- Protocol Version: Zephyr-7X-Rev4.0.0 (MAJOR UPDATE)
- Quantum Key Length: 1024 bits (UPGRADED from 847 bits)
- Encryption Algorithm: ATFE-AES-Hybrid-2024-PLUS (NEW VERSION)
- Maximum Throughput: 25.4 Gbps under optimal conditions (DOUBLED)
- Security Rating: COSMIC-ULTRA-PLUS (NEW HIGHEST CLASSIFICATION)

## Unique Features (UPDATED)
1. Advanced Temporal Flux Mechanism: Uses quantum temporal displacement with time-lock security
2. Enhanced Volkov Cipher: Now uses prime sequences based on the Golden Ratio to 63 decimal places
3. NEW Authentication Code: ZX-7-MARINA-2024-NEXUS-ULTRA

## Implementation Details (UPDATED)
The protocol now requires NEW specialized hardware called "Advanced Quantum Flux Generators" (AQFG-2024)
manufactured exclusively by Nexus Industries. Each AQFG unit costs $4.7 million (PRICE INCREASED) and 
has a unique serial number starting with "AQFG-ZX7-" (NEW FORMAT).

## Security Clearance (UPDATED)
Access to this protocol now requires COSMIC-ULTRA-PLUS clearance level 10 or higher (INCREASED).
Only 6 individuals worldwide currently have this clearance level (REDUCED from 12).

## Contact Information (UPDATED)
For technical support, contact Dr. Marina Volkov at m.volkov@nexus-research.institute
NEW Emergency protocol activation code: ZEPHYR-SEVEN-X-BETA-TEN-TEN-EIGHT (CHANGED)
"""
        
        try:
            # First, delete the original document
            print("🗑️ Deleting original document...")
            original_doc_id = self.get_document_id_by_title("Project Zephyr-7X Protocol")
            delete_success = self.delete_document(original_doc_id)
            
            if delete_success:
                print("   Original document deleted successfully")
            else:
                raise Exception("Failed to delete original document")
            
            # Wait for deletion to process
            time.sleep(2)
            
            # Upload the updated document
            print("📤 Uploading updated document...")
            updated_doc_info = self.upload_document(
                content=updated_content,
                title="Project Zephyr-7X Protocol Updated",
                description="UPDATED classified quantum encryption protocol documentation"
            )
            
            print(f"   Updated document uploaded successfully!")
            print(f"   File ID: {updated_doc_info['file_id']}")
            print(f"   Chunks created: {updated_doc_info['chunks_created']}")
            
            # Wait for indexing
            print("⏳ Waiting for document indexing...")
            time.sleep(3)
            
            # Test queries to verify updated information
            update_test_queries = [
                {
                    "query": "What is the current quantum key length in Zephyr-7X protocol?",
                    "expected_keywords": ["1024 bits", "1024-bit"],
                    "old_keywords": ["847 bits", "847-bit"],
                    "description": "Updated key length"
                },
                {
                    "query": "What is the current emergency protocol activation code?",
                    "expected_keywords": ["ZEPHYR-SEVEN-X-BETA-TEN-TEN-EIGHT"],
                    "old_keywords": ["ZEPHYR-SEVEN-X-ALPHA-NINE-NINE-SEVEN"],
                    "description": "Updated activation code"
                }
            ]
            
            all_updates_verified = True
            for i, test_query in enumerate(update_test_queries, 1):
                print(f"\n🔍 Update Query {i}: {test_query['description']}")
                print(f"   Question: {test_query['query']}")
                
                result = self.query_system(test_query['query'], test_query['expected_keywords'])
                
                print(f"   Response: {result['response'][:200]}...")
                print(f"   Sources used: {result['context_used']}")
                
                # Check if new information is present and old information is absent
                response_text = result['response'].lower()
                new_info_found = any(keyword.lower() in response_text for keyword in test_query['expected_keywords'])
                old_info_found = any(keyword.lower() in response_text for keyword in test_query.get('old_keywords', []))
                
                print(f"   New info found: {new_info_found}")
                print(f"   Old info found: {old_info_found}")
                
                if new_info_found and not old_info_found and result['context_used'] > 0:
                    self.log_result(f"Update Query {i} - {test_query['description']}", True, "Updated information correctly retrieved")
                else:
                    self.log_result(f"Update Query {i} - {test_query['description']}", False, f"Update verification failed - new: {new_info_found}, old: {old_info_found}")
                    all_updates_verified = False
            
            # Overall test result
            if all_updates_verified:
                self.log_result("Test Case 2 - Update and Verify", True, "All document updates verified successfully")
            else:
                self.log_result("Test Case 2 - Update and Verify", False, "Some updates were not properly reflected")
                
            return updated_doc_info
            
        except Exception as e:
            self.log_result("Test Case 2 - Update and Verify", False, str(e))
            return None

    def test_case_3_delete_and_verify_removal(self, doc_info):
        """Test Case 3: Delete Document and Verify Information Removal"""
        print("\n" + "="*60)
        print("TEST CASE 3: Delete Document and Verify Information Removal")
        print("="*60)
        
        try:
            # Delete the document
            print("🗑️ Deleting document...")
            doc_id = self.get_document_id_by_title("Project Zephyr-7X Protocol Updated")
            delete_success = self.delete_document(doc_id)
            
            if delete_success:
                print("   Document deleted successfully")
            else:
                raise Exception("Failed to delete document")
            
            # Wait for deletion to process
            print("⏳ Waiting for deletion to process...")
            time.sleep(3)
            
            # Test queries to verify information is no longer available
            deletion_test_queries = [
                {
                    "query": "What is Project Zephyr-7X and who developed it?",
                    "should_not_contain": ["Marina Volkov", "Nexus Research Institute", "Zephyr-7X"],
                    "description": "Basic project information should be unavailable"
                },
                {
                    "query": "What is the emergency protocol activation code for Zephyr-7X?",
                    "should_not_contain": ["ZEPHYR-SEVEN-X-BETA-TEN-TEN-EIGHT", "ZEPHYR-SEVEN-X-ALPHA-NINE-NINE-SEVEN"],
                    "description": "Specific codes should be unavailable"
                }
            ]
            
            all_deletions_verified = True
            for i, test_query in enumerate(deletion_test_queries, 1):
                print(f"\n🔍 Deletion Query {i}: {test_query['description']}")
                print(f"   Question: {test_query['query']}")
                
                result = self.query_system(test_query['query'])
                
                print(f"   Response: {result['response'][:200]}...")
                print(f"   Sources used: {result['context_used']}")
                
                # Check if specific information is absent
                response_text = result['response'].lower()
                specific_info_found = any(keyword.lower() in response_text for keyword in test_query['should_not_contain'])
                
                print(f"   Specific info found: {specific_info_found}")
                print(f"   Context sources: {len(result['sources'])}")
                
                # Success if no specific information found
                if not specific_info_found:
                    self.log_result(f"Deletion Query {i} - {test_query['description']}", True, "Specific information successfully removed")
                else:
                    self.log_result(f"Deletion Query {i} - {test_query['description']}", False, "Specific information still found after deletion")
                    all_deletions_verified = False
            
            # Overall test result
            if all_deletions_verified:
                self.log_result("Test Case 3 - Delete and Verify Removal", True, "All specific information successfully removed")
            else:
                self.log_result("Test Case 3 - Delete and Verify Removal", False, "Some specific information still accessible after deletion")
                
        except Exception as e:
            self.log_result("Test Case 3 - Delete and Verify Removal", False, str(e))

    def run_all_tests(self):
        """Run all three core test cases"""
        print("🧪 CORE RAG FUNCTIONALITY TEST SUITE")
        print("="*80)
        print("Testing RAG system's ability to:")
        print("1. Learn from unique documents")
        print("2. Update knowledge when documents change") 
        print("3. Forget information when documents are deleted")
        print("="*80)
        
        # Test Case 1: Add and Query
        doc_info = self.test_case_1_add_and_query()
        
        if doc_info:
            # Test Case 2: Update and Verify
            updated_doc_info = self.test_case_2_update_and_verify(doc_info)
            
            if updated_doc_info:
                # Test Case 3: Delete and Verify Removal
                self.test_case_3_delete_and_verify_removal(updated_doc_info)
        
        # Print final results
        self.print_final_results()
    
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("FINAL TEST RESULTS")
        print("="*80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test']}")
            if not result['success']:
                print(f"   └─ {result['details']}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ RAG system successfully demonstrates:")
            print("   • Learning from unique documents")
            print("   • Updating knowledge when documents change")
            print("   • Forgetting information when documents are deleted")
        else:
            print(f"\n⚠️ {total - passed} TESTS FAILED")
            print("❌ RAG system has issues with core functionality")
        
        print("="*80)

def main():
    """Run the core RAG functionality tests"""
    test_suite = RAGTestSuite()
    
    try:
        # Check if API is available
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code != 200:
            print("❌ RAG system API is not available. Please start the system first.")
            print("   Run: python main.py")
            return
        
        print("✅ RAG system API is available")
        
        # Run all tests
        test_suite.run_all_tests()
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to RAG system API")
        print("   Please ensure the system is running on http://localhost:8000")
        print("   Run: python main.py")
    except Exception as e:
        print(f"❌ Test suite error: {e}")

if __name__ == "__main__":
    main() 