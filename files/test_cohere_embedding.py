#!/usr/bin/env python3
"""
Test Cohere Embedding Integration
"""
import os
import requests
import json

def test_cohere_config():
    """Test switching to Cohere embeddings"""
    print("🧪 Testing Cohere Embedding Configuration")
    print("=" * 50)
    
    # Check if COHERE_API_KEY is set
    cohere_key = os.getenv('COHERE_API_KEY')
    if not cohere_key:
        print("❌ COHERE_API_KEY environment variable not set")
        print("💡 Please set your Cohere API key:")
        print("   export COHERE_API_KEY=your_api_key_here")
        return False
    else:
        print(f"✅ COHERE_API_KEY is set (length: {len(cohere_key)})")
    
    return True

def test_cohere_direct():
    """Test Cohere embedding directly"""
    print("\n🔍 Testing Cohere Embedding Directly...")
    
    try:
        from src.ingestion.embedder import CohereEmbedder
        
        # Test with a simple text
        embedder = CohereEmbedder(
            model_name="embed-english-v3.0",
            api_key=os.getenv('COHERE_API_KEY')
        )
        
        test_texts = ["Hello world", "This is a test"]
        embeddings = embedder.embed_texts(test_texts)
        
        print(f"   ✅ Generated embeddings for {len(test_texts)} texts")
        print(f"   📏 Embedding dimension: {embedder.get_dimension()}")
        print(f"   📊 First embedding length: {len(embeddings[0])}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def update_server_config():
    """Update server to use Cohere embeddings"""
    print("\n🔧 Updating Server Configuration...")
    
    try:
        # Update config via API
        config_update = {
            "embedding": {
                "provider": "cohere",
                "model_name": "embed-english-v3.0",
                "dimension": 1024,
                "batch_size": 96
            }
        }
        
        response = requests.post(
            "http://localhost:8000/config/update",
            json=config_update,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Configuration updated successfully")
            return True
        else:
            print(f"   ❌ Failed to update config: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error updating config: {e}")
        return False

def test_server_with_cohere():
    """Test server functionality with Cohere"""
    print("\n🧪 Testing Server with Cohere Embeddings...")
    
    try:
        # Check current config
        response = requests.get("http://localhost:8000/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"   🔧 Current embedding provider: {config.get('embedding_provider', 'unknown')}")
            print(f"   🔧 Current embedding model: {config.get('embedding_model', 'unknown')}")
        
        # Test ingestion with Cohere
        payload = {
            "text": "Cohere is a leading AI company that provides large language models and embedding models for enterprise applications. Their embedding models are particularly good at understanding semantic meaning.",
            "metadata": {
                "title": "Cohere Test Document",
                "source": "cohere_test",
                "type": "embedding_test"
            }
        }
        
        response = requests.post(
            "http://localhost:8000/ingest",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Ingestion successful - Chunks: {result.get('chunks_created')}")
            
            # Test query
            query_payload = {
                "query": "What is Cohere known for?",
                "max_results": 3
            }
            
            response = requests.post(
                "http://localhost:8000/query",
                json=query_payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Query successful")
                print(f"   📝 Response: {result.get('response', '')[:100]}...")
                print(f"   📚 Sources found: {len(result.get('sources', []))}")
                return True
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                return False
        else:
            print(f"   ❌ Ingestion failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run Cohere embedding tests"""
    print("🚀 Cohere Embedding Integration Test")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_cohere_config),
        ("Direct Cohere Test", test_cohere_direct),
        ("Server with Cohere", test_server_with_cohere)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        result = test_func()
        results.append((test_name, result))
        
        if not result and test_name == "Environment Setup":
            print(f"\n⚠️ {test_name} failed. Cannot continue without API key.")
            break
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 Cohere Test Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

if __name__ == "__main__":
    main() 