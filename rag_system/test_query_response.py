#!/usr/bin/env python3
"""
Test script to verify the actual query engine response with new source labels
"""

import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.storage.faiss_store import FAISSStore
from src.ingestion.embedder import Embedder
from src.retrieval.query_engine import QueryEngine

def test_query_response():
    """Test the actual query engine response with new source labels"""
    
    print("🔍 Testing Query Engine Response")
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
            # Return a response that shows the source labels
            return "Based on the ServiceNow incidents report, there are 5 total incidents with 2 high priority, 2 medium priority, and 1 low priority. The incidents include network connectivity issues, software license renewals, printer malfunctions, email system performance problems, and database backup verification needs."
    
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
    test_query = "How many ServiceNow incidents are there and what are they?"
    print(f"🔍 Testing query: '{test_query}'")
    
    # Process query
    response = query_engine.process_query(test_query, top_k=3)
    
    print(f"\n📝 Response: {response.get('response', 'No response')}")
    print(f"🎯 Confidence: {response.get('confidence_score', 0):.3f}")
    print(f"📊 Total sources: {response.get('total_sources', 0)}")
    
    # Show sources
    sources = response.get('sources', [])
    print(f"\n📚 Sources ({len(sources)}):")
    
    for i, source in enumerate(sources, 1):
        print(f"\n  Source {i}:")
        print(f"    Label: '{source.get('source_label', 'N/A')}'")
        print(f"    Original filename: '{source.get('original_filename', 'N/A')}'")
        print(f"    File path: '{source.get('file_path', 'N/A')}'")
        print(f"    Filename: '{source.get('filename', 'N/A')}'")
        print(f"    Similarity score: {source.get('similarity_score', 0):.3f}")
        print(f"    Text preview: '{source.get('text', 'N/A')[:150]}...'")
    
    print("\n✅ Query engine response test completed!")

if __name__ == "__main__":
    test_query_response() 