#!/usr/bin/env python3
"""
Test Azure Embeddings
Simple test to verify Azure Cohere v3 embeddings configuration
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_azure_embeddings():
    """Test Azure embeddings client directly"""
    print("🧪 Testing Azure Embeddings (Cohere v3)")
    print("=" * 50)
    
    try:
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv(".env")
        
        # Check environment variables
        azure_api_key = os.getenv("AZURE_API_KEY")
        azure_endpoint = os.getenv("AZURE_EMBEDDINGS_ENDPOINT")
        
        print(f"🔑 Azure API Key: {'✅ Set' if azure_api_key else '❌ Missing'}")
        print(f"🌐 Azure Endpoint: {'✅ Set' if azure_endpoint else '❌ Missing'}")
        
        if not azure_api_key or not azure_endpoint:
            print("❌ Missing Azure credentials")
            return False
        
        # Test Azure embeddings directly
        print("\n🔧 Testing Azure AI Inference Embeddings...")
        from azure.ai.inference import EmbeddingsClient
        from azure.core.credentials import AzureKeyCredential
        
        client = EmbeddingsClient(
            endpoint=azure_endpoint,
            credential=AzureKeyCredential(azure_api_key)
        )
        
        # Test embedding
        test_texts = ["Hello world", "This is a test"]
        response = client.embed(
            input=test_texts,
            model="Cohere-embed-v3-english",
            input_type="document"
        )
        
        print(f"✅ Azure embeddings working!")
        print(f"📊 Model: Cohere-embed-v3-english")
        print(f"📏 Dimension: {len(response.data[0].embedding)}")
        print(f"📝 Test texts: {len(test_texts)}")
        print(f"🎯 Embeddings generated: {len(response.data)}")
        
        # Test with our embedder class
        print("\n🔧 Testing our AzureEmbedder class...")
        from ingestion.embedder import AzureEmbedder
        
        embedder = AzureEmbedder(
            model_name="Cohere-embed-v3-english",
            api_key=azure_api_key,
            endpoint=azure_endpoint
        )
        
        embeddings = embedder.embed_texts(test_texts)
        dimension = embedder.get_dimension()
        
        print(f"✅ AzureEmbedder working!")
        print(f"📏 Dimension: {dimension}")
        print(f"🎯 Embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_azure_embeddings()
    if success:
        print("\n🎉 Azure embeddings test passed!")
    else:
        print("\n💥 Azure embeddings test failed!")
        sys.exit(1) 