#!/usr/bin/env python3
"""
Test Enhanced Features
Tests file upload and directory processing functionality
"""
import requests
import json
import os
import tempfile
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_file_upload():
    """Test file upload functionality"""
    print("🔍 Testing File Upload...")
    
    # Create a test file
    test_content = """
# Test Document

This is a test document for the RAG system.

## Section 1
This section contains important information about network security.

## Section 2
This section discusses best practices for system administration.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        test_file_path = f.name
    
    try:
        # Prepare metadata
        metadata = {
            "title": "Test Document",
            "description": "A test document for upload functionality",
            "author": "Test System"
        }
        
        # Upload file
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/markdown')}
            data = {'metadata': json.dumps(metadata)}
            
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ File upload successful!")
            print(f"   Status: {result.get('status')}")
            print(f"   File ID: {result.get('file_id')}")
            print(f"   Chunks Created: {result.get('chunks_created', 0)}")
            print(f"   Embeddings Generated: {result.get('embeddings_generated', 0)}")
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def test_api_endpoints():
    """Test API endpoints availability"""
    print("\n🔍 Testing API Endpoints...")
    
    endpoints = [
        ("/health", "Health Check"),
        ("/stats", "System Statistics"),
        ("/manage/stats/detailed", "Detailed Statistics"),
        ("/manage/documents?limit=5", "Document List"),
        ("/manage/vectors?limit=5", "Vector List")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
            else:
                print(f"⚠️ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Error - {e}")

def test_enhanced_ui_import():
    """Test if enhanced UI can be imported"""
    print("\n🔍 Testing Enhanced UI Import...")
    
    try:
        import sys
        from pathlib import Path
        
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from src.api.gradio_ui_enhanced import create_enhanced_interface, RAGSystemUI
        
        print("✅ Enhanced UI import successful!")
        
        # Test UI class instantiation
        ui = RAGSystemUI(api_base_url=API_BASE_URL)
        print("✅ Enhanced UI class instantiation successful!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Enhanced UI import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Enhanced UI test error: {e}")
        return False

def test_directory_structure():
    """Test if all required files exist"""
    print("\n🔍 Testing Directory Structure...")
    
    required_files = [
        "src/api/gradio_ui_enhanced.py",
        "src/api/gradio_ui.py",
        "src/api/main.py",
        "src/api/management_api.py",
        "launch_ui.py",
        "launch_enhanced_ui.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: Found")
        else:
            print(f"❌ {file_path}: Missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🧪 Enhanced Features Test Suite")
    print("=" * 50)
    
    # Test directory structure
    structure_ok = test_directory_structure()
    
    # Test enhanced UI import
    ui_import_ok = test_enhanced_ui_import()
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test file upload (only if API is running)
    upload_ok = test_file_upload()
    
    print("\n📊 Test Summary:")
    print(f"   Directory Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"   Enhanced UI Import: {'✅ PASS' if ui_import_ok else '❌ FAIL'}")
    print(f"   File Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    
    if structure_ok and ui_import_ok:
        print("\n🎉 Enhanced features are ready to use!")
        print("\nTo start the enhanced UI:")
        print("   python launch_enhanced_ui.py")
        print("\nThen visit: http://localhost:7861")
    else:
        print("\n⚠️ Some issues detected. Check the output above.")

if __name__ == "__main__":
    main() 