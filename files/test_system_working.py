#!/usr/bin/env python3
"""
Test script to verify the RAG system is working end-to-end
"""
import sys
from pathlib import Path
import requests
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_api_health():
    """Test if the API is responding"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Health Check: PASSED")
            return True
        else:
            print(f"❌ API Health Check: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Health Check: FAILED ({e})")
        return False

def test_core_components():
    """Test core RAG components directly"""
    try:
        print("🔧 Testing core RAG components...")
        
        # Test embedder
        from src.ingestion.embedder import Embedder
        import os
        
        embedder = Embedder(
            provider="cohere",
            model_name="embed-english-v3.0",
            api_key=os.getenv("COHERE_API_KEY")
        )
        
        test_text = "This is a test document for RAG system."
        embeddings = embedder.embed_texts([test_text])
        print(f"✅ Embedder: Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
        
        # Test FAISS store
        from src.storage.faiss_store import FAISSStore
        faiss_store = FAISSStore("data/vectors/test_index.bin", dimension=1024)
        
        # Add test embedding
        faiss_store.add_vectors(embeddings, ["test_doc_1"])
        print("✅ FAISS Store: Added test vectors")
        
        # Search test
        results = faiss_store.search(embeddings[0], k=1)
        print(f"✅ FAISS Store: Search returned {len(results)} results")
        
        # Test LLM client
        from src.retrieval.llm_client import LLMClient
        llm_client = LLMClient(
            provider="groq",
            model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        response = llm_client.generate("What is artificial intelligence?", max_tokens=50)
        print(f"✅ LLM Client: Generated response ({len(response)} characters)")
        
        print("✅ All core components working!")
        return True
        
    except Exception as e:
        print(f"❌ Core components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints"""
    try:
        print("🔧 Testing API endpoints...")
        
        # Test query endpoint
        query_data = {
            "query": "What is artificial intelligence?",
            "max_results": 3
        }
        
        response = requests.post("http://localhost:8000/query", json=query_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query API: Response received with {len(result.get('sources', []))} sources")
        else:
            print(f"❌ Query API: Failed (Status: {response.status_code})")
            return False
        
        # Test ingest endpoint (if available)
        try:
            ingest_data = {
                "text": "This is a test document about artificial intelligence and machine learning.",
                "metadata": {"title": "Test Document", "source": "test"}
            }
            
            response = requests.post("http://localhost:8000/ingest", json=ingest_data, timeout=10)
            if response.status_code == 200:
                print("✅ Ingest API: Document ingested successfully")
            else:
                print(f"⚠️ Ingest API: Status {response.status_code} (may not be implemented)")
        except:
            print("⚠️ Ingest API: Not available or failed")
        
        print("✅ API endpoints test completed!")
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 RAG System Comprehensive Test")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: API Health
    if test_api_health():
        tests_passed += 1
    
    # Test 2: Core Components
    if test_core_components():
        tests_passed += 1
    
    # Test 3: API Endpoints
    if test_api_endpoints():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"🧪 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! RAG system is working correctly!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 