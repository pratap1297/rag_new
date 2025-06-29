#!/usr/bin/env python3
"""
Test script to verify extraction dumps are working with actual content
"""

import os
import sys
import tempfile
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def setup_debug_environment():
    """Setup debug environment"""
    os.environ['RAG_SAVE_EXTRACTION_DUMPS'] = 'true'
    
    # Configure logging to DEBUG level
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger().setLevel(logging.DEBUG)
    
    print("✅ Debug environment configured")

def create_test_file():
    """Create a test file with content"""
    test_content = """
# Test Document for Extraction Dumps

This is a test document to verify that extraction dumps are working correctly.

## Content Details
- This document contains multiple paragraphs
- It has headers and bullet points
- The content should be fully extracted and saved in debug dumps

## Test Data
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## End of Test Document
This is the end of the test document. The extraction should capture all of this content.
    """.strip()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    print(f"✅ Created test file: {temp_file}")
    print(f"   Content length: {len(test_content)} characters")
    return temp_file, test_content

def test_extraction_dumps():
    """Test the extraction dumps functionality"""
    try:
        # Setup
        setup_debug_environment()
        test_file, expected_content = create_test_file()
        
        # Import RAG system components
        from core.system_init import initialize_system
        
        print("\n🔧 Initializing RAG system...")
        container = initialize_system()
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        
        print(f"\n📁 Testing file ingestion: {test_file}")
        
        # Clear existing debug files
        debug_dir = Path("data/logs")
        if debug_dir.exists():
            for debug_file in debug_dir.glob("debug_*extraction*.json"):
                debug_file.unlink()
            print("🧹 Cleared existing debug files")
        
        # Ingest the test file
        result = ingestion_engine.ingest_file(test_file)
        
        print(f"\n✅ Ingestion completed:")
        print(f"   Status: {result.get('status')}")
        print(f"   Chunks created: {result.get('chunks_created', 0)}")
        print(f"   Vectors stored: {result.get('vectors_stored', 0)}")
        
        # Check for debug files
        debug_files = list(debug_dir.glob("debug_*extraction*.json"))
        
        if debug_files:
            print(f"\n📄 Found {len(debug_files)} debug extraction files:")
            for debug_file in debug_files:
                print(f"   - {debug_file.name}")
                
                # Read and display content
                import json
                with open(debug_file, 'r', encoding='utf-8') as f:
                    debug_data = json.load(f)
                
                print(f"     • Method: {debug_data.get('extraction_method', 'processor')}")
                print(f"     • Text length: {debug_data.get('extracted_text_length', 'N/A')}")
                print(f"     • Processing time: {debug_data.get('processing_time_seconds', 'N/A')}s")
                
                if 'extracted_text_preview' in debug_data:
                    preview = debug_data['extracted_text_preview']
                    print(f"     • Preview: {preview[:100]}...")
                
                if 'chunks_detail' in debug_data:
                    print(f"     • Chunks: {len(debug_data['chunks_detail'])}")
        else:
            print("\n❌ No debug extraction files found!")
            
        # Cleanup
        os.unlink(test_file)
        print(f"\n🧹 Cleaned up test file: {test_file}")
        
        return len(debug_files) > 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing extraction dumps functionality...\n")
    
    success = test_extraction_dumps()
    
    if success:
        print("\n🎉 Test completed successfully! Extraction dumps are working.")
    else:
        print("\n💥 Test failed. Check the error messages above.")
        sys.exit(1) 