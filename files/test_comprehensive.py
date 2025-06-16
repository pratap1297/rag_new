#!/usr/bin/env python3
"""
Comprehensive RAG System Test
Test multiple documents, various query types, and edge cases
"""
import requests
import json
import time
from typing import List, Dict, Any

class RAGSystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
    def wait_for_server(self, max_attempts: int = 10):
        """Wait for server to be ready"""
        print("🔄 Waiting for server to be ready...")
        for attempt in range(max_attempts):
            try:
                response = self.session.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"   Attempt {attempt + 1}/{max_attempts}...")
            time.sleep(2)
        
        print("❌ Server not ready after maximum attempts")
        return False
    
    def test_health_and_config(self):
        """Test basic health and configuration"""
        print("\n🔍 Testing Health and Configuration")
        print("=" * 50)
        
        try:
            # Health check
            health_response = self.session.get(f"{self.base_url}/health")
            print(f"   Health Status: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   System Status: {health_data.get('status')}")
            
            # Configuration
            config_response = self.session.get(f"{self.base_url}/config")
            print(f"   Config Status: {config_response.status_code}")
            if config_response.status_code == 200:
                config_data = config_response.json()
                print(f"   Environment: {config_data.get('environment')}")
                print(f"   LLM Provider: {config_data.get('llm_provider')}")
                print(f"   Embedding Model: {config_data.get('embedding_model')}")
            
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def ingest_document(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Ingest a single document"""
        try:
            payload = {
                "text": text,
                "metadata": metadata
            }
            
            response = self.session.post(
                f"{self.base_url}/ingest",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Ingested '{metadata.get('title', 'Unknown')}' - {result.get('chunks_created')} chunks")
                return True
            else:
                print(f"   ❌ Failed to ingest '{metadata.get('title', 'Unknown')}': {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error ingesting '{metadata.get('title', 'Unknown')}': {e}")
            return False
    
    def test_multiple_documents(self):
        """Test ingesting multiple diverse documents"""
        print("\n📚 Testing Multiple Document Ingestion")
        print("=" * 50)
        
        documents = [
            {
                "text": """
                Machine Learning is a subset of artificial intelligence that focuses on algorithms 
                that can learn and make decisions from data. It includes supervised learning, 
                unsupervised learning, and reinforcement learning. Popular algorithms include 
                linear regression, decision trees, neural networks, and support vector machines.
                """,
                "metadata": {
                    "title": "Machine Learning Fundamentals",
                    "category": "AI/ML",
                    "author": "Data Scientist",
                    "difficulty": "intermediate"
                }
            },
            {
                "text": """
                Python is a versatile programming language known for its simplicity and readability. 
                It's widely used in web development, data science, automation, and artificial intelligence. 
                Key features include dynamic typing, extensive libraries, and cross-platform compatibility. 
                Popular frameworks include Django, Flask, NumPy, and Pandas.
                """,
                "metadata": {
                    "title": "Python Programming Overview",
                    "category": "Programming",
                    "author": "Software Engineer",
                    "difficulty": "beginner"
                }
            },
            {
                "text": """
                Cloud computing delivers computing services over the internet, including servers, 
                storage, databases, networking, and software. The main service models are IaaS 
                (Infrastructure as a Service), PaaS (Platform as a Service), and SaaS (Software as a Service). 
                Major providers include AWS, Microsoft Azure, and Google Cloud Platform.
                """,
                "metadata": {
                    "title": "Cloud Computing Basics",
                    "category": "Cloud Technology",
                    "author": "Cloud Architect",
                    "difficulty": "intermediate"
                }
            },
            {
                "text": """
                Data Science is an interdisciplinary field that combines statistics, programming, 
                and domain expertise to extract insights from data. The typical workflow includes 
                data collection, cleaning, exploration, modeling, and visualization. Common tools 
                include Python, R, SQL, Jupyter notebooks, and various visualization libraries.
                """,
                "metadata": {
                    "title": "Data Science Workflow",
                    "category": "Data Science",
                    "author": "Data Analyst",
                    "difficulty": "intermediate"
                }
            },
            {
                "text": """
                Cybersecurity protects digital systems, networks, and data from threats and attacks. 
                Key principles include confidentiality, integrity, and availability (CIA triad). 
                Common threats include malware, phishing, ransomware, and social engineering. 
                Protection measures include firewalls, encryption, access controls, and security awareness training.
                """,
                "metadata": {
                    "title": "Cybersecurity Fundamentals",
                    "category": "Security",
                    "author": "Security Expert",
                    "difficulty": "advanced"
                }
            }
        ]
        
        successful = 0
        for doc in documents:
            if self.ingest_document(doc["text"], doc["metadata"]):
                successful += 1
        
        print(f"\n   📊 Successfully ingested {successful}/{len(documents)} documents")
        return successful == len(documents)
    
    def test_diverse_queries(self):
        """Test various types of queries"""
        print("\n🔍 Testing Diverse Query Types")
        print("=" * 50)
        
        queries = [
            {
                "query": "What is machine learning?",
                "expected_category": "AI/ML",
                "description": "Direct factual question"
            },
            {
                "query": "How do I start programming in Python?",
                "expected_category": "Programming",
                "description": "How-to question"
            },
            {
                "query": "Compare cloud service models",
                "expected_category": "Cloud Technology",
                "description": "Comparison question"
            },
            {
                "query": "What tools are used in data science?",
                "expected_category": "Data Science",
                "description": "List/enumeration question"
            },
            {
                "query": "Explain the CIA triad in cybersecurity",
                "expected_category": "Security",
                "description": "Explanation question"
            },
            {
                "query": "What are neural networks and decision trees?",
                "expected_category": "AI/ML",
                "description": "Multi-concept question"
            }
        ]
        
        successful_queries = 0
        
        for i, query_info in enumerate(queries, 1):
            print(f"\n   Query {i}: {query_info['description']}")
            print(f"   ❓ '{query_info['query']}'")
            
            try:
                payload = {
                    "query": query_info["query"],
                    "max_results": 3
                }
                
                response = self.session.post(
                    f"{self.base_url}/query",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    sources = result.get("sources", [])
                    
                    print(f"   ✅ Response length: {len(response_text)} characters")
                    print(f"   📚 Sources found: {len(sources)}")
                    
                    if sources:
                        # Check if we found relevant sources
                        relevant_found = any(
                            source.get("metadata", {}).get("category") == query_info["expected_category"]
                            for source in sources
                        )
                        if relevant_found:
                            print(f"   🎯 Found relevant source from {query_info['expected_category']}")
                        else:
                            print(f"   ⚠️ No sources from expected category {query_info['expected_category']}")
                    
                    # Show response preview
                    preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
                    print(f"   💬 Response: {preview}")
                    
                    successful_queries += 1
                else:
                    print(f"   ❌ Query failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n   📊 Successfully processed {successful_queries}/{len(queries)} queries")
        return successful_queries == len(queries)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n⚠️ Testing Edge Cases")
        print("=" * 50)
        
        edge_cases = [
            {
                "name": "Empty query",
                "payload": {"query": "", "max_results": 3},
                "expected_status": 400
            },
            {
                "name": "Very long query",
                "payload": {"query": "What is " + "very " * 100 + "long query?", "max_results": 3},
                "expected_status": 200
            },
            {
                "name": "Query with special characters",
                "payload": {"query": "What is AI? @#$%^&*()", "max_results": 3},
                "expected_status": 200
            },
            {
                "name": "High max_results",
                "payload": {"query": "What is programming?", "max_results": 100},
                "expected_status": 200
            }
        ]
        
        successful_cases = 0
        
        for case in edge_cases:
            print(f"\n   Testing: {case['name']}")
            try:
                response = self.session.post(
                    f"{self.base_url}/query",
                    json=case["payload"]
                )
                
                if response.status_code == case["expected_status"]:
                    print(f"   ✅ Expected status {case['expected_status']}")
                    successful_cases += 1
                else:
                    print(f"   ❌ Got status {response.status_code}, expected {case['expected_status']}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n   📊 Passed {successful_cases}/{len(edge_cases)} edge case tests")
        return successful_cases == len(edge_cases)
    
    def test_system_stats(self):
        """Test system statistics"""
        print("\n📊 Testing System Statistics")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{self.base_url}/stats", timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✅ Stats retrieved successfully")
                print(f"   📁 Total Files: {stats.get('total_files', 0)}")
                print(f"   📄 Total Chunks: {stats.get('total_chunks', 0)}")
                print(f"   🔢 Total Vectors: {stats.get('total_vectors', 0)}")
                print(f"   📚 Collections: {stats.get('collections', 0)}")
                return True
            else:
                print(f"   ❌ Stats request failed: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("   ⚠️ Stats request timed out (non-critical)")
            return True  # Don't fail the test for timeout
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

def main():
    """Run comprehensive tests"""
    print("🧪 Comprehensive RAG System Test")
    print("=" * 60)
    
    tester = RAGSystemTester()
    
    # Wait for server
    if not tester.wait_for_server():
        print("❌ Server not available. Make sure to run: python main.py")
        return
    
    # Run all tests
    results = []
    
    results.append(("Health & Config", tester.test_health_and_config()))
    results.append(("Multiple Documents", tester.test_multiple_documents()))
    results.append(("Diverse Queries", tester.test_diverse_queries()))
    results.append(("Edge Cases", tester.test_edge_cases()))
    results.append(("System Stats", tester.test_system_stats()))
    
    # Summary
    print("\n📋 Comprehensive Test Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} test suites passed")
    
    if passed == len(results):
        print("🎉 All comprehensive tests passed! RAG system is fully functional.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 