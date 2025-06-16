#!/usr/bin/env python3
"""
RAG System API Test Script
Test the RAG system API endpoints
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_config():
    """Test config endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=5)
        if response.status_code == 200:
            print("✅ Config endpoint working")
            config_data = response.json()
            print(f"   Environment: {config_data.get('environment')}")
            print(f"   LLM Provider: {config_data.get('llm_provider')}")
            print(f"   Embedding Model: {config_data.get('embedding_model')}")
            return True
        else:
            print(f"❌ Config endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Config endpoint failed: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Stats endpoint working")
            stats_data = response.json()
            print(f"   Total files: {stats_data.get('total_files', 0)}")
            print(f"   Total vectors: {stats_data.get('total_vectors', 0)}")
            return True
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Stats endpoint failed: {e}")
        return False

def test_upload():
    """Test file upload"""
    try:
        # Create a test file
        test_file = Path("test_upload.txt")
        test_content = """
        This is a test document for the RAG system.
        It contains information about artificial intelligence and machine learning.
        RAG systems combine retrieval and generation to provide accurate responses.
        Vector databases store embeddings for efficient similarity search.
        """
        test_file.write_text(test_content.strip())
        
        # Upload the file
        with open(test_file, 'rb') as f:
            files = {'file': ('test_upload.txt', f, 'text/plain')}
            metadata = json.dumps({
                "category": "test",
                "description": "Test document for RAG system"
            })
            data = {'metadata': metadata}
            
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data, timeout=30)
        
        # Cleanup
        test_file.unlink()
        
        if response.status_code == 200:
            print("✅ File upload successful")
            upload_data = response.json()
            print(f"   Status: {upload_data.get('status')}")
            print(f"   Chunks created: {upload_data.get('chunks_created', 0)}")
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ File upload failed: {e}")
        return False
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return False

def test_query():
    """Test query endpoint"""
    try:
        query_data = {
            "query": "What is artificial intelligence?",
            "top_k": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/query", 
            json=query_data, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Query successful")
            query_result = response.json()
            print(f"   Query: {query_result.get('query')}")
            print(f"   Response: {query_result.get('response', '')[:100]}...")
            print(f"   Sources found: {query_result.get('total_sources', 0)}")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Query failed: {e}")
        return False

def wait_for_server(max_wait=60):
    """Wait for server to be ready"""
    print("🔄 Waiting for server to start...")
    for i in range(max_wait):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        
        print(f"   Waiting... ({i+1}/{max_wait})")
        time.sleep(1)
    
    print("❌ Server did not start within timeout")
    return False

def main():
    """Run all API tests"""
    print("🧪 RAG System API Tests")
    print("=" * 40)
    
    # Wait for server
    if not wait_for_server():
        return
    
    print("\n📋 Running API tests...")
    
    tests = [
        ("Health Check", test_health),
        ("Config Endpoint", test_config),
        ("Stats Endpoint", test_stats),
        ("File Upload", test_upload),
        ("Query Processing", test_query)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ⚠️  {test_name} test failed")
        except Exception as e:
            print(f"   ❌ {test_name} test error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API tests passed! RAG system is working correctly.")
        print("\n🚀 You can now:")
        print("   • Upload documents via POST /upload")
        print("   • Query the system via POST /query")
        print("   • Check system health via GET /health")
        print("   • View API docs at http://localhost:8000/docs")
    else:
        print("⚠️  Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    main() 