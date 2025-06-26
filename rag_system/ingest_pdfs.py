#!/usr/bin/env python3
"""
Simple script to ingest PDF files containing AP Models information
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
from src.ingestion.processors.pdf_processor import PDFProcessor

def ingest_pdf_files():
    """Ingest PDF files containing AP Models information"""
    
    print("📥 Ingesting PDF files with AP Models information")
    print("=" * 60)
    
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
    
    # Initialize PDF processor
    pdf_processor = PDFProcessor()
    
    # List of PDF files to ingest
    pdf_files = [
        "test_documents/BuildingA_Network_Layout.pdf",
        "test_documents/BuildingB_Network_Layout.pdf", 
        "test_documents/BuildingC_Network_Layout.pdf"
    ]
    
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            print(f"❌ File not found: {pdf_file}")
            continue
            
        print(f"\n📄 Processing: {pdf_file}")
        
        try:
            # Extract text from PDF
            text_content = pdf_processor.extract_text(pdf_file)
            print(f"📊 Extracted {len(text_content)} characters from PDF")
            
            # Prepare file metadata
            file_metadata = {
                'file_path': os.path.abspath(pdf_file),
                'original_filename': os.path.abspath(pdf_file),
                'filename': os.path.basename(pdf_file),
                'file_size': len(text_content),
                'file_type': '.pdf',
                'source_type': 'file',
                'category': 'network_layout',
                'tags': ['access points', 'wireless', 'network', 'ap models']
            }
            
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
                    'doc_id': f"{os.path.basename(pdf_file).replace('.pdf', '')}_chunk_{i}",
                    'filename': os.path.basename(pdf_file),
                    'original_filename': os.path.abspath(pdf_file),
                    'file_path': os.path.abspath(pdf_file),
                    'source_type': 'file',
                    'category': 'network_layout',
                    'tags': ['access points', 'wireless', 'network', 'ap models']
                }
                chunk_metadata_list.append(chunk_metadata)
            
            # Add to FAISS store
            vector_ids = faiss_store.add_vectors(embeddings, chunk_metadata_list)
            print(f"💾 Stored {len(vector_ids)} vectors in FAISS")
            
            # Store file metadata
            file_id = metadata_store.add_file_metadata(pdf_file, {
                **file_metadata,
                'chunk_count': len(chunks),
                'vector_ids': vector_ids
            })
            
            print(f"📁 Stored file metadata with ID: {file_id}")
            print(f"✅ Successfully ingested: {pdf_file}")
            
        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")
            continue
    
    # Test search for AP Models
    print("\n🔍 Testing search for AP Models:")
    test_query = "List all AP Models"
    query_embedding = embedder.embed_text(test_query)
    results = faiss_store.search_with_metadata(query_embedding, k=5)
    
    print(f"📋 Found {len(results)} results for query: '{test_query}'")
    
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        metadata = result.get('metadata', {})
        print(f"    File: {metadata.get('filename', 'N/A')}")
        print(f"    Category: {metadata.get('category', 'N/A')}")
        print(f"    Tags: {metadata.get('tags', 'N/A')}")
        print(f"    Text preview: {result.get('text', 'N/A')[:200]}...")
    
    print("\n✅ PDF ingestion completed successfully!")

if __name__ == "__main__":
    ingest_pdf_files() 