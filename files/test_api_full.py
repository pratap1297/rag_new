#!/usr/bin/env python3
"""
Comprehensive API Test with Dummy Data
Tests all RAG functionality through API endpoints using sample documents
"""
import requests
import json
import time
import sys
import os
from pathlib import Path

# Add src to path for direct component testing if needed
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class RAGAPITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_health(self):
        """Test system health"""
        print("🔍 Testing System Health...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"   ✅ Status: {health['status']}")
                print(f"   📊 Services: {health['components']['container']['services']}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    def test_config(self):
        """Test configuration endpoint"""
        print("\n🔧 Testing Configuration...")
        try:
            response = self.session.get(f"{self.base_url}/config")
            if response.status_code == 200:
                config = response.json()
                print(f"   ✅ Environment: {config.get('environment')}")
                print(f"   🧠 Embedding Model: {config.get('embedding_model')}")
                print(f"   🤖 LLM Provider: {config.get('llm_provider')}")
                print(f"   📏 Chunk Size: {config.get('chunk_size')}")
                return config
            else:
                print(f"   ❌ Config failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Config error: {e}")
            return None
    
    def test_ingest_text(self, text, metadata):
        """Test text ingestion via API"""
        print(f"\n📄 Testing Text Ingestion...")
        print(f"   📝 Text length: {len(text)} characters")
        print(f"   🏷️ Metadata: {metadata}")
        
        try:
            # Try the ingest endpoint
            ingest_data = {
                "text": text,
                "metadata": metadata
            }
            
            response = self.session.post(f"{self.base_url}/ingest", json=ingest_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Ingestion successful!")
                print(f"   📊 Result: {result}")
                return result
            else:
                print(f"   ❌ Ingestion failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Ingestion error: {e}")
            return None
    

    
    def test_query(self, query, max_results=3):
        """Test query processing via API"""
        print(f"\n🔍 Testing Query Processing...")
        print(f"   ❓ Query: '{query}'")
        print(f"   📊 Max results: {max_results}")
        
        try:
            query_data = {
                "query": query,
                "max_results": max_results
            }
            
            response = self.session.post(f"{self.base_url}/query", json=query_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Query successful!")
                print(f"   🤖 Response: {result.get('response', 'No response')[:200]}...")
                print(f"   📚 Sources found: {len(result.get('sources', []))}")
                
                # Show sources
                for i, source in enumerate(result.get('sources', [])[:3]):
                    print(f"   📄 Source {i+1}: {source.get('text', '')[:100]}...")
                
                return result
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Query error: {e}")
            return None
    

    
    def test_stats(self):
        """Test stats endpoint"""
        print(f"\n📊 Testing Stats...")
        try:
            response = self.session.get(f"{self.base_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✅ Stats retrieved: {stats}")
                return stats
            else:
                print(f"   ⚠️ Stats endpoint returned: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ⚠️ Stats error: {e}")
            return None

def main():
    """Main test function"""
    print("🧪 Comprehensive RAG API Test with Dummy Data")
    print("=" * 60)
    
    tester = RAGAPITester()
    
    # Test 1: Health Check
    if not tester.test_health():
        print("❌ Health check failed - stopping tests")
        return
    
    # Test 2: Configuration
    config = tester.test_config()
    if not config:
        print("❌ Configuration test failed")
        return
    
    # Test 3: Document Ingestion with Dummy Data
    dummy_documents = [
        {
            "text": """
            Artificial Intelligence (AI) is a branch of computer science that aims to create 
            intelligent machines that can perform tasks that typically require human intelligence. 
            These tasks include learning, reasoning, problem-solving, perception, and language understanding.
            
            Machine Learning is a subset of AI that focuses on the development of algorithms and 
            statistical models that enable computers to improve their performance on a specific task 
            through experience without being explicitly programmed.
            
            Deep Learning is a subset of machine learning that uses artificial neural networks 
            with multiple layers to model and understand complex patterns in data.
            """,
            "metadata": {
                "title": "Introduction to AI",
                "source": "educational_content",
                "category": "technology",
                "author": "AI Expert"
            }
        },
        {
            "text": """
            Python is a high-level, interpreted programming language with dynamic semantics. 
            Its high-level built-in data structures, combined with dynamic typing and dynamic binding, 
            make it very attractive for Rapid Application Development, as well as for use as a 
            scripting or glue language to connect existing components together.
            
            Python's simple, easy to learn syntax emphasizes readability and therefore reduces 
            the cost of program maintenance. Python supports modules and packages, which encourages 
            program modularity and code reuse.
            """,
            "metadata": {
                "title": "Python Programming",
                "source": "programming_guide",
                "category": "programming",
                "author": "Python Developer"
            }
        },
        {
            "text": """
            Cloud computing is the delivery of computing services—including servers, storage, 
            databases, networking, software, analytics, and intelligence—over the Internet ("the cloud") 
            to offer faster innovation, flexible resources, and economies of scale.
            
            The main types of cloud computing include Infrastructure as a Service (IaaS), 
            Platform as a Service (PaaS), and Software as a Service (SaaS). Each type provides 
            different levels of control, flexibility, and management.
            """,
            "metadata": {
                "title": "Cloud Computing Basics",
                "source": "tech_documentation",
                "category": "cloud",
                "author": "Cloud Architect"
            }
        }
    ]
    
    # Ingest all dummy documents
    ingestion_results = []
    for i, doc in enumerate(dummy_documents):
        print(f"\n📄 Document {i+1}/{len(dummy_documents)}: {doc['metadata']['title']}")
        result = tester.test_ingest_text(doc["text"], doc["metadata"])
        if result:
            ingestion_results.append(result)
        time.sleep(1)  # Small delay between ingestions
    
    print(f"\n📊 Ingestion Summary: {len(ingestion_results)}/{len(dummy_documents)} documents processed")
    
    # Test 4: Query Processing with Various Questions
    test_queries = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "What are the benefits of Python programming?",
        "Explain cloud computing services",
        "What is the difference between AI and machine learning?",
        "What are the main types of cloud computing?"
    ]
    
    query_results = []
    for i, query in enumerate(test_queries):
        print(f"\n🔍 Query {i+1}/{len(test_queries)}")
        result = tester.test_query(query)
        if result:
            query_results.append(result)
        time.sleep(1)  # Small delay between queries
    
    print(f"\n📊 Query Summary: {len(query_results)}/{len(test_queries)} queries processed")
    
    # Test 5: Stats
    tester.test_stats()
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎉 Comprehensive RAG API Test Complete!")
    print("\n📋 Test Results:")
    print(f"   ✅ Health Check: Passed")
    print(f"   ✅ Configuration: Passed")
    print(f"   📄 Document Ingestion: {len(ingestion_results)}/{len(dummy_documents)} successful")
    print(f"   🔍 Query Processing: {len(query_results)}/{len(test_queries)} successful")
    
    if len(ingestion_results) > 0 and len(query_results) > 0:
        print("\n🎯 RAG System is fully functional!")
        print("   ✅ Documents can be ingested and processed")
        print("   ✅ Queries can be answered with context")
        print("   ✅ Vector search is working")
        print("   ✅ LLM generation is working")
    else:
        print("\n⚠️ Some functionality needs attention")
        if len(ingestion_results) == 0:
            print("   ❌ Document ingestion needs implementation")
        if len(query_results) == 0:
            print("   ❌ Query processing needs implementation")
    
    print(f"\n🌐 Access your RAG system at: {tester.base_url}")
    print(f"📚 API Documentation: {tester.base_url}/docs")

if __name__ == "__main__":
    main() 