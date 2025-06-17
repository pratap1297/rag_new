#!/usr/bin/env python3
"""
Test Configuration
Simple test to verify configuration is being read correctly
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config():
    """Test configuration loading"""
    print("🧪 Testing Configuration")
    print("=" * 50)
    
    try:
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv(".env")
        
        # Test environment variables
        print("🔧 Environment Variables:")
        print(f"  RAG_EMBEDDING_PROVIDER: {os.getenv('RAG_EMBEDDING_PROVIDER')}")
        print(f"  RAG_EMBEDDING_MODEL: {os.getenv('RAG_EMBEDDING_MODEL')}")
        print(f"  RAG_LLM_PROVIDER: {os.getenv('RAG_LLM_PROVIDER')}")
        print(f"  RAG_LLM_MODEL: {os.getenv('RAG_LLM_MODEL')}")
        print(f"  AZURE_API_KEY: {'✅ Set' if os.getenv('AZURE_API_KEY') else '❌ Missing'}")
        print(f"  AZURE_EMBEDDINGS_ENDPOINT: {'✅ Set' if os.getenv('AZURE_EMBEDDINGS_ENDPOINT') else '❌ Missing'}")
        
        # Test constants function
        print("\n🔧 Testing Constants:")
        from core.constants import get_embedding_dimension
        provider = os.getenv('RAG_EMBEDDING_PROVIDER', 'azure')
        model = os.getenv('RAG_EMBEDDING_MODEL', 'Cohere-embed-v3-english')
        expected_dim = get_embedding_dimension(provider, model)
        print(f"  Expected dimension for {provider}/{model}: {expected_dim}")
        
        # Test config manager
        print("\n🔧 Testing ConfigManager:")
        from core.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        embedding_config = config_manager.get_config('embedding')
        llm_config = config_manager.get_config('llm')
        
        print(f"  Embedding Provider: {embedding_config.provider}")
        print(f"  Embedding Model: {embedding_config.model_name}")
        print(f"  Embedding Dimension (from config): {embedding_config.dimension}")
        print(f"  Embedding Dimension (expected): {expected_dim}")
        print(f"  Embedding API Key: {'✅ Set' if embedding_config.api_key else '❌ Missing'}")
        
        print(f"  LLM Provider: {llm_config.provider}")
        print(f"  LLM Model: {llm_config.model_name}")
        print(f"  LLM API Key: {'✅ Set' if llm_config.api_key else '❌ Missing'}")
        
        # Check if dimensions match
        if embedding_config.dimension != expected_dim:
            print(f"  ⚠️  WARNING: Dimension mismatch! Config: {embedding_config.dimension}, Expected: {expected_dim}")
        else:
            print(f"  ✅ Dimension match: {embedding_config.dimension}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config()
    if success:
        print("\n🎉 Configuration test passed!")
    else:
        print("\n💥 Configuration test failed!")
        sys.exit(1) 