#!/usr/bin/env python3
"""
Debug search results to see what metadata is available
"""

import json
import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.storage.faiss_store import FAISSStore
from src.ingestion.embedder import Embedder

def debug_search_results():
    """Debug what metadata is returned by search"""
    
    print("🔍 Debugging Search Results")
    print("=" * 50)
    
    # Initialize components
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Initialize embedder
    embedder = Embedder(
        provider=config.embedding.provider,
        model_name=config.embedding.model_name,
        device=config.embedding.device,
        batch_size=config.embedding.batch_size,
        api_key=config.embedding.api_key,
        endpoint=os.getenv('AZURE_EMBEDDINGS_ENDPOINT') if config.embedding.provider == 'azure' else None
    )
    
    # Initialize FAISS store with correct parameters
    faiss_store = FAISSStore(
        index_path="data/vectors/index.faiss",
        dimension=config.embedding.dimension
    )
    
    # Test query
    test_query = "ServiceNow incidents"
    print(f"🔍 Testing query: '{test_query}'")
    
    # Get query embedding
    query_embedding = embedder.embed_text(test_query)
    print(f"📊 Query embedding dimension: {len(query_embedding)}")
    
    # Search with metadata
    results = faiss_store.search_with_metadata(query_embedding, k=3)
    print(f"📋 Found {len(results)} results")
    
    print("\n📄 Detailed result analysis:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    vector_id: {result.get('vector_id', 'N/A')}")
        print(f"    doc_id: {result.get('doc_id', 'N/A')}")
        print(f"    filename: {result.get('filename', 'N/A')}")
        print(f"    chunk_id: {result.get('chunk_id', 'N/A')}")
        print(f"    similarity_score: {result.get('similarity_score', 'N/A')}")
        print(f"    content preview: {result.get('text', 'N/A')[:100]}...")
        
        # Check metadata
        metadata = result.get('metadata', {})
        print(f"    metadata keys: {list(metadata.keys())}")
        
        # Check for source information in metadata
        source_fields = ['source', 'file_path', 'original_filename', 'source_type']
        for field in source_fields:
            if field in metadata:
                print(f"    metadata.{field}: {metadata[field]}")
    
    # Check what would be the best source label
    print("\n🎯 Source Label Analysis:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i} source options:")
        
        # Priority order for source labels
        source_options = [
            result.get('metadata', {}).get('original_filename'),
            result.get('metadata', {}).get('file_path'),
            result.get('filename'),
            result.get('metadata', {}).get('source'),
            result.get('doc_id'),
            f"Source {i}"
        ]
        
        for j, option in enumerate(source_options, 1):
            if option and option != 'unknown':
                print(f"    {j}. {option}")
                break
        else:
            print(f"    Fallback: Source {i}")

if __name__ == "__main__":
    debug_search_results() 