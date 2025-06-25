#!/usr/bin/env python3
"""
Debug Embeddings
Test the embedding generation process to see if query embeddings are being generated correctly
"""
import sys
import os
sys.path.append('rag_system/src')

import numpy as np
from rag_system.src.ingestion.embedder import Embedder
from rag_system.src.storage.faiss_store import FAISSStore
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_embeddings():
    """Debug the embedding generation process"""
    print("🧠 Debugging Embedding Generation")
    print("=" * 50)
    
    try:
        # Initialize the embedder (same as used by the system)
        print("1. 🚀 Initializing Embedder...")
        
        embedder = Embedder(
            provider='azure',
            api_key=os.getenv('AZURE_API_KEY', '6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr'),
            endpoint=os.getenv('AZURE_EMBEDDINGS_ENDPOINT', 'https://azurehub1910875317.services.ai.azure.com/models'),
            model_name=os.getenv('RAG_EMBEDDING_MODEL', 'Cohere-embed-v3-english')
        )
        
        print(f"   ✅ Embedder initialized")
        print(f"   Provider: {embedder.provider}")
        print(f"   Model: {embedder.model_name}")
        
        # Test embedding generation
        print("\n2. 🧪 Testing Embedding Generation...")
        
        test_queries = [
            "security",
            "password policy",
            "What is the security policy?",
            "test"
        ]
        
        embeddings_generated = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: '{query}'")
            
            try:
                embedding = embedder.embed_text(query)
                
                if embedding and len(embedding) > 0:
                    print(f"   ✅ Embedding generated successfully")
                    print(f"   📊 Dimension: {len(embedding)}")
                    print(f"   📈 Sample values: {embedding[:5]}...")
                    print(f"   🔢 Data type: {type(embedding[0])}")
                    
                    # Check if embedding is normalized
                    norm = np.linalg.norm(embedding)
                    print(f"   📏 L2 norm: {norm:.6f}")
                    
                    embeddings_generated += 1
                else:
                    print(f"   ❌ Empty or invalid embedding generated")
                    
            except Exception as e:
                print(f"   ❌ Embedding generation failed: {e}")
                import traceback
                traceback.print_exc()
        
        if embeddings_generated == 0:
            print(f"\n❌ No embeddings generated successfully!")
            print(f"   This explains why queries return no results.")
            return False
        
        # Test direct search with generated embedding
        print(f"\n3. 🔍 Testing Direct Search with Generated Embedding...")
        
        # Use the first successful embedding
        test_query = "security"
        test_embedding = embedder.embed_text(test_query)
        
        if test_embedding:
            print(f"   Using query: '{test_query}'")
            print(f"   Embedding dimension: {len(test_embedding)}")
            
            # Initialize FAISS store
            faiss_store = FAISSStore(
                index_path="rag_system/data/vectors/faiss_index.bin",
                dimension=1024
            )
            
            # Perform search
            results = faiss_store.search_with_metadata(test_embedding, k=10)
            
            print(f"   📚 Search results: {len(results)} found")
            
            if results:
                print(f"   ✅ SUCCESS: Query embedding search works!")
                
                # Show similarity scores
                similarities = [r.get('similarity_score', 0) for r in results]
                print(f"   📊 Similarity range: {min(similarities):.6f} to {max(similarities):.6f}")
                
                # Show first result
                first_result = results[0]
                print(f"\n   📄 Best match:")
                print(f"      Similarity: {first_result.get('similarity_score', 0):.6f}")
                print(f"      Content: {first_result.get('content', '')[:100]}...")
                
                return True
            else:
                print(f"   ❌ No results from search with generated embedding")
                return False
        else:
            print(f"   ❌ Failed to generate test embedding")
            return False
        
    except Exception as e:
        print(f"❌ Error during embedding debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_embeddings():
    """Compare embeddings from different sources"""
    print(f"\n4. 🔄 Comparing Embedding Consistency...")
    
    try:
        embedder = Embedder(
            provider='azure',
            api_key=os.getenv('AZURE_API_KEY', '6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr'),
            endpoint=os.getenv('AZURE_EMBEDDINGS_ENDPOINT', 'https://azurehub1910875317.services.ai.azure.com/models'),
            model_name=os.getenv('RAG_EMBEDDING_MODEL', 'Cohere-embed-v3-english')
        )
        
        # Generate embedding for same text multiple times
        test_text = "security policy requirements"
        
        embeddings = []
        for i in range(3):
            embedding = embedder.embed_text(test_text)
            embeddings.append(embedding)
            print(f"   Embedding {i+1}: {len(embedding)} dims, first 3 values: {embedding[:3]}")
        
        # Check consistency
        if len(embeddings) >= 2:
            similarity_12 = np.dot(embeddings[0], embeddings[1])
            similarity_13 = np.dot(embeddings[0], embeddings[2])
            
            print(f"   📊 Embedding consistency:")
            print(f"      Similarity 1-2: {similarity_12:.6f}")
            print(f"      Similarity 1-3: {similarity_13:.6f}")
            
            if similarity_12 > 0.99 and similarity_13 > 0.99:
                print(f"   ✅ Embeddings are consistent")
            else:
                print(f"   ⚠️ Embeddings vary between calls")
        
    except Exception as e:
        print(f"   ❌ Embedding comparison failed: {e}")

if __name__ == "__main__":
    print("🔧 Starting Embedding Debug...")
    
    success = debug_embeddings()
    compare_embeddings()
    
    if success:
        print(f"\n✅ Embedding generation is working!")
        print(f"   The issue may be elsewhere in the query pipeline.")
    else:
        print(f"\n❌ Embedding generation has issues!")
        print(f"   This is likely the root cause of the query problem.")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. If embeddings work, check the query engine pipeline")
    print(f"   2. If embeddings fail, check Azure AI configuration")
    print(f"   3. Verify the embedding model name and endpoint")
    print(f"   4. Check API key validity and rate limits") 