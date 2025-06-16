#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Unified Document Processors
Demonstrates the new processor architecture with all document types
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the unified processors
from rag_system.src.ingestion.processors import (
    create_processor_registry,
    get_processor_for_file,
    list_supported_extensions,
    get_processor_capabilities,
    AVAILABLE_PROCESSORS
)

def load_config():
    """Load configuration from environment"""
    load_dotenv('rag_system/.env')
    
    return {
        # Azure Computer Vision
        'COMPUTER_VISION_ENDPOINT': os.getenv('COMPUTER_VISION_ENDPOINT'),
        'COMPUTER_VISION_KEY': os.getenv('COMPUTER_VISION_KEY'),
        
        # ServiceNow
        'SERVICENOW_INSTANCE_URL': os.getenv('SERVICENOW_INSTANCE_URL'),
        'SERVICENOW_USERNAME': os.getenv('SERVICENOW_USERNAME'),
        'SERVICENOW_PASSWORD': os.getenv('SERVICENOW_PASSWORD'),
        'SERVICENOW_TABLE': 'incident',
        
        # Processing settings
        'use_azure_cv': True,
        'extract_images': True,
        'extract_tables': True,
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'confidence_threshold': 0.7
    }

def test_processor_capabilities():
    """Test processor capabilities and supported extensions"""
    print("=" * 80)
    print("UNIFIED DOCUMENT PROCESSOR ARCHITECTURE")
    print("=" * 80)
    
    # Show available processors
    print(f"\nAvailable Processors ({len(AVAILABLE_PROCESSORS)}):")
    for name, processor_class in AVAILABLE_PROCESSORS.items():
        print(f"  • {name.upper()}: {processor_class.__name__}")
    
    # Show supported extensions
    print(f"\nSupported File Extensions:")
    extensions = list_supported_extensions()
    for processor_name, exts in extensions.items():
        print(f"  • {processor_name.upper()}: {', '.join(exts)}")

def test_processor_selection():
    """Test automatic processor selection"""
    print(f"\nAutomatic Processor Selection:")
    
    config = load_config()
    
    test_files = [
        'document.pdf',
        'spreadsheet.xlsx', 
        'report.docx',
        'image.png',
        'data.txt',
        'code.py',
        'config.json',
        'servicenow'
    ]
    
    for file_path in test_files:
        processor = get_processor_for_file(file_path, config)
        if processor:
            print(f"  • {file_path:<15} -> {processor.__class__.__name__}")
        else:
            print(f"  • {file_path:<15} -> No processor found")

def test_excel_processor():
    """Test Excel processor with existing file"""
    print(f"\nTesting Excel Processor:")
    
    excel_file = "Facility_Managers_2024.xlsx"
    if not os.path.exists(excel_file):
        print(f"  Excel file not found: {excel_file}")
        return
    
    config = load_config()
    processor = get_processor_for_file(excel_file, config)
    
    if processor:
        print(f"  Processor: {processor.__class__.__name__}")
        try:
            result = processor.process(excel_file)
            print(f"  Status: {result['status']}")
            print(f"  Sheets: {len(result.get('sheets', []))}")
            print(f"  Chunks: {len(result.get('chunks', []))}")
            
            if result.get('chunks'):
                first_chunk = result['chunks'][0]
                print(f"  First chunk preview: {first_chunk['text'][:100]}...")
                
        except Exception as e:
            print(f"  Processing failed: {e}")
    else:
        print(f"  No processor found for {excel_file}")

def test_text_processor():
    """Test text processor with a simple file"""
    print(f"\nTesting Text Processor:")
    
    # Create a test text file
    test_file = "test_document.txt"
    test_content = """This is a test document for the unified processor architecture.

The new system supports multiple document types:
- PDF files with Azure Computer Vision
- Excel spreadsheets with embedded objects
- Word documents with tables
- Images with OCR
- ServiceNow tickets
- Plain text files

Each processor follows the same interface but provides specialized extraction capabilities."""
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        config = load_config()
        processor = get_processor_for_file(test_file, config)
        
        if processor:
            print(f"  Processor: {processor.__class__.__name__}")
            
            result = processor.process(test_file)
            print(f"  Status: {result['status']}")
            print(f"  Characters: {result['metadata'].get('char_count', 0)}")
            print(f"  Words: {result['metadata'].get('word_count', 0)}")
            print(f"  Chunks: {len(result.get('chunks', []))}")
            print(f"  Language: {result['metadata'].get('language', 'unknown')}")
            print(f"  Content type: {result['metadata'].get('content_type', 'unknown')}")
            
        # Clean up
        os.remove(test_file)
        
    except Exception as e:
        print(f"  Processing failed: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)

def test_registry_functionality():
    """Test processor registry functionality"""
    print(f"\nTesting Processor Registry:")
    
    config = load_config()
    registry = create_processor_registry(config)
    
    print(f"  Registered processors: {len(registry.list_processors())}")
    for processor_name in registry.list_processors():
        print(f"    • {processor_name}")
    
    # Test file type detection
    test_cases = [
        ("document.pdf", "PDFProcessor"),
        ("data.xlsx", "ExcelProcessor"),
        ("report.docx", "WordProcessor"),
        ("photo.jpg", "ImageProcessor"),
        ("notes.txt", "TextProcessor"),
        ("unknown.xyz", None)
    ]
    
    print(f"\n  File type detection:")
    for file_path, expected in test_cases:
        processor = registry.get_processor(file_path)
        actual = processor.__class__.__name__ if processor else None
        status = "✓" if actual == expected else "✗"
        print(f"    {status} {file_path:<15} -> {actual or 'None'}")

def main():
    """Main test function"""
    try:
        # Test basic capabilities
        test_processor_capabilities()
        test_processor_selection()
        test_registry_functionality()
        
        # Test specific processors
        test_excel_processor()
        test_text_processor()
        
        print(f"\n" + "=" * 80)
        print("UNIFIED PROCESSOR ARCHITECTURE TESTING COMPLETE")
        print("=" * 80)
        
        print(f"\nSummary:")
        print(f"  • {len(AVAILABLE_PROCESSORS)} processors available")
        print(f"  • Supports multiple file types with unified interface")
        print(f"  • Azure Computer Vision integration")
        print(f"  • ServiceNow API integration")
        print(f"  • Automatic processor selection")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 