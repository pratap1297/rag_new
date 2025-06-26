#!/usr/bin/env python3
"""
Test ingestion script to verify source labels work correctly
"""

import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.storage.faiss_store import FAISSStore
from src.ingestion.embedder import Embedder
from src.ingestion.chunker import Chunker
from src.storage.persistent_metadata_store import PersistentJSONMetadataStore

def test_ingestion():
    """Test ingestion with proper source labels"""
    
    print("📥 Testing Document Ingestion")
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
    
    # Initialize metadata store
    metadata_store = PersistentJSONMetadataStore("data/metadata")
    
    # Initialize chunker
    chunker = Chunker(
        chunk_size=1000,
        chunk_overlap=200,
        use_semantic=True
    )
    
    # Test file path
    test_file = "test_document.txt"
    test_file_path = os.path.abspath(test_file)
    
    print(f"📄 Testing with file: {test_file_path}")
    
    # Read the test file
    with open(test_file, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    print(f"📊 File content length: {len(text_content)} characters")
    
    # Prepare file metadata with full path
    file_metadata = {
        'file_path': test_file_path,
        'original_filename': test_file_path,  # Full path
        'filename': os.path.basename(test_file_path),
        'file_size': len(text_content),
        'file_type': '.txt',
        'source_type': 'file',
        'test_document': True
    }
    
    print(f"📋 File metadata: {file_metadata}")
    
    # Chunk the text
    chunks = chunker.chunk_text(text_content, file_metadata)
    print(f"🔪 Created {len(chunks)} chunks")
    
    # Generate embeddings
    chunk_texts = [chunk['text'] for chunk in chunks]
    embeddings = embedder.embed_texts(chunk_texts)
    print(f"🧠 Generated {len(embeddings)} embeddings")
    
    # Prepare chunk metadata
    chunk_metadata_list = []
    for i, chunk in enumerate(chunks):
        chunk_metadata = {
            'text': chunk['text'],
            'content': chunk['text'],
            'chunk_index': i,
            'total_chunks': len(chunks),
            'chunk_size': len(chunk['text']),
            'doc_id': f"test_doc_{i}",
            'filename': os.path.basename(test_file_path),
            'original_filename': test_file_path,  # Full path
            'file_path': test_file_path,  # Full path
            'source_type': 'file',
            'test_document': True
        }
        chunk_metadata_list.append(chunk_metadata)
    
    # Add to FAISS store
    vector_ids = faiss_store.add_vectors(embeddings, chunk_metadata_list)
    print(f"💾 Stored {len(vector_ids)} vectors in FAISS")
    
    # Store file metadata
    file_id = metadata_store.add_file_metadata(test_file_path, {
        **file_metadata,
        'chunk_count': len(chunks),
        'vector_ids': vector_ids
    })
    
    print(f"📁 Stored file metadata with ID: {file_id}")
    
    # Test search
    print("\n🔍 Testing search functionality:")
    test_query = "ServiceNow incidents"
    query_embedding = embedder.embed_text(test_query)
    results = faiss_store.search_with_metadata(query_embedding, k=3)
    
    print(f"📋 Found {len(results)} results for query: '{test_query}'")
    
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        metadata = result.get('metadata', {})
        print(f"    original_filename: {metadata.get('original_filename', 'N/A')}")
        print(f"    file_path: {metadata.get('file_path', 'N/A')}")
        print(f"    filename: {result.get('filename', 'N/A')}")
        print(f"    text preview: {result.get('text', 'N/A')[:100]}...")
    
    print("\n✅ Ingestion test completed successfully!")

if __name__ == "__main__":
    test_ingestion() 