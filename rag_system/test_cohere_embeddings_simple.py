#!/usr/bin/env python3
"""
Simple Cohere Embeddings Test
- Loads .env at the top (standard pattern)
- Uses os.getenv for all keys/endpoints (as in main codebase)
- Works for Cohere (including Azure Foundry) and Azure
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# --- Standard .env loading pattern (as in main codebase) ---
try:
    from dotenv import load_dotenv
    load_dotenv(".env")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment")

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_cohere_embeddings():
    """Test Cohere embeddings using Azure endpoint (as configured in .env)"""
    print("🔍 Testing Cohere Embeddings (via Azure endpoint)")
    print("=" * 50)
    try:
        from azure.ai.inference import EmbeddingsClient
        from azure.core.credentials import AzureKeyCredential
        api_key = os.getenv('AZURE_API_KEY')
        endpoint = os.getenv('AZURE_EMBEDDINGS_ENDPOINT')
        if not api_key or not endpoint:
            print("❌ AZURE_API_KEY or AZURE_EMBEDDINGS_ENDPOINT not set in .env or environment")
            return False, None, 0
        print(f"✅ Using Azure endpoint for Cohere embeddings")
        print(f"   Endpoint: {endpoint}")
        client = EmbeddingsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        model_name = "Cohere-embed-v3-english"  # Cohere model via Azure
        test_texts = [
            "Hello world, this is a test.",
            "Cohere provides excellent embedding models.",
            "Azure AI services are powerful.",
            "Embeddings capture semantic meaning.",
            "Machine learning is transforming technology."
        ]
        # Single embedding
        print(f"\n📝 Testing single embedding...")
        start_time = time.time()
        response = client.embed(
            input=["test"],
            model=model_name,
            input_type="document"
        )
        single_time = time.time() - start_time
        dimension = len(response.data[0].embedding)
        print(f"✅ Single embedding successful")
        print(f"📏 Dimension: {dimension}")
        print(f"⏱️  Time: {single_time:.3f}s")
        # Batch embeddings
        print(f"\n📝 Testing batch embeddings...")
        start_time = time.time()
        response = client.embed(
            input=test_texts,
            model=model_name,
            input_type="document"
        )
        batch_time = time.time() - start_time
        embeddings = [item.embedding for item in response.data]
        print(f"✅ Batch embeddings successful")
        print(f"📊 Generated {len(embeddings)} embeddings")
        print(f"⏱️  Total time: {batch_time:.3f}s")
        print(f"📈 Average time per embedding: {batch_time/len(test_texts):.3f}s")
        return True, embeddings, dimension
    except ImportError as e:
        print(f"❌ Azure AI Inference package not installed: {e}")
        return False, None, 0
    except Exception as e:
        print(f"❌ Azure API error: {e}")
        return False, None, 0

def test_azure_embeddings():
    """Test Azure embeddings using .env and os.getenv (standard pattern)"""
    print("\n🔍 Testing Azure Embeddings (.env pattern)")
    print("=" * 50)
    try:
        from azure.ai.inference import EmbeddingsClient
        from azure.core.credentials import AzureKeyCredential
        api_key = os.getenv('AZURE_API_KEY')
        endpoint = os.getenv('AZURE_EMBEDDINGS_ENDPOINT')
        if not api_key or not endpoint:
            print("⚠️  AZURE_API_KEY or AZURE_EMBEDDINGS_ENDPOINT not set in .env or environment")
            return False, None, 0
        print(f"✅ AZURE_API_KEY and AZURE_EMBEDDINGS_ENDPOINT found")
        client = EmbeddingsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        model_name = "Cohere-embed-v3-english"
        test_texts = [
            "Hello world, this is a test.",
            "Cohere provides excellent embedding models.",
            "Azure AI services are powerful.",
            "Embeddings capture semantic meaning.",
            "Machine learning is transforming technology."
        ]
        # Single embedding
        print(f"\n📝 Testing single embedding...")
        start_time = time.time()
        response = client.embed(
            input=["test"],
            model=model_name,
            input_type="document"
        )
        single_time = time.time() - start_time
        dimension = len(response.data[0].embedding)
        print(f"✅ Single embedding successful")
        print(f"📏 Dimension: {dimension}")
        print(f"⏱️  Time: {single_time:.3f}s")
        # Batch embeddings
        print(f"\n📝 Testing batch embeddings...")
        start_time = time.time()
        response = client.embed(
            input=test_texts,
            model=model_name,
            input_type="document"
        )
        batch_time = time.time() - start_time
        embeddings = [item.embedding for item in response.data]
        print(f"✅ Batch embeddings successful")
        print(f"📊 Generated {len(embeddings)} embeddings")
        print(f"⏱️  Total time: {batch_time:.3f}s")
        print(f"📈 Average time per embedding: {batch_time/len(test_texts):.3f}s")
        return True, embeddings, dimension
    except ImportError as e:
        print(f"❌ Azure AI Inference package not installed: {e}")
        return False, None, 0
    except Exception as e:
        print(f"❌ Azure API error: {e}")
        return False, None, 0

def main():
    print("🚀 Cohere & Azure Embeddings Test (via Azure endpoints)")
    print("=" * 60)
    cohere_success, cohere_embeddings, cohere_dim = test_cohere_embeddings()
    azure_success, azure_embeddings, azure_dim = test_azure_embeddings()
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Cohere Embeddings (via Azure): {'✅ PASS' if cohere_success else '❌ FAIL'}")
    if cohere_success:
        print(f"  - Dimension: {cohere_dim}")
        print(f"  - Embeddings generated: {len(cohere_embeddings) if cohere_embeddings else 0}")
    print(f"Azure Embeddings (direct):     {'✅ PASS' if azure_success else '❌ FAIL'}")
    if azure_success:
        print(f"  - Dimension: {azure_dim}")
        print(f"  - Embeddings generated: {len(azure_embeddings) if azure_embeddings else 0}")
    if cohere_success and azure_success:
        print(f"\nBoth Cohere and Azure embeddings are working via Azure endpoints!")
    if cohere_success:
        print(f"\n🎉 Cohere embeddings via Azure are working properly!")
        return True
    else:
        print(f"\n💥 Cohere embeddings test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)