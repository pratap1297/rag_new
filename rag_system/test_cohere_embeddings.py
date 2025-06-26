#!/usr/bin/env python3
"""
Cohere Embeddings Test
Tests Cohere embeddings and compares with Azure embeddings to ensure they're working properly.
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_cohere_embeddings():
    """Test Cohere embeddings directly"""
    print("🔍 Testing Cohere Embeddings")
    print("=" * 50)
    
    try:
        import cohere
        
        # Check API key
        api_key = os.getenv('COHERE_API_KEY')
        if not api_key:
            print("❌ COHERE_API_KEY not set")
            return False, None, 0
        
        print(f"✅ Cohere API key found (length: {len(api_key)})")
        
        # Initialize client
        client = cohere.Client(api_key)
        model_name = "embed-english-v3.0"
        
        # Test texts
        test_texts = [
            "Hello world, this is a test.",
            "Cohere provides excellent embedding models.",
            "Azure AI services are powerful.",
            "Embeddings capture semantic meaning.",
            "Machine learning is transforming technology."
        ]
        
        # Test single embedding
        print(f"\n📝 Testing single embedding...")
        start_time = time.time()
        response = client.embed(
            texts=["test"],
            model=model_name,
            input_type="search_document"
        )
        single_time = time.time() - start_time
        
        dimension = len(response.embeddings[0])
        print(f"✅ Single embedding successful")
        print(f"📏 Dimension: {dimension}")
        print(f"⏱️  Time: {single_time:.3f}s")
        
        # Test batch embeddings
        print(f"\n📝 Testing batch embeddings...")
        start_time = time.time()
        response = client.embed(
            texts=test_texts,
            model=model_name,
            input_type="search_document"
        )
        batch_time = time.time() - start_time
        
        embeddings = response.embeddings
        print(f"✅ Batch embeddings successful")
        print(f"📊 Generated {len(embeddings)} embeddings")
        print(f"⏱️  Total time: {batch_time:.3f}s")
        print(f"📈 Average time per embedding: {batch_time/len(test_texts):.3f}s")
        
        return True, embeddings, dimension
        
    except ImportError as e:
        print(f"❌ Cohere package not installed: {e}")
        return False, None, 0
    except Exception as e:
        print(f"❌ Cohere API error: {e}")
        return False, None, 0

def test_azure_embeddings():
    """Test Azure embeddings for comparison"""
    print("\n🔍 Testing Azure Embeddings (for comparison)")
    print("=" * 50)
    
    try:
        from azure.ai.inference import EmbeddingsClient
        from azure.core.credentials import AzureKeyCredential
        
        # Check credentials
        api_key = os.getenv('AZURE_API_KEY')
        endpoint = os.getenv('AZURE_EMBEDDINGS_ENDPOINT')
        
        if not api_key or not endpoint:
            print("⚠️  Azure credentials not set, skipping Azure test")
            return False, None, 0
        
        print(f"✅ Azure credentials found")
        
        # Initialize client
        client = EmbeddingsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        model_name = "Cohere-embed-v3-english"
        
        # Test texts (same as Cohere)
        test_texts = [
            "Hello world, this is a test.",
            "Cohere provides excellent embedding models.",
            "Azure AI services are powerful.",
            "Embeddings capture semantic meaning.",
            "Machine learning is transforming technology."
        ]
        
        # Test single embedding
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
        
        # Test batch embeddings
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

def test_our_embedder_classes():
    """Test our custom embedder classes"""
    print("\n🔧 Testing Our Embedder Classes")
    print("=" * 50)
    
    try:
        from ingestion.embedder import CohereEmbedder, AzureEmbedder
        
        test_texts = [
            "Hello world, this is a test.",
            "Cohere provides excellent embedding models.",
            "Azure AI services are powerful.",
            "Embeddings capture semantic meaning.",
            "Machine learning is transforming technology."
        ]
        
        # Test CohereEmbedder
        print("Testing CohereEmbedder...")
        try:
            cohere_embedder = CohereEmbedder(
                model_name="embed-english-v3.0",
                api_key=os.getenv('COHERE_API_KEY')
            )
            
            start_time = time.time()
            embeddings = cohere_embedder.embed_texts(test_texts)
            batch_time = time.time() - start_time
            
            print(f"✅ CohereEmbedder working")
            print(f"📏 Dimension: {cohere_embedder.get_dimension()}")
            print(f"⏱️  Time: {batch_time:.3f}s")
            print(f"📊 Generated {len(embeddings)} embeddings")
            
        except Exception as e:
            print(f"❌ CohereEmbedder failed: {e}")
        
        # Test AzureEmbedder
        print("\nTesting AzureEmbedder...")
        try:
            azure_embedder = AzureEmbedder(
                model_name="Cohere-embed-v3-english",
                api_key=os.getenv('AZURE_API_KEY'),
                endpoint=os.getenv('AZURE_EMBEDDINGS_ENDPOINT')
            )
            
            start_time = time.time()
            embeddings = azure_embedder.embed_texts(test_texts)
            batch_time = time.time() - start_time
            
            print(f"✅ AzureEmbedder working")
            print(f"📏 Dimension: {azure_embedder.get_dimension()}")
            print(f"⏱️  Time: {batch_time:.3f}s")
            print(f"📊 Generated {len(embeddings)} embeddings")
            
        except Exception as e:
            print(f"❌ AzureEmbedder failed: {e}")
            
    except ImportError as e:
        print(f"❌ Cannot import embedder classes: {e}")

def compare_embeddings(cohere_embeddings, azure_embeddings):
    """Compare Cohere and Azure embeddings"""
    if not cohere_embeddings or not azure_embeddings:
        print("\n⚠️  Cannot compare embeddings - missing data")
        return
    
    print("\n🔍 Comparing Cohere vs Azure Embeddings")
    print("=" * 50)
    
    # Convert to numpy arrays
    cohere_emb = np.array(cohere_embeddings)
    azure_emb = np.array(azure_embeddings)
    
    # Check dimensions
    cohere_dim = cohere_emb.shape[1]
    azure_dim = azure_emb.shape[1]
    
    print(f"📏 Cohere dimension: {cohere_dim}")
    print(f"📏 Azure dimension: {azure_dim}")
    
    if cohere_dim != azure_dim:
        print("⚠️  Dimensions don't match - cannot compare directly")
        return
    
    # Normalize for cosine similarity
    cohere_norm = cohere_emb / np.linalg.norm(cohere_emb, axis=1, keepdims=True)
    azure_norm = azure_emb / np.linalg.norm(azure_emb, axis=1, keepdims=True)
    
    # Calculate similarities
    similarities = np.sum(cohere_norm * azure_norm, axis=1)
    
    # Statistics
    mean_sim = np.mean(similarities)
    std_sim = np.std(similarities)
    min_sim = np.min(similarities)
    max_sim = np.max(similarities)
    
    print(f"\n📊 Similarity Statistics:")
    print(f"   Mean: {mean_sim:.4f}")
    print(f"   Std:  {std_sim:.4f}")
    print(f"   Min:  {min_sim:.4f}")
    print(f"   Max:  {max_sim:.4f}")
    
    # Test semantic search
    print(f"\n🔍 Testing Semantic Search:")
    test_queries = [
        "What is machine learning?",
        "How does Azure work?",
        "Tell me about Cohere"
    ]
    
    for i, query in enumerate(test_queries):
        if i < len(cohere_norm):
            # Use the first embedding as query
            query_emb = cohere_norm[i]
            
            # Calculate similarities
            cohere_sims = np.dot(cohere_norm, query_emb)
            azure_sims = np.dot(azure_norm, query_emb)
            
            # Get top matches
            cohere_top = np.argsort(cohere_sims)[-3:][::-1]
            azure_top = np.argsort(azure_sims)[-3:][::-1]
            
            print(f"\nQuery: {query}")
            print(f"  Cohere top matches: {[f'{idx}({cohere_sims[idx]:.3f})' for idx in cohere_top]}")
            print(f"  Azure top matches:  {[f'{idx}({azure_sims[idx]:.3f})' for idx in azure_top]}")

def main():
    """Main test function"""
    print("🚀 Cohere Embeddings Test")
    print("=" * 60)
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
    
    # Test Cohere embeddings
    cohere_success, cohere_embeddings, cohere_dim = test_cohere_embeddings()
    
    # Test Azure embeddings
    azure_success, azure_embeddings, azure_dim = test_azure_embeddings()
    
    # Test our embedder classes
    test_our_embedder_classes()
    
    # Compare embeddings if both succeeded
    if cohere_success and azure_success:
        compare_embeddings(cohere_embeddings, azure_embeddings)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    print(f"Cohere Embeddings: {'✅ PASS' if cohere_success else '❌ FAIL'}")
    if cohere_success:
        print(f"  - Dimension: {cohere_dim}")
        print(f"  - Embeddings generated: {len(cohere_embeddings) if cohere_embeddings else 0}")
    
    print(f"Azure Embeddings:  {'✅ PASS' if azure_success else '❌ FAIL'}")
    if azure_success:
        print(f"  - Dimension: {azure_dim}")
        print(f"  - Embeddings generated: {len(azure_embeddings) if azure_embeddings else 0}")
    
    if cohere_success and azure_success:
        print(f"Embedding Comparison: ✅ COMPLETED")
        if cohere_dim == azure_dim:
            print(f"  - Dimensions match: ✅")
        else:
            print(f"  - Dimensions differ: ⚠️")
    
    # Overall result
    if cohere_success:
        print(f"\n🎉 Cohere embeddings are working properly!")
        if azure_success:
            print(f"🎉 Both Cohere and Azure embeddings are working!")
        return True
    else:
        print(f"\n💥 Cohere embeddings test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)