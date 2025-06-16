#!/usr/bin/env python3
"""
Quick RAG System Test
Fast test with timeouts to avoid hanging
"""
import requests
import json
import time

def test_server_connection():
    """Test if server is running"""
    print("🔍 Testing Server Connection...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server is running - Status: {data.get('status')}")
            return True
        else:
            print(f"   ❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server. Is it running?")
        print("   💡 Start server with: python main.py")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Server connection timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_simple_ingestion():
    """Test simple text ingestion"""
    print("\n📄 Testing Simple Ingestion...")
    try:
        payload = {
            "text": "The quick brown fox jumps over the lazy dog. This is a simple test sentence.",
            "metadata": {
                "title": "Test Document",
                "source": "quick_test"
            }
        }
        
        response = requests.post(
            "http://localhost:8000/ingest",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Ingestion successful - Chunks: {result.get('chunks_created')}")
            return True
        else:
            print(f"   ❌ Ingestion failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   📄 Error: {error}")
            except:
                print(f"   📄 Raw response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Ingestion request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_simple_query():
    """Test simple query"""
    print("\n🔍 Testing Simple Query...")
    try:
        payload = {
            "query": "What is a fox?",
            "max_results": 2
        }
        
        response = requests.post(
            "http://localhost:8000/query",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            sources = result.get("sources", [])
            
            print(f"   ✅ Query successful")
            print(f"   📝 Response length: {len(response_text)}")
            print(f"   📚 Sources found: {len(sources)}")
            
            if response_text:
                preview = response_text[:80] + "..." if len(response_text) > 80 else response_text
                print(f"   💬 Response: {preview}")
            
            return True
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   📄 Error: {error}")
            except:
                print(f"   📄 Raw response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Query request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_config():
    """Test configuration endpoint"""
    print("\n🔧 Testing Configuration...")
    try:
        response = requests.get("http://localhost:8000/config", timeout=5)
        
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ Config retrieved")
            print(f"   🌍 Environment: {config.get('environment')}")
            print(f"   🤖 LLM Provider: {config.get('llm_provider')}")
            print(f"   🧠 Embedding Model: {config.get('embedding_model')}")
            return True
        else:
            print(f"   ❌ Config failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Config request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run quick tests"""
    print("🧪 Quick RAG System Test")
    print("=" * 40)
    
    tests = [
        ("Server Connection", test_server_connection),
        ("Configuration", test_config),
        ("Simple Ingestion", test_simple_ingestion),
        ("Simple Query", test_simple_query)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        result = test_func()
        results.append((test_name, result))
        
        if not result:
            print(f"\n⚠️ {test_name} failed. Stopping tests.")
            break
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print(f"\n{'='*40}")
    print("📋 Quick Test Summary")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All quick tests passed!")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    main() 