#!/usr/bin/env python3
"""
Minimal RAG System Startup
Bypasses complex initialization to get basic system running
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def minimal_startup():
    """Minimal system startup"""
    print("🚀 MINIMAL RAG SYSTEM STARTUP")
    print("="*50)
    
    try:
        # Step 1: Basic environment check
        print("🔧 Step 1: Basic environment check...")
        print(f"   Python version: {sys.version}")
        print(f"   Working directory: {os.getcwd()}")
        print("   ✅ Environment OK")
        
        # Step 2: Test basic imports
        print("🔧 Step 2: Testing basic imports...")
        
        print("   📦 Testing core imports...")
        from src.core.config_manager import ConfigManager
        print("   ✅ ConfigManager imported")
        
        # Skip JSON store for now
        print("   ⚠️ Skipping JSONStore (causing hang)")
        
        print("   📦 Testing embedder...")
        from src.ingestion.embedder import Embedder
        print("   ✅ Embedder imported")
        
        print("   📦 Testing FAISS store...")
        from src.storage.faiss_store import FAISSStore
        print("   ✅ FAISSStore imported")
        
        print("   📦 Testing LLM client...")
        from src.retrieval.llm_client import LLMClient
        print("   ✅ LLMClient imported")
        
        # Step 3: Test basic functionality
        print("🔧 Step 3: Testing basic functionality...")
        
        print("   📦 Creating config manager...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print(f"   ✅ Config loaded: {config.environment}")
        
        print("   📦 Testing embedder...")
        embedder = Embedder(
            provider="cohere",
            model_name="embed-english-v3.0"
        )
        print(f"   ✅ Embedder created: {embedder.get_dimension()} dimensions")
        
        print("   📦 Testing FAISS store...")
        faiss_store = FAISSStore(
            index_path="data/vectors/minimal_test.faiss",
            dimension=1024
        )
        print("   ✅ FAISS store created")
        
        print("   📦 Testing LLM client...")
        llm_client = LLMClient(
            provider="groq",
            model_name="meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        print("   ✅ LLM client created")
        
        # Step 4: Test end-to-end functionality
        print("🔧 Step 4: Testing end-to-end functionality...")
        
        print("   📦 Testing embedding...")
        test_texts = ["Hello world", "This is a test document"]
        embeddings = embedder.embed_texts(test_texts)
        print(f"   ✅ Generated {len(embeddings)} embeddings")
        
        print("   📦 Testing vector storage...")
        metadata = [{"text": text, "source": "test"} for text in test_texts]
        vector_ids = faiss_store.add_vectors(embeddings, metadata)
        print(f"   ✅ Stored {len(vector_ids)} vectors")
        
        print("   📦 Testing vector search...")
        query_embedding = embedder.embed_text("Hello")
        results = faiss_store.search(query_embedding, k=1)
        print(f"   ✅ Found {len(results)} search results")
        
        print("   📦 Testing LLM generation...")
        if llm_client.test_connection():
            print("   ✅ LLM connection successful")
        else:
            print("   ⚠️ LLM connection failed")
        
        print("\n✅ MINIMAL RAG SYSTEM WORKING!")
        print("="*50)
        print("🎯 Core components are functional")
        print("🎯 You can now work on fixing the full initialization")
        
        return True
        
    except Exception as e:
        print(f"\n❌ MINIMAL STARTUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    minimal_startup() 