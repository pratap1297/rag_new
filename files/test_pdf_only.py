#!/usr/bin/env python3
"""
Test PDF Processing Only
"""
import requests
import time
import os

API_BASE_URL = "http://localhost:8000"

def test_pdf_upload():
    """Test PDF file upload specifically"""
    print("🔍 Testing PDF upload...")
    
    pdf_file = "test_documents/employee_handbook.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        return False
    
    print(f"📄 Found PDF file: {pdf_file} ({os.path.getsize(pdf_file)} bytes)")
    
    try:
        # Test with a very long timeout
        print("📤 Uploading PDF (this may take a while)...")
        
        with open(pdf_file, 'rb') as f:
            files = {'file': ('employee_handbook.pdf', f, 'application/pdf')}
            data = {'metadata': '{"source": "test", "type": "handbook"}'}
            
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                timeout=600  # 10 minute timeout
            )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ PDF upload successful!")
            print(f"   Chunks created: {result.get('chunks_created', 'unknown')}")
            return True
        else:
            print(f"❌ PDF upload failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ PDF upload timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ PDF upload error: {e}")
        return False

def test_api_health():
    """Test if API is responsive"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🚀 Testing PDF Processing")
    print("=" * 50)
    
    # Check API health first
    if not test_api_health():
        print("❌ API is not responding. Please restart the server.")
        exit(1)
    
    print("✅ API is healthy")
    
    # Test PDF upload
    success = test_pdf_upload()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PDF test completed successfully!")
    else:
        print("❌ PDF test failed!") 