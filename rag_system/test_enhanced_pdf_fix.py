#!/usr/bin/env python3
"""
Test script to verify Enhanced PDF Processor fix
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_enhanced_pdf_processor():
    """Test that Enhanced PDF Processor is created when Azure config is available"""
    print("🧪 Testing Enhanced PDF Processor Fix")
    print("=" * 50)
    
    try:
        # Import the PDF processor factory
        from ingestion.processors.pdf_processor import create_pdf_processor
        
        # Create a test config with Azure AI configuration
        test_config = {
            'azure_ai': {
                'computer_vision_endpoint': 'https://computervision1298.cognitiveservices.azure.com/',
                'computer_vision_key': 'test-key-12345'
            },
            'max_file_size_mb': 50,
            'supported_formats': ['.pdf']
        }
        
        print("📋 Test config created with Azure AI settings")
        print(f"   Azure CV endpoint: {test_config['azure_ai']['computer_vision_endpoint']}")
        print(f"   Azure CV key: {test_config['azure_ai']['computer_vision_key'][:10]}...")
        
        # Create PDF processor
        print("\n🔧 Creating PDF processor...")
        processor = create_pdf_processor(config=test_config)
        
        # Check the processor type
        processor_type = processor.__class__.__name__
        print(f"✅ Created processor: {processor_type}")
        
        # Check if it has Azure client
        if hasattr(processor, 'azure_client'):
            print(f"✅ Processor has Azure client: {processor.azure_client is not None}")
            if processor.azure_client:
                print(f"   Azure client type: {processor.azure_client.__class__.__name__}")
        else:
            print("❌ Processor does not have Azure client")
        
        # Check supported extensions
        if hasattr(processor, 'supported_extensions'):
            print(f"✅ Supported extensions: {processor.supported_extensions}")
        
        # Test can_process method
        can_process_pdf = processor.can_process("test.pdf")
        print(f"✅ Can process PDF: {can_process_pdf}")
        
        # Determine success
        if processor_type == "EnhancedPDFProcessor" and hasattr(processor, 'azure_client'):
            print("\n🎉 SUCCESS: Enhanced PDF Processor with Azure client created!")
            return True
        elif processor_type == "PDFProcessor":
            print("\n⚠️  PARTIAL SUCCESS: Basic PDF Processor created (Azure client creation might have failed)")
            return False
        else:
            print(f"\n❌ UNEXPECTED: Unknown processor type: {processor_type}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_without_azure_config():
    """Test that basic PDF processor is created when no Azure config"""
    print("\n🧪 Testing without Azure config")
    print("-" * 30)
    
    try:
        from ingestion.processors.pdf_processor import create_pdf_processor
        
        # Create config without Azure AI
        basic_config = {
            'max_file_size_mb': 50,
            'supported_formats': ['.pdf']
        }
        
        processor = create_pdf_processor(config=basic_config)
        processor_type = processor.__class__.__name__
        
        print(f"✅ Created processor: {processor_type}")
        
        if processor_type == "PDFProcessor":
            print("✅ SUCCESS: Basic PDF Processor created when no Azure config")
            return True
        else:
            print(f"❌ UNEXPECTED: Expected PDFProcessor, got {processor_type}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Enhanced PDF Processor Fix Verification")
    print("=" * 60)
    
    # Test 1: With Azure config
    success1 = test_enhanced_pdf_processor()
    
    # Test 2: Without Azure config  
    success2 = test_without_azure_config()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   Test 1 (With Azure): {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Test 2 (Without Azure): {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1:
        print("\n🎉 Enhanced PDF Processor fix is working!")
        print("   The system will now use Azure Vision API for PDF text extraction.")
    else:
        print("\n⚠️  Enhanced PDF Processor fix needs more work.")
        print("   The system is still using basic PDF processing.") 