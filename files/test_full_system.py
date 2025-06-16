#!/usr/bin/env python3
"""
Comprehensive RAG System Test
Upload test documents and run various queries to verify system functionality
"""
import requests
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

class RAGSystemTester:
    def __init__(self):
        self.uploaded_files = []
        self.test_results = []
    
    def wait_for_server(self, max_wait=60):
        """Wait for server to be ready"""
        print("🔄 Waiting for RAG system to be ready...")
        for i in range(max_wait):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ Server is ready! Status: {health_data.get('status', 'unknown')}")
                    return True
            except:
                pass
            
            if i % 10 == 0:  # Print every 10 seconds
                print(f"   Waiting... ({i+1}/{max_wait})")
            time.sleep(1)
        
        print("❌ Server did not start within timeout")
        return False
    
    def upload_test_documents(self):
        """Upload test documents to the system"""
        print("\n📁 Uploading test documents...")
        
        test_docs = [
            {
                "file": "test_documents/company_policy.md",
                "metadata": {
                    "category": "policy",
                    "department": "HR",
                    "document_type": "company_manual",
                    "version": "2024.1"
                }
            },
            {
                "file": "test_documents/technical_guide.txt",
                "metadata": {
                    "category": "technical",
                    "department": "Engineering",
                    "document_type": "architecture_guide",
                    "complexity": "advanced"
                }
            }
        ]
        
        for doc_info in test_docs:
            file_path = Path(doc_info["file"])
            if not file_path.exists():
                print(f"❌ Test document not found: {file_path}")
                continue
            
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f, 'text/plain')}
                    metadata = json.dumps(doc_info["metadata"])
                    data = {'metadata': metadata}
                    
                    print(f"   Uploading {file_path.name}...")
                    response = requests.post(
                        f"{BASE_URL}/upload", 
                        files=files, 
                        data=data, 
                        timeout=60
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ {file_path.name}: {result.get('chunks_created', 0)} chunks created")
                    self.uploaded_files.append({
                        "file": file_path.name,
                        "result": result
                    })
                else:
                    print(f"   ❌ {file_path.name}: Upload failed ({response.status_code})")
                    print(f"      Error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ {file_path.name}: Upload error - {e}")
        
        print(f"\n📊 Upload Summary: {len(self.uploaded_files)} files uploaded successfully")
    
    def test_queries(self):
        """Test various types of queries"""
        print("\n🔍 Testing query functionality...")
        
        test_queries = [
            {
                "name": "Remote Work Policy",
                "query": "What is the company's remote work policy?",
                "expected_topics": ["remote work", "eligibility", "guidelines"],
                "filters": {"category": "policy"}
            },
            {
                "name": "Vacation Days",
                "query": "How many vacation days do employees get?",
                "expected_topics": ["vacation", "annual leave", "days"],
                "filters": {"category": "policy"}
            },
            {
                "name": "Training Budget",
                "query": "What is the training budget for senior employees?",
                "expected_topics": ["training", "budget", "senior"],
                "filters": {"department": "HR"}
            },
            {
                "name": "Technical Architecture",
                "query": "What embedding model does the RAG system use?",
                "expected_topics": ["embedding", "model", "sentence-transformers"],
                "filters": {"category": "technical"}
            },
            {
                "name": "Vector Database",
                "query": "How does the vector database work in the RAG system?",
                "expected_topics": ["FAISS", "vector", "similarity"],
                "filters": {"document_type": "architecture_guide"}
            },
            {
                "name": "Performance Optimization",
                "query": "How can I optimize the performance of the RAG system?",
                "expected_topics": ["optimization", "performance", "batch"],
                "filters": {"category": "technical"}
            },
            {
                "name": "Security Measures",
                "query": "What security measures are implemented?",
                "expected_topics": ["security", "encryption", "authentication"],
                "filters": None
            },
            {
                "name": "General Query",
                "query": "What benefits does the company offer?",
                "expected_topics": ["benefits", "health", "insurance"],
                "filters": None
            }
        ]
        
        for i, test_query in enumerate(test_queries, 1):
            print(f"\n   🔍 Test {i}: {test_query['name']}")
            print(f"      Query: {test_query['query']}")
            
            try:
                query_data = {
                    "query": test_query["query"],
                    "top_k": 5
                }
                
                if test_query["filters"]:
                    query_data["filters"] = test_query["filters"]
                
                response = requests.post(
                    f"{BASE_URL}/query",
                    json=query_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Analyze response
                    response_text = result.get('response', '').lower()
                    sources_count = result.get('total_sources', 0)
                    
                    # Check if expected topics are mentioned
                    topics_found = []
                    for topic in test_query['expected_topics']:
                        if topic.lower() in response_text:
                            topics_found.append(topic)
                    
                    success = len(topics_found) > 0 and sources_count > 0
                    
                    if success:
                        print(f"      ✅ Success: Found {sources_count} sources")
                        print(f"         Topics found: {', '.join(topics_found)}")
                        print(f"         Response: {result['response'][:100]}...")
                    else:
                        print(f"      ⚠️  Partial: {sources_count} sources, topics: {topics_found}")
                        print(f"         Response: {result['response'][:100]}...")
                    
                    self.test_results.append({
                        "test": test_query['name'],
                        "success": success,
                        "sources": sources_count,
                        "topics_found": topics_found,
                        "response_length": len(result['response'])
                    })
                    
                else:
                    print(f"      ❌ Query failed: {response.status_code}")
                    print(f"         Error: {response.text}")
                    self.test_results.append({
                        "test": test_query['name'],
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"      ❌ Query error: {e}")
                self.test_results.append({
                    "test": test_query['name'],
                    "success": False,
                    "error": str(e)
                })
            
            # Small delay between queries
            time.sleep(1)
    
    def test_system_endpoints(self):
        """Test system endpoints"""
        print("\n🔧 Testing system endpoints...")
        
        endpoints = [
            ("Health Check", "GET", "/health"),
            ("Configuration", "GET", "/config"),
            ("Statistics", "GET", "/stats")
        ]
        
        for name, method, endpoint in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {name}: Working")
                    
                    # Print relevant info
                    if endpoint == "/health":
                        print(f"      Status: {data.get('status', 'unknown')}")
                    elif endpoint == "/config":
                        print(f"      Environment: {data.get('environment', 'unknown')}")
                        print(f"      LLM Provider: {data.get('llm_provider', 'unknown')}")
                    elif endpoint == "/stats":
                        print(f"      Total files: {data.get('total_files', 0)}")
                        print(f"      Total vectors: {data.get('total_vectors', 0)}")
                else:
                    print(f"   ❌ {name}: Failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {name}: Error - {e}")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 RAG SYSTEM TEST REPORT")
        print("="*60)
        
        # Upload summary
        print(f"\n📁 Document Upload:")
        print(f"   Files uploaded: {len(self.uploaded_files)}")
        total_chunks = sum(f['result'].get('chunks_created', 0) for f in self.uploaded_files)
        print(f"   Total chunks created: {total_chunks}")
        
        # Query test summary
        print(f"\n🔍 Query Tests:")
        successful_queries = sum(1 for r in self.test_results if r.get('success', False))
        total_queries = len(self.test_results)
        print(f"   Successful queries: {successful_queries}/{total_queries}")
        print(f"   Success rate: {(successful_queries/total_queries*100):.1f}%")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result.get('success', False) else "❌"
            print(f"   {status} {result['test']}")
            if result.get('success', False):
                print(f"      Sources: {result.get('sources', 0)}, "
                      f"Topics: {len(result.get('topics_found', []))}, "
                      f"Response length: {result.get('response_length', 0)}")
            elif 'error' in result:
                print(f"      Error: {result['error']}")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if successful_queries == total_queries and len(self.uploaded_files) > 0:
            print("   🎉 EXCELLENT: All tests passed! RAG system is working perfectly.")
        elif successful_queries >= total_queries * 0.8:
            print("   ✅ GOOD: Most tests passed. System is working well.")
        elif successful_queries >= total_queries * 0.5:
            print("   ⚠️  FAIR: Some tests passed. System needs attention.")
        else:
            print("   ❌ POOR: Many tests failed. System needs debugging.")
        
        print(f"\n🚀 Next Steps:")
        print("   1. Review any failed tests above")
        print("   2. Check system logs for detailed error information")
        print("   3. Upload your own documents and test with real queries")
        print("   4. Access the API documentation at http://localhost:8000/docs")

def main():
    """Main test function"""
    print("🧪 RAG SYSTEM COMPREHENSIVE TEST")
    print("="*50)
    
    tester = RAGSystemTester()
    
    # Wait for server
    if not tester.wait_for_server():
        print("❌ Cannot connect to RAG system. Make sure it's running with: python start.py")
        return
    
    # Run tests
    tester.test_system_endpoints()
    tester.upload_test_documents()
    
    # Wait a bit for indexing
    print("\n⏳ Waiting for document indexing to complete...")
    time.sleep(5)
    
    tester.test_queries()
    tester.generate_report()

if __name__ == "__main__":
    main() 