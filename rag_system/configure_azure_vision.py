#!/usr/bin/env python3
"""
Azure Vision API Configuration Script
Helps configure Azure Computer Vision and Document Intelligence credentials
"""
import json
import os
from pathlib import Path

def update_azure_config():
    """Update Azure AI configuration with user credentials"""
    print("🔧 Azure Vision API Configuration")
    print("=" * 50)
    print()
    
    # Get configuration file path
    config_path = Path("../data/config/system_config.json")
    if not config_path.exists():
        config_path = Path("data/config/system_config.json")
    
    if not config_path.exists():
        print("❌ Configuration file not found!")
        print("Please run this script from the rag_system directory")
        return
    
    # Load current configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("Please provide your Azure Vision API credentials:")
    print("(You can find these in your Azure portal under your Cognitive Services resource)")
    print()
    
    # Get Computer Vision credentials
    print("📍 Computer Vision Service:")
    cv_endpoint = input("Enter Computer Vision Endpoint: ").strip()
    cv_key = input("Enter Computer Vision Key: ").strip()
    
    print()
    
    # Get Document Intelligence credentials (optional)
    print("📄 Document Intelligence Service (optional - for advanced PDF processing):")
    use_di = input("Do you have Document Intelligence? (y/n): ").strip().lower()
    
    di_endpoint = ""
    di_key = ""
    enable_di = False
    
    if use_di in ['y', 'yes']:
        di_endpoint = input("Enter Document Intelligence Endpoint: ").strip()
        di_key = input("Enter Document Intelligence Key: ").strip()
        enable_di = True
    
    # Update configuration
    if cv_endpoint and cv_key:
        config['azure_ai']['computer_vision_endpoint'] = cv_endpoint
        config['azure_ai']['computer_vision_key'] = cv_key
        
        if enable_di and di_endpoint and di_key:
            config['azure_ai']['document_intelligence_endpoint'] = di_endpoint
            config['azure_ai']['document_intelligence_key'] = di_key
            config['azure_ai']['enable_document_intelligence'] = True
        else:
            config['azure_ai']['enable_document_intelligence'] = False
        
        # Save configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print()
        print("✅ Azure Vision API configuration updated successfully!")
        print()
        print("🔄 Your PDF files will now be processed with Azure Vision API")
        print("📋 Benefits:")
        print("   • Extract text from scanned PDFs and images")
        print("   • Process handwritten content")
        print("   • Better accuracy for complex layouts")
        print("   • Table and form extraction")
        print()
        print("🚀 Restart your RAG system to apply the changes")
        
    else:
        print("❌ Computer Vision credentials are required!")
        print("Please provide both endpoint and key")

def test_azure_connection():
    """Test Azure Vision API connection"""
    print("\n🧪 Testing Azure Vision API Connection...")
    
    try:
        # Load configuration
        config_path = Path("../data/config/system_config.json")
        if not config_path.exists():
            config_path = Path("data/config/system_config.json")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        azure_config = config.get('azure_ai', {})
        
        if not azure_config.get('computer_vision_endpoint') or not azure_config.get('computer_vision_key'):
            print("❌ Azure Vision API not configured")
            return
        
        # Test connection
        from src.integrations.azure_ai.azure_client import AzureAIClient
        
        client = AzureAIClient(azure_config)
        
        if client.is_available():
            print("✅ Azure Vision API connection successful!")
            
            # Get service info
            info = client.get_service_info()
            print("\n📊 Service Information:")
            print(f"   Computer Vision: {'✅ Available' if info['computer_vision']['available'] else '❌ Not available'}")
            print(f"   Document Intelligence: {'✅ Available' if info['document_intelligence']['available'] else '❌ Not available'}")
            print(f"   Max Image Size: {info['settings']['max_image_size_mb']}MB")
            print(f"   OCR Language: {info['settings']['ocr_language']}")
            
        else:
            print("❌ Azure Vision API connection failed")
            print("Please check your credentials and network connection")
        
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        print("Make sure you've installed the required Azure packages")

def main():
    """Main function"""
    print("Welcome to Azure Vision API Configuration!")
    print()
    
    choice = input("Choose an option:\n1. Configure Azure credentials\n2. Test connection\n3. Both\n\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        update_azure_config()
    
    if choice in ['2', '3']:
        test_azure_connection()

if __name__ == "__main__":
    main() 