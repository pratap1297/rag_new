#!/usr/bin/env python3
"""
Excel File Ingestion Test with Azure AI Inference SDK
Shows how to ingest Excel files using proper Azure AI services
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

def create_azure_embedder():
    """Create Azure AI Inference embeddings client"""
    try:
        from azure.ai.inference import EmbeddingsClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = "https://azurehub1910875317.services.ai.azure.com/models"
        api_key = "6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr"
        model_name = "Cohere-embed-v3-english"
        
        client = EmbeddingsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        class AzureEmbedder:
            def __init__(self, client, model_name):
                self.client = client
                self.model_name = model_name
                self._dimension = None
                
            def embed_text(self, text: str):
                """Generate embedding for a single text"""
                return self.embed_texts([text])[0]
                
            def embed_texts(self, texts):
                """Generate embeddings for multiple texts"""
                response = self.client.embed(
                    input=texts,
                    model=self.model_name
                )
                embeddings = [item.embedding for item in response.data]
                if self._dimension is None:
                    self._dimension = len(embeddings[0]) if embeddings else 1024
                return embeddings
                
            def get_dimension(self):
                """Get embedding dimension"""
                if self._dimension is None:
                    # Test with a sample to get dimension
                    test_embedding = self.embed_text("test")
                    self._dimension = len(test_embedding)
                return self._dimension
        
        return AzureEmbedder(client, model_name)
        
    except ImportError:
        print("❌ Azure AI Inference SDK not installed. Run: pip install azure-ai-inference")
        return None
    except Exception as e:
        print(f"❌ Failed to create Azure embedder: {e}")
        return None

def ingest_excel_file():
    """Ingest Excel file using Azure AI services"""
    
    # Path to your Excel file
    excel_file_path = r'D:\Projects-D\pepsi-final2\document_generator\test_data\Facility_Managers_2024.xlsx'
    
    if not os.path.exists(excel_file_path):
        print(f"Excel file not found: {excel_file_path}")
        return
    
    try:
        print("🔧 Configuring Azure AI services...")
        
        # Configure Azure Computer Vision for Excel processor
        os.environ['COMPUTER_VISION_ENDPOINT'] = 'https://computervision1298.cognitiveservices.azure.com/'
        os.environ['COMPUTER_VISION_KEY'] = 'FSf3hSW3ogphcme0MgMMKZNTzkQTXo6sNikmlyUhSqahBHgnoaOFJQQJ99BFACYeBjFXJ3w3AAAFACOGPuhx'
        os.environ['COMPUTER_VISION_REGION'] = 'eastus'
        
        # Create Azure embedder
        print("🔧 Creating Azure AI embedder...")
        azure_embedder = create_azure_embedder()
        if not azure_embedder:
            print("❌ Failed to create Azure embedder")
            return
        
        print("✅ Azure AI embedder created successfully")
        
        # Initialize core components manually (without LLM dependency)
        print("🔧 Initializing core components...")
        
        # Initialize config manager
        from src.core.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        # Initialize FAISS store
        from src.storage.faiss_store import FAISSStore
        dimension = azure_embedder.get_dimension()
        print(f"📊 Using embedding dimension: {dimension}")
        
        faiss_store = FAISSStore(
            index_path="data/vectors/faiss_index.bin",
            dimension=dimension
        )
        
        # Initialize metadata store
        from src.storage.persistent_metadata_store import PersistentJSONMetadataStore
        metadata_store = PersistentJSONMetadataStore("data/metadata")
        
        # Initialize chunker
        from src.ingestion.chunker import Chunker
        chunker = Chunker(chunk_size=1000, chunk_overlap=200, use_semantic=True)
        
        # Initialize ingestion engine manually
        from src.ingestion.ingestion_engine import IngestionEngine
        ingestion_engine = IngestionEngine(
            chunker=chunker,
            embedder=azure_embedder,
            faiss_store=faiss_store,
            metadata_store=metadata_store,
            config_manager=config_manager
        )
        
        print("✅ Core components initialized")
        
        # Optional: Add custom metadata
        metadata = {
            'document_type': 'facility_management',
            'source': 'facility_managers_database',
            'department': 'operations',
            'doc_path': 'facility_managers_2024.xlsx',
            'processed_with': 'azure_ai_inference'
        }
        
        # Ingest the Excel file
        print(f"📄 Ingesting Excel file: {excel_file_path}")
        result = ingestion_engine.ingest_file(excel_file_path, metadata)
        
        print("\n=== 📊 Ingestion Result ===")
        print(f"Status: {result['status']}")
        print(f"File ID: {result.get('file_id')}")
        print(f"Chunks created: {result.get('chunks_created')}")
        print(f"Vectors stored: {result.get('vectors_stored')}")
        
        if result.get('is_update'):
            print(f"Updated existing file - replaced {result.get('old_vectors_deleted')} old vectors")
        
        # Test search using Azure AI embeddings
        print("\n=== 🔍 Testing Search with Azure AI Embeddings ===")
        try:
            # Create a search query using Azure AI embeddings
            query_text = "facility managers Building A"
            print(f"Searching for: '{query_text}'")
            query_embedding = azure_embedder.embed_text(query_text)
            
            # Search FAISS directly using Azure AI embeddings
            search_results = faiss_store.search(query_embedding, k=3)
            
            print(f"Found {len(search_results)} search results using Azure AI Cohere embeddings:")
            for i, result in enumerate(search_results, 1):
                print(f"\n📄 Result {i}:")
                print(f"   Score: {result.get('similarity_score', 0):.4f}")
                print(f"   Text: {result.get('content', result.get('text', 'No content'))[:200]}...")
                print(f"   Source: {result.get('file_name', result.get('filename', 'Unknown'))}")
                print(f"   Document Type: {result.get('document_type', 'Unknown')}")
                print(f"   File Path: {result.get('file_path', 'Unknown')}")
                
        except Exception as search_error:
            print(f"⚠️ Search test failed: {search_error}")
            
            # Try to show some basic stats instead
            try:
                index_info = faiss_store.get_index_info()
                print(f"✅ Vector store now contains {index_info.get('ntotal', 0)} vectors")
                print("✅ Excel file was successfully ingested even though search test failed")
            except Exception as e:
                print(f"Could not get vector store stats: {e}")
        
        print("\n🎉 Excel file successfully ingested using Azure AI Inference SDK!")
        print("🔍 Your Excel data is now searchable using Azure AI Cohere embeddings")
        print("📊 Advanced Excel processing with Azure Computer Vision completed")
        
    except Exception as e:
        print(f"❌ Error during ingestion: {str(e)}")
        import traceback
        print("\nDetailed error:")
        print(traceback.format_exc())

if __name__ == '__main__':
    print("🚀 Starting Excel ingestion with Azure AI Inference SDK...")
    ingest_excel_file() 