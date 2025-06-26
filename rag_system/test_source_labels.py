#!/usr/bin/env python3
"""
Test script to verify source labels are working correctly
"""

import json
import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.storage.faiss_store import FAISSStore
from src.ingestion.embedder import Embedder
from src.retrieval.query_engine import QueryEngine
from src.retrieval.llm_client import LLMClient

def test_source_labels():
    """Test that source labels are working correctly"""
    
    print("🧪 Testing Source Labels")
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
    
    # Initialize FAISS store
    faiss_store = FAISSStore(
        index_path="data/vectors/index.faiss",
        dimension=config.embedding.dimension
    )
    
    # Initialize LLM client (mock for testing)
    class MockLLMClient:
        def generate(self, prompt):
            return "This is a test response from the mock LLM client."
    
    llm_client = MockLLMClient()
    
    # Initialize query engine
    query_engine = QueryEngine(
        faiss_store=faiss_store,
        embedder=embedder,
        llm_client=llm_client,
        metadata_store=None,  # Not needed for this test
        config_manager=config_manager
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
    
    if not results:
        print("❌ No results found. This might be because:")
        print("   - No documents have been ingested yet")
        print("   - The query doesn't match any content")
        print("   - The vector database is empty")
        return
    
    print("\n📄 Testing source label generation:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Raw metadata: {result.get('metadata', {})}")
        
        # Test the source label generation
        source_label = query_engine._get_source_label(result, i)
        print(f"    Generated source label: '{source_label}'")
        
        # Show what fields are available
        metadata = result.get('metadata', {})
        print(f"    Available fields:")
        print(f"      - original_filename: {metadata.get('original_filename', 'N/A')}")
        print(f"      - file_path: {metadata.get('file_path', 'N/A')}")
        print(f"      - filename: {result.get('filename', 'N/A')}")
        print(f"      - source: {metadata.get('source', 'N/A')}")
        print(f"      - doc_id: {result.get('doc_id', 'N/A')}")
    
    # Test the format_sources method
    print("\n🎯 Testing _format_sources method:")
    formatted_sources = query_engine._format_sources(results)
    
    for i, source in enumerate(formatted_sources, 1):
        print(f"\n  Formatted Source {i}:")
        print(f"    source_label: '{source.get('source_label', 'N/A')}'")
        print(f"    original_filename: '{source.get('original_filename', 'N/A')}'")
        print(f"    file_path: '{source.get('file_path', 'N/A')}'")
        print(f"    filename: '{source.get('filename', 'N/A')}'")
        print(f"    text preview: '{source.get('text', 'N/A')[:100]}...'")
    
    print("\n✅ Source label test completed!")

if __name__ == "__main__":
    test_source_labels() 