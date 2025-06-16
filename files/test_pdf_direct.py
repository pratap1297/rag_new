#!/usr/bin/env python3
"""
Test PDF Processing Directly
"""
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.append('.')

def test_pdf_extraction():
    """Test PDF text extraction directly"""
    pdf_file = Path("test_documents/employee_handbook.pdf")
    
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_file}")
        return False
    
    print(f"📄 Testing PDF: {pdf_file} ({pdf_file.stat().st_size} bytes)")
    
    try:
        # Test PyPDF2 directly
        print("🔧 Testing PyPDF2 extraction...")
        import PyPDF2
        
        text = ""
        with open(pdf_file, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            print(f"📊 PDF has {len(reader.pages)} pages")
            
            for i, page in enumerate(reader.pages):
                print(f"   Processing page {i+1}...")
                page_text = page.extract_text()
                text += page_text + "\n"
                print(f"   Page {i+1}: {len(page_text)} characters")
        
        print(f"✅ Total extracted text: {len(text)} characters")
        print(f"📝 First 200 characters: {text[:200]}...")
        
        if len(text.strip()) == 0:
            print("⚠️  Warning: No text extracted from PDF")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ingestion_engine():
    """Test the ingestion engine directly"""
    try:
        print("🔧 Testing ingestion engine...")
        
        # Import the ingestion engine
        from src.core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        print("✅ Ingestion engine created")
        
        # Test PDF ingestion
        pdf_file = "test_documents/employee_handbook.pdf"
        print(f"📄 Testing ingestion of: {pdf_file}")
        
        result = ingestion_engine.ingest_file(pdf_file)
        print(f"✅ Ingestion result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ingestion engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing PDF Processing Directly")
    print("=" * 50)
    
    # Test 1: Direct PDF extraction
    print("\n📋 Test 1: Direct PDF Extraction")
    pdf_success = test_pdf_extraction()
    
    # Test 2: Ingestion engine
    print("\n📋 Test 2: Ingestion Engine")
    ingestion_success = test_ingestion_engine()
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    print(f"   PDF Extraction: {'✅ PASS' if pdf_success else '❌ FAIL'}")
    print(f"   Ingestion Engine: {'✅ PASS' if ingestion_success else '❌ FAIL'}")
    
    if pdf_success and ingestion_success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!") 