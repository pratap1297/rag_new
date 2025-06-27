#!/usr/bin/env python3
"""
Test Azure Vision API PDF Extraction
Tests Azure Computer Vision with the BuildingA/B/C network layout PDFs
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_azure_pdf_extraction():
    """Test Azure Vision API with PDF files"""
    print("🧪 Testing Azure Vision API PDF Extraction")
    print("=" * 50)
    
    # Load configuration
    config_path = Path("../data/config/system_config.json")
    if not config_path.exists():
        config_path = Path("data/config/system_config.json")
    
    if not config_path.exists():
        print("❌ Configuration file not found!")
        return
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    azure_config = config.get('azure_ai', {})
    
    # Check if Azure is configured
    if not azure_config.get('computer_vision_endpoint') or not azure_config.get('computer_vision_key'):
        print("❌ Azure Vision API not configured")
        print("Please run: python configure_azure_vision.py")
        return
    
    # Test with BuildingA PDF
    test_pdf = Path("test_documents/BuildingA_Network_Layout.pdf")
    if not test_pdf.exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        print("Available test files:")
        for pdf in Path("test_documents").glob("*.pdf"):
            print(f"   📄 {pdf.name}")
        return
    
    print(f"📄 Testing with: {test_pdf.name}")
    
    try:
        # Test with enhanced PDF processor
        from src.ingestion.processors.enhanced_pdf_processor import EnhancedPDFProcessor
        from src.integrations.azure_ai.azure_client import AzureAIClient
        
        # Create Azure client
        azure_client = AzureAIClient(azure_config)
        
        if not azure_client.is_available():
            print("❌ Azure client not available")
            return
        
        print("✅ Azure client initialized")
        
        # Create enhanced PDF processor
        processor = EnhancedPDFProcessor(config=config, azure_client=azure_client)
        print("✅ Enhanced PDF processor created")
        
        # Process the PDF
        print("🔄 Processing PDF with Azure Vision...")
        result = processor.process(str(test_pdf))
        
        if result['status'] == 'success':
            print("✅ PDF processed successfully!")
            print(f"📊 Results:")
            print(f"   Pages processed: {len(result['pages'])}")
            print(f"   Chunks created: {len(result['chunks'])}")
            print(f"   Images found: {len(result.get('images', []))}")
            print(f"   Tables found: {len(result.get('tables', []))}")
            
            # Show first page content
            if result['pages']:
                first_page = result['pages'][0]
                print(f"\n📖 First page content preview:")
                text_preview = first_page['text'][:300] + "..." if len(first_page['text']) > 300 else first_page['text']
                print(f"   {text_preview}")
                
                if first_page['images']:
                    print(f"   🖼️  Images with OCR: {len(first_page['images'])}")
                    for img in first_page['images']:
                        if img.get('ocr_text'):
                            print(f"      Image {img['image_index']}: {img['ocr_text'][:100]}...")
            
            # Show first chunk
            if result['chunks']:
                first_chunk = result['chunks'][0]
                print(f"\n📝 First chunk preview:")
                chunk_preview = first_chunk['text'][:300] + "..." if len(first_chunk['text']) > 300 else first_chunk['text']
                print(f"   {chunk_preview}")
        else:
            print("❌ PDF processing failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure Azure packages are installed:")
        print("   pip install azure-cognitiveservices-vision-computervision")
        print("   pip install azure-ai-formrecognizer")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_basic_azure_connection():
    """Test basic Azure connection without PDF processing"""
    print("\n🔗 Testing Basic Azure Connection...")
    
    try:
        from src.integrations.azure_ai.azure_client import AzureAIClient
        
        # Load config
        config_path = Path("../data/config/system_config.json")
        if not config_path.exists():
            config_path = Path("data/config/system_config.json")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        azure_config = config.get('azure_ai', {})
        
        # Create client
        client = AzureAIClient(azure_config)
        
        if client.is_available():
            print("✅ Azure Computer Vision client available")
            
            # Get service info
            info = client.get_service_info()
            print("📊 Service Status:")
            print(f"   Computer Vision: {'✅' if info['computer_vision']['available'] else '❌'}")
            print(f"   Document Intelligence: {'✅' if info['document_intelligence']['available'] else '❌'}")
            print(f"   Endpoint: {info['computer_vision']['endpoint']}")
            
        else:
            print("❌ Azure client not available")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

def main():
    """Main function"""
    print("Azure Vision PDF Extraction Test")
    print()
    
    # Test basic connection first
    test_basic_azure_connection()
    
    print()
    
    # Test PDF extraction
    test_azure_pdf_extraction()

if __name__ == "__main__":
    main() 