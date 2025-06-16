#!/usr/bin/env python3
"""
Step-by-step RAG System Test
Test each component individually to isolate issues
"""
import sys
import os
import requests
import json
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_system_health():
    """Test if the system is running and healthy"""
    print("🔍 Step 1: Testing System Health")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System Status: {data.get('status', 'unknown')}")
            print(f"   📊 Services: {data.get('services', 0)}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot connect to server: {e}")
        print("   💡 Make sure to run: python main.py")
        return False

def test_configuration():
    """Test system configuration"""
    print("\n🔧 Step 2: Testing Configuration")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ Environment: {config.get('environment')}")
            print(f"   🧠 Embedding Model: {config.get('embedding_model')}")
            print(f"   🤖 LLM Provider: {config.get('llm_provider')}")
            print(f"   📏 Chunk Size: {config.get('chunk_size')}")
            return True
        else:
            print(f"   ❌ Config check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Config request failed: {e}")
        return False

def test_simple_ingestion():
    """Test simple text ingestion"""
    print("\n📄 Step 3: Testing Simple Text Ingestion")
    print("=" * 50)
    
    # Simple test data
    test_text = "Artificial intelligence is a branch of computer science that aims to create intelligent machines."
    test_metadata = {
        "title": "AI Basics",
        "source": "test",
        "category": "technology"
    }
    
    print(f"   📝 Test text: {test_text[:50]}...")
    print(f"   🏷️ Metadata: {test_metadata}")
    
    try:
        payload = {
            "text": test_text,
            "metadata": test_metadata
        }
        
        response = requests.post(
            "http://localhost:8000/ingest",
            json=payload,
            timeout=30
        )
        
        print(f"   📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Ingestion Status: {result.get('status')}")
            print(f"   📊 Chunks Created: {result.get('chunks_created')}")
            print(f"   🔢 Embeddings Generated: {result.get('embeddings_generated')}")
            return True
        else:
            print(f"   ❌ Ingestion failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   📄 Error: {error_detail}")
            except:
                print(f"   📄 Raw response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_query_processing():
    """Test query processing"""
    print("\n🔍 Step 4: Testing Query Processing")
    print("=" * 50)
    
    test_query = "What is artificial intelligence?"
    
    print(f"   ❓ Query: {test_query}")
    
    try:
        payload = {
            "query": test_query,
            "max_results": 3
        }
        
        response = requests.post(
            "http://localhost:8000/query",
            json=payload,
            timeout=30
        )
        
        print(f"   📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Query processed successfully")
            print(f"   🤖 Response length: {len(result.get('response', ''))}")
            print(f"   📚 Sources found: {len(result.get('sources', []))}")
            
            # Show first 100 chars of response
            response_text = result.get('response', '')
            if response_text:
                print(f"   💬 Response preview: {response_text[:100]}...")
            
            return True
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   📄 Error: {error_detail}")
            except:
                print(f"   📄 Raw response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_stats():
    """Test system statistics"""
    print("\n📊 Step 5: Testing System Statistics")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Stats retrieved successfully")
            print(f"   📁 Total Files: {stats.get('total_files', 0)}")
            print(f"   📄 Total Chunks: {stats.get('total_chunks', 0)}")
            print(f"   🔢 Total Vectors: {stats.get('total_vectors', 0)}")
            print(f"   📚 Collections: {stats.get('collections', 0)}")
            return True
        else:
            print(f"   ❌ Stats failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Stats request failed: {e}")
        return False

def main():
    """Run all tests step by step"""
    print("🧪 RAG System Step-by-Step Test")
    print("=" * 60)
    
    results = []
    
    # Test each step
    results.append(("System Health", test_system_health()))
    
    if results[-1][1]:  # Only continue if health check passed
        results.append(("Configuration", test_configuration()))
        results.append(("Simple Ingestion", test_simple_ingestion()))
        results.append(("Query Processing", test_query_processing()))
        results.append(("System Statistics", test_stats()))
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! RAG system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 