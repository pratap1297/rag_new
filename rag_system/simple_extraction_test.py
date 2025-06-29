#!/usr/bin/env python3
"""
Simple test to upload a file and check for extraction dumps
"""

import os
import requests
import json
import tempfile
from pathlib import Path
import time

def setup_debug_environment():
    """Setup debug environment"""
    os.environ['RAG_SAVE_EXTRACTION_DUMPS'] = 'true'
    print("✅ Set RAG_SAVE_EXTRACTION_DUMPS=true")

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

def test_file_upload():
    """Test file upload through API"""
    try:
        # Setup
        setup_debug_environment()
        test_file, expected_content = create_test_file()
        
        # Clear existing debug files
        debug_dir = Path("data/logs")
        if debug_dir.exists():
            for debug_file in debug_dir.glob("debug_*extraction*.json"):
                debug_file.unlink()
            print("🧹 Cleared existing debug files")
        
        # Upload file through API
        api_url = "http://localhost:8000/upload"
        
        print(f"\n📁 Uploading file through API: {test_file}")
        
        with open(test_file, 'rb') as f:
            files = {'file': (Path(test_file).name, f, 'text/markdown')}
            response = requests.post(api_url, files=files)
        
        print(f"📤 Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful:")
            print(f"   Status: {result.get('status')}")
            print(f"   File ID: {result.get('file_id')}")
            print(f"   Chunks: {result.get('chunks_created', 0)}")
            print(f"   Vectors: {result.get('vectors_stored', 0)}")
        else:
            print(f"❌ Upload failed: {response.text}")
            return False
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Check for debug files
        debug_files = list(debug_dir.glob("debug_*extraction*.json"))
        
        if debug_files:
            print(f"\n📄 Found {len(debug_files)} debug extraction files:")
            for debug_file in debug_files:
                print(f"   - {debug_file.name}")
                
                # Read and display content
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
                    
                # Show actual extracted text if available
                if 'extracted_text' in debug_data:
                    extracted_text = debug_data['extracted_text']
                    print(f"     • Full text length: {len(extracted_text)}")
                    print(f"     • Full text sample: {extracted_text[:200]}...")
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

def check_api_server():
    """Check if API server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API server is not running: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing extraction dumps via API upload...\n")
    
    # Check if API server is running
    if not check_api_server():
        print("\n💥 API server is not running. Please start it first with:")
        print("   python src/main_managed.py")
        exit(1)
    
    success = test_file_upload()
    
    if success:
        print("\n🎉 Test completed successfully! Extraction dumps are working.")
    else:
        print("\n💥 Test failed. Check the error messages above.") 