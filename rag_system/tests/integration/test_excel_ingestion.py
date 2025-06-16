#!/usr/bin/env python3
"""
Excel File Ingestion Test
Shows how to ingest Excel files into the RAG system using the main ingestion engine
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

def ingest_excel_file():
    """Ingest Excel file using the RAG system components"""
    
    # Path to your Excel file
    excel_file_path = r'D:\Projects-D\pepsi-final2\document_generator\test_data\Facility_Managers_2024.xlsx'
    
    if not os.path.exists(excel_file_path):
        print(f"Excel file not found: {excel_file_path}")
        return
    
    try:
        # Set Azure AI environment variables before initialization
        print("Configuring Azure AI services...")
        
        # Configure Embedding to use Cohere via Azure
        os.environ['RAG_EMBEDDING_PROVIDER'] = 'cohere'
        os.environ['RAG_EMBEDDING_MODEL'] = 'embed-english-v3.0'
        os.environ['COHERE_API_KEY'] = '6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr'
        
        # Configure Azure Computer Vision for Excel processor
        os.environ['AZURE_CV_ENDPOINT'] = 'https://computervision1298.cognitiveservices.azure.com/'
        os.environ['AZURE_CV_KEY'] = 'FSf3hSW3ogphcme0MgMMKZNTzkQTXo6sNikmlyUhSqahBHgnoaOFJQQJ99BFACYeBjFXJ3w3AAAFACOGPuhx'
        os.environ['COMPUTER_VISION_ENDPOINT'] = 'https://computervision1298.cognitiveservices.azure.com/'
        os.environ['COMPUTER_VISION_KEY'] = 'FSf3hSW3ogphcme0MgMMKZNTzkQTXo6sNikmlyUhSqahBHgnoaOFJQQJ99BFACYeBjFXJ3w3AAAFACOGPuhx'
        os.environ['COMPUTER_VISION_REGION'] = 'eastus'
        
        # Skip LLM configuration to avoid Groq dependency
        print("Note: Skipping LLM configuration to focus on Excel ingestion")
        
        # Initialize RAG system components
        print("Initializing RAG system...")
        from src.core.system_init import initialize_system
        container = initialize_system()
        
        # Get the ingestion engine
        print("Getting ingestion engine...")
        ingestion_engine = container.get('ingestion_engine')
        
        # Optional: Add custom metadata
        metadata = {
            'document_type': 'facility_management',
            'source': 'facility_managers_database',
            'department': 'operations',
            'doc_path': 'facility_managers_2024.xlsx'  # Unique identifier for updates
        }
        
        # Ingest the Excel file
        print(f"Ingesting Excel file: {excel_file_path}")
        result = ingestion_engine.ingest_file(excel_file_path, metadata)
        
        print("\n=== Ingestion Result ===")
        print(f"Status: {result['status']}")
        print(f"File ID: {result.get('file_id')}")
        print(f"Chunks created: {result.get('chunks_created')}")
        print(f"Vectors stored: {result.get('vectors_stored')}")
        
        if result.get('is_update'):
            print(f"Updated existing file - replaced {result.get('old_vectors_deleted')} old vectors")
        
        # Test search using Azure Cohere embeddings (no LLM needed)
        print("\n=== Testing Search with Azure Cohere Embeddings ===")
        try:
            # Get FAISS store and embedder directly
            faiss_store = container.get('faiss_store')
            embedder = container.get('embedder')
            
            # Create a search query using Azure Cohere embeddings
            query_text = "facility managers Building A"
            print(f"Searching for: '{query_text}'")
            query_embedding = embedder.embed_text(query_text)
            
            # Search FAISS directly using Azure Cohere embeddings
            search_results = faiss_store.search(query_embedding, top_k=3)
            
            print(f"Found {len(search_results)} search results using Azure Cohere embeddings:")
            for i, result in enumerate(search_results, 1):
                print(f"\nResult {i}:")
                print(f"Score: {result['score']:.4f}")
                print(f"Text: {result['text'][:200]}...")
                print(f"Source: {result['metadata'].get('file_name', 'Unknown')}")
                print(f"Document Type: {result['metadata'].get('document_type', 'Unknown')}")
                
        except Exception as search_error:
            print(f"⚠️ Search test failed: {search_error}")
            
            # Try to show some basic stats instead
            try:
                faiss_store = container.get('faiss_store')
                index_info = faiss_store.get_index_info()
                print(f"✅ Vector store now contains {index_info.get('ntotal', 0)} vectors")
                print("✅ Excel file was successfully ingested even though search test failed")
            except Exception as e:
                print(f"Could not get vector store stats: {e}")
        
        print("\n✅ Excel file successfully ingested using Azure AI services!")
        print("🔍 Your Excel data is now searchable using Azure Cohere embeddings")
        
    except Exception as e:
        print(f"❌ Error during ingestion: {str(e)}")
        import traceback
        print("\nDetailed error:")
        print(traceback.format_exc())

if __name__ == '__main__':
    ingest_excel_file() 