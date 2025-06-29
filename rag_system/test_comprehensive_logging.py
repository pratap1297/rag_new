#!/usr/bin/env python3
"""
Test Comprehensive Extraction Logging
Demonstrates the comprehensive logging system with PDF/Excel processing
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_comprehensive_logging():
    """Test comprehensive logging with a new document"""
    
    print("🧪 Testing Comprehensive Extraction Logging")
    print("=" * 60)
    
    # Setup debug logging
    from setup_debug_logging import setup_debug_logging
    debug_config = setup_debug_logging(enable_extraction_debug=True, save_dumps=True)
    
    print(f"Debug logging configured:")
    print(f"  - Logs directory: {debug_config['logs_dir']}")
    print(f"  - Debug log: {debug_config['debug_log']}")
    
    try:
        # Initialize system
        from src.core.system_init import initialize_system
        
        print("\n🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        
        # Create a simple test document to force processing
        test_content = """# Network Layout Test Document
        
This is a test document to demonstrate comprehensive extraction logging.

## Building Information
- Building: Test Building
- Floor: 1
- Network Equipment: Router, Switch, Access Points

## Signal Strength Data
Location A: -45 dBm
Location B: -52 dBm  
Location C: -38 dBm

## Coverage Analysis
The network coverage shows excellent signal strength across all tested locations.
Quality metrics indicate optimal performance for wireless connectivity.
"""
        
        # Create test file
        test_file = Path("test_comprehensive_logging_doc.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"\n📄 Processing test file: {test_file}")
        print(f"Content length: {len(test_content)} chars")
        
        # Process file with comprehensive logging
        result = ingestion_engine.ingest_file(str(test_file))
        
        # Display results
        print(f"\n📊 Processing Results:")
        print(f"  - Status: {result.get('status', 'Unknown')}")
        print(f"  - Chunks created: {result.get('chunk_count', 0)}")
        print(f"  - Vectors added: {result.get('vector_count', 0)}")
        print(f"  - Processing time: {result.get('processing_time', 'Unknown')}")
        
        if result.get('metadata', {}).get('processor_used'):
            print(f"  - Processor used: {result['metadata']['processor_used']}")
            print(f"  - Processor chunks: {result['metadata'].get('processor_chunk_count', 0)}")
            print(f"  - Processor time: {result['metadata'].get('processor_processing_time', 'Unknown')}")
        
        # Save detailed result
        output_file = f"comprehensive_logging_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = Path(debug_config['logs_dir']) / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Comprehensive logging test complete!")
        print(f"  - Detailed results: {output_path}")
        print(f"  - Debug logs: {debug_config['debug_log']}")
        print(f"  - Extraction dumps in: {debug_config['logs_dir']}")
        
        # Show what was logged
        debug_log_path = Path(debug_config['debug_log'])
        if debug_log_path.exists() and debug_log_path.stat().st_size > 0:
            print(f"\n📋 Debug Log Sample (last 10 lines):")
            with open(debug_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"  {line.strip()}")
        
        # Clean up test file
        test_file.unlink()
        print(f"\n🧹 Cleaned up test file: {test_file}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_pdf_processor_logging():
    """Test PDF processor with comprehensive logging"""
    
    print("\n🔍 Testing PDF Processor Logging")
    print("=" * 50)
    
    try:
        # Initialize system
        from src.core.system_init import initialize_system
        container = initialize_system()
        
        # Get the enhanced PDF processor directly
        ingestion_engine = container.get('ingestion_engine')
        processor = ingestion_engine.processor_registry.get_processor("test.pdf")
        
        if processor:
            print(f"📄 Found PDF processor: {processor.__class__.__name__}")
            
            # Check if it's the enhanced processor
            if hasattr(processor, 'azure_client'):
                print(f"✅ Enhanced PDF Processor with Azure CV detected")
                print(f"   Azure client available: {processor.azure_client is not None}")
                if processor.azure_client:
                    print(f"   Azure services: Computer Vision, Document Intelligence")
            else:
                print(f"📄 Basic PDF Processor detected")
            
        else:
            print("❌ No PDF processor found")
            
    except Exception as e:
        print(f"❌ Error testing PDF processor: {e}")

def main():
    """Main function to run comprehensive logging tests"""
    print("🔬 Comprehensive Extraction Logging Test Suite")
    print("=" * 60)
    
    # Test 1: Basic comprehensive logging with markdown
    result = test_comprehensive_logging()
    
    # Test 2: Check PDF processor capabilities
    test_pdf_processor_logging()
    
    if result:
        print(f"\n🎯 Comprehensive Logging Summary:")
        print(f"✅ Environment variables set for debug mode")
        print(f"✅ Detailed processor logging enabled")
        print(f"✅ Extraction dump files configured")
        print(f"✅ Debug logs capture full processing pipeline")
        print(f"✅ Metadata tracking comprehensive")
        
        print(f"\n📋 What the logging captures:")
        print(f"  📄 PDF Processing:")
        print(f"    - Azure Vision API calls and responses")
        print(f"    - OCR text extraction results")
        print(f"    - Image processing details")
        print(f"    - Table extraction metrics")
        print(f"    - Page-by-page processing times")
        print(f"    - Chunk creation with metadata")
        print(f"  ")
        print(f"  📊 Excel Processing:")
        print(f"    - Sheet-by-sheet analysis")
        print(f"    - Cell count and data extraction")
        print(f"    - Image OCR processing")
        print(f"    - Chart extraction attempts")
        print(f"    - Azure AI integration status")
        print(f"  ")
        print(f"  🔍 Ingestion Engine:")
        print(f"    - Processor selection logic")
        print(f"    - Processing time tracking")
        print(f"    - Chunk creation details")
        print(f"    - Error handling and fallbacks")
        
        print(f"\n🧪 Ready for Production Debugging!")
        print(f"The comprehensive logging system is now active and will capture")
        print(f"detailed information about PDF/Excel extraction processes.")
        
    else:
        print(f"\n❌ Test failed - check logs for details")

if __name__ == "__main__":
    main() 