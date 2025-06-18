#!/usr/bin/env python3
"""
Test Azure LLM Client
Simple test to verify Azure LLM configuration
"""
import os
import sys
from pathlib import Path

# Add src to path and set up proper imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

def test_azure_llm():
    """Test Azure LLM client directly"""
    print("🧪 Testing Azure LLM Client")
    print("=" * 50)
    
    try:
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv(".env")
        
        # Check environment variables
        azure_api_key = os.getenv("AZURE_API_KEY")
        azure_endpoint = os.getenv("AZURE_CHAT_ENDPOINT")
        
        print(f"🔑 Azure API Key: {'✅ Set' if azure_api_key else '❌ Missing'}")
        print(f"🌐 Azure Endpoint: {'✅ Set' if azure_endpoint else '❌ Missing'}")
        
        if not azure_api_key or not azure_endpoint:
            print("❌ Azure credentials not properly configured")
            return False
        
        # Test Azure client directly
        print("\n🤖 Testing Azure AI Inference directly...")
        
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.ai.inference.models import SystemMessage, UserMessage
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint=azure_endpoint,
                credential=AzureKeyCredential(azure_api_key),
                api_version="2024-05-01-preview"
            )
            
            response = client.complete(
                messages=[
                    SystemMessage(content="You are a helpful assistant."),
                    UserMessage(content="Hello, this is a test. Please respond with 'Azure LLM is working'.")
                ],
                max_tokens=50,
                temperature=0.1,
                model="Llama-4-Maverick-17B-128E-Instruct-FP8"
            )
            
            response_text = response.choices[0].message.content
            print(f"✅ Azure AI Inference Response: {response_text}")
            
            return True
            
        except Exception as e:
            print(f"❌ Azure AI Inference test failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_azure_llm()
    sys.exit(0 if success else 1)
