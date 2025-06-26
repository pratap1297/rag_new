#!/usr/bin/env python3
"""
Script to ingest AP Models documentation into the vector database
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

def ingest_ap_models():
    """Ingest AP Models documentation"""
    
    print("📥 Ingesting AP Models Documentation")
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
    
    # AP Models file path
    ap_models_file = "test_documents/ap_models_documentation.md"
    ap_models_file_path = os.path.abspath(ap_models_file)
    
    print(f"📄 Processing file: {ap_models_file_path}")
    
    # Read the AP Models file
    with open(ap_models_file, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    print(f"📊 File content length: {len(text_content)} characters")
    
    # Prepare file metadata
    file_metadata = {
        'file_path': ap_models_file_path,
        'original_filename': ap_models_file_path,
        'filename': os.path.basename(ap_models_file_path),
        'file_size': len(text_content),
        'file_type': '.md',
        'source_type': 'file',
        'title': 'AP Models Documentation',
        'category': 'technical',
        'tags': ['access points', 'wireless', 'network', 'cisco', 'aruba', 'ubiquiti']
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
            'doc_id': f"ap_models_doc_chunk_{i}",
            'filename': os.path.basename(ap_models_file_path),
            'original_filename': ap_models_file_path,
            'file_path': ap_models_file_path,
            'source_type': 'file',
            'title': 'AP Models Documentation',
            'category': 'technical',
            'tags': ['access points', 'wireless', 'network', 'cisco', 'aruba', 'ubiquiti']
        }
        chunk_metadata_list.append(chunk_metadata)
    
    # Add to FAISS store
    vector_ids = faiss_store.add_vectors(embeddings, chunk_metadata_list)
    print(f"💾 Stored {len(vector_ids)} vectors in FAISS")
    
    # Store file metadata
    file_id = metadata_store.add_file_metadata(ap_models_file_path, {
        **file_metadata,
        'chunk_count': len(chunks),
        'vector_ids': vector_ids
    })
    
    print(f"📁 Stored file metadata with ID: {file_id}")
    
    # Test search for AP Models
    print("\n🔍 Testing search for AP Models:")
    test_query = "List all AP Models"
    query_embedding = embedder.embed_text(test_query)
    results = faiss_store.search_with_metadata(query_embedding, k=5)
    
    print(f"📋 Found {len(results)} results for query: '{test_query}'")
    
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        metadata = result.get('metadata', {})
        print(f"    Title: {metadata.get('title', 'N/A')}")
        print(f"    Category: {metadata.get('category', 'N/A')}")
        print(f"    Tags: {metadata.get('tags', 'N/A')}")
        print(f"    Text preview: {result.get('text', 'N/A')[:200]}...")
    
    print("\n✅ AP Models ingestion completed successfully!")

if __name__ == "__main__":
    ingest_ap_models() 