#!/usr/bin/env python3
"""
API Timeout Test Script
Test the RAG API with proper timeout handling
"""
import requests
import time
import json
import sys

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test basic health check"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Health check timed out")
        return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_detailed_health():
    """Test detailed health check"""
    print("🔍 Testing detailed health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health/detailed", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Detailed health check passed - Status: {data.get('status')}")
            components = data.get('components', {})
            for comp, status in components.items():
                print(f"      - {comp}: {status.get('status', 'unknown')}")
            return True
        else:
            print(f"   ❌ Detailed health check failed: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Detailed health check timed out")
        return False
    except Exception as e:
        print(f"   ❌ Detailed health check error: {e}")
        return False

def test_simple_query():
    """Test a simple query"""
    print("🔍 Testing simple query...")
    try:
        query_data = {
            "query": "Hello, how are you?",
            "max_results": 2
        }
        response = requests.post(
            f"{API_BASE_URL}/query", 
            json=query_data, 
            timeout=45
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Query successful - Response length: {len(data.get('response', ''))}")
            print(f"      Sources found: {len(data.get('sources', []))}")
            return True
        else:
            print(f"   ❌ Query failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Query timed out")
        return False
    except Exception as e:
        print(f"   ❌ Query error: {e}")
        return False

def test_text_ingestion():
    """Test text ingestion"""
    print("🔍 Testing text ingestion...")
    try:
        ingest_data = {
            "text": "This is a test document for ingestion. It contains some sample text to test the RAG system.",
            "metadata": {
                "title": "Test Document",
                "source": "API Test",
                "type": "test"
            }
        }
        response = requests.post(
            f"{API_BASE_URL}/ingest", 
            json=ingest_data, 
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Text ingestion successful - Chunks: {data.get('chunks_created', 0)}")
            return True
        else:
            print(f"   ❌ Text ingestion failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Text ingestion timed out")
        return False
    except Exception as e:
        print(f"   ❌ Text ingestion error: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    print("🔍 Testing stats endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Stats retrieved successfully")
            if 'faiss_store' in data:
                faiss_stats = data['faiss_store']
                print(f"      Vector count: {faiss_stats.get('vector_count', 0)}")
            return True
        else:
            print(f"   ❌ Stats failed: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Stats request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Stats error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API Timeout Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Detailed Health", test_detailed_health),
        ("Simple Query", test_simple_query),
        ("Text Ingestion", test_text_ingestion),
        ("Stats", test_stats)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly with timeouts.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the API server and configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 