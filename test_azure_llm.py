#!/usr/bin/env python3
"""
Test Azure LLM Client
Simple test to verify Azure LLM configuration
"""
import os
import sys
from pathlib import Path

# Add rag_system/src to path
sys.path.insert(0, str(Path("rag_system/src")))

# Set environment variables
os.environ.setdefault('AZURE_API_KEY', '6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr')
os.environ.setdefault('AZURE_CHAT_ENDPOINT', 'https://azurehub1910875317.services.ai.azure.com/models')

def test_azure_llm():
    """Test Azure LLM client directly"""
    print("🧪 Testing Azure LLM Client")
    print("=" * 50)
    
    try:
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv("rag_system/.env")
        
        # Check environment variables
        azure_api_key = os.getenv("AZURE_API_KEY")
        azure_endpoint = os.getenv("AZURE_CHAT_ENDPOINT")
        
        print(f"🔑 Azure API Key: {'✅ Set' if azure_api_key else '❌ Missing'}")
        print(f"🌐 Azure Endpoint: {'✅ Set' if azure_endpoint else '❌ Missing'}")
        
        if not azure_api_key or not azure_endpoint:
            print("❌ Azure credentials not properly configured")
            return False
        
        # Test Azure LLM client
        from retrieval.llm_client import LLMClient
        
        print("\n🤖 Creating Azure LLM Client...")
        llm_client = LLMClient(
            provider="azure",
            model_name="Llama-4-Maverick-17B-128E-Instruct-FP8",
            api_key=azure_api_key,
            endpoint=azure_endpoint,
            temperature=0.1,
            max_tokens=100
        )
        print("✅ Azure LLM Client created successfully")
        
        # Test connection
        print("\n🔗 Testing connection...")
        test_prompt = "Hello, this is a test. Please respond with 'Azure LLM is working'."
        
        response = llm_client.generate(test_prompt, max_tokens=50)
        print(f"✅ Response received: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_azure_llm()
    sys.exit(0 if success else 1) 