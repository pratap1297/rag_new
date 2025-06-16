#!/usr/bin/env python3
"""
Debug RAG System Startup
Identify where the system hangs during initialization
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config_manager():
    """Test configuration manager"""
    print("🔧 Testing configuration manager...")
    try:
        from src.core.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print(f"✅ Config loaded: {config.environment} environment")
        print(f"   LLM Provider: {config.llm.provider}")
        print(f"   API Key set: {'Yes' if config.llm.api_key else 'No'}")
        return config_manager
    except Exception as e:
        print(f"❌ Config manager failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_json_store():
    """Test JSON store"""
    print("\n💾 Testing JSON store...")
    try:
        from src.core.json_store import JSONStore
        store = JSONStore("data/test")
        store.write("test", {"test": "data"})
        data = store.read("test")
        print(f"✅ JSON store working: {data}")
        return True
    except Exception as e:
        print(f"❌ JSON store failed: {e}")
        return False

def test_embedder():
    """Test embedder initialization"""
    print("\n🔤 Testing embedder...")
    try:
        from src.ingestion.embedder import Embedder
        
        # Test Cohere embedder first
        print("   Testing Cohere embedder...")
        try:
            embedder = Embedder(
                provider="cohere",
                model_name="embed-english-v3.0",
                batch_size=96
            )
            print("✅ Cohere embedder initialized successfully")
            
            # Test embedding
            test_texts = ["Hello world", "This is a test"]
            embeddings = embedder.embed_texts(test_texts)
            print(f"✅ Cohere embedding test: {len(embeddings)} embeddings generated")
            print(f"   Cohere embedding dimension: {embedder.get_dimension()}")
            return True
            
        except Exception as cohere_error:
            print(f"⚠️  Cohere embedder failed: {cohere_error}")
            print("   Falling back to sentence-transformers...")
            
            # Fallback to sentence-transformers
            embedder = Embedder(
                provider="sentence-transformers",
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                batch_size=32
            )
            print("✅ SentenceTransformers embedder initialized successfully")
            
            # Test embedding
            test_texts = ["Hello world", "This is a test"]
            embeddings = embedder.embed_texts(test_texts)
            print(f"✅ SentenceTransformers embedding test: {len(embeddings)} embeddings generated")
            print(f"   SentenceTransformers embedding dimension: {embedder.get_dimension()}")
            return True
        
    except Exception as e:
        print(f"❌ Embedder failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_faiss_store():
    """Test FAISS store"""
    print("\n🔍 Testing FAISS store...")
    try:
        from src.storage.faiss_store import FAISSStore
        
        faiss_store = FAISSStore(
            index_path="data/vectors/test_index.faiss",
            dimension=1024  # Cohere embedding dimension
        )
        print("✅ FAISS store initialized")
        
        # Test adding vectors
        import numpy as np
        test_vectors = np.random.random((2, 1024)).astype('float32').tolist()
        test_metadata = [{"text": "test1"}, {"text": "test2"}]
        
        ids = faiss_store.add_vectors(test_vectors, test_metadata)
        print(f"✅ FAISS test: Added {len(ids)} vectors")
        
        # Test search
        search_results = faiss_store.search(test_vectors[0], k=1)
        print(f"✅ FAISS search: Found {len(search_results)} results")
        return True
        
    except Exception as e:
        print(f"❌ FAISS store failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_client():
    """Test LLM client"""
    print("\n🤖 Testing LLM client...")
    try:
        from src.retrieval.llm_client import LLMClient
        
        llm_client = LLMClient(
            provider="groq",
            model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=0.1,
            max_tokens=100
        )
        print("✅ LLM client initialized")
        
        # Test connection
        if llm_client.test_connection():
            print("✅ LLM connection test: PASSED")
        else:
            print("⚠️  LLM connection test: FAILED (but client initialized)")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM client failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debug tests"""
    print("🐛 RAG SYSTEM DEBUG")
    print("="*40)
    
    # Test each component individually
    tests = [
        ("Configuration Manager", test_config_manager),
        ("JSON Store", test_json_store),
        ("Embedder", test_embedder),
        ("FAISS Store", test_faiss_store),
        ("LLM Client", test_llm_client)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                break  # Stop at first failure
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            break
    
    print(f"\n🏁 Debug completed!")
    print("If any component failed, that's likely where the system is hanging.")

if __name__ == "__main__":
    main() 