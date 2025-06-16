#!/usr/bin/env python3
"""
Detailed PDF Content Analysis
Test what content was actually extracted from the PDF
"""

import sys
import os
import requests
import json
from pathlib import Path

def analyze_pdf_content():
    """Analyze what content was actually extracted from the PDF"""
    
    print("🔍 Detailed PDF Content Analysis")
    print("=" * 50)
    
    pdf_path = r"C:\Users\jaideepvm\Downloads\USAMReport-21-40-1-5.pdf"
    
    # Step 1: Check PDF file
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"📄 PDF File: {Path(pdf_path).name}")
    print(f"📊 Size: {file_size:.2f} MB")
    
    # Step 2: Check what documents are in the system
    print("\n📚 Checking Documents in RAG System...")
    documents = get_system_documents()
    
    if documents:
        print(f"✅ Found {len(documents)} documents in system")
        
        # Look for our PDF
        pdf_docs = [doc for doc in documents if 'USAMReport' in str(doc) or 'pdf' in str(doc).lower()]
        if pdf_docs:
            print(f"📄 Found PDF-related documents: {len(pdf_docs)}")
            for i, doc in enumerate(pdf_docs[:3], 1):
                print(f"   {i}. {doc}")
        else:
            print("⚠️ No PDF documents found in system")
    else:
        print("❌ Could not retrieve documents from system")
    
    # Step 3: Test specific PDF queries
    print("\n🔍 Testing PDF-Specific Queries...")
    
    # Very specific queries about the PDF
    specific_queries = [
        "USAMReport-21-40-1-5.pdf",
        "USAM report content",
        "What is in the PDF file I just uploaded?",
        "Show me the latest document that was uploaded",
        "What content was extracted from the PDF?"
    ]
    
    for query in specific_queries:
        print(f"\n🔍 Query: '{query}'")
        result = query_with_sources(query)
        
        if result:
            response = result.get('response', '')
            sources = result.get('sources', [])
            
            print(f"📝 Response: {response[:150]}...")
            print(f"📚 Sources found: {len(sources)}")
            
            for i, source in enumerate(sources[:2], 1):
                source_info = f"Source {i}: "
                if isinstance(source, dict):
                    source_info += f"{source.get('title', 'N/A')} | "
                    source_info += f"Score: {source.get('relevance_score', source.get('score', 'N/A'))}"
                    if 'excerpt' in source:
                        source_info += f" | Excerpt: {source['excerpt'][:100]}..."
                else:
                    source_info += str(source)[:100]
                print(f"   {source_info}")
        else:
            print("❌ Query failed")
    
    # Step 4: Test direct content extraction
    print("\n🔧 Testing Direct PDF Processing...")
    test_direct_pdf_processing(pdf_path)

def get_system_documents():
    """Get list of documents in the system"""
    try:
        response = requests.get('http://localhost:8000/manage/documents', timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get documents: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
        return None

def query_with_sources(query):
    """Query the system and return response with sources"""
    try:
        response = requests.post(
            'http://localhost:8000/query',
            json={"query": query, "max_results": 5},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Query failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None

def test_direct_pdf_processing(pdf_path):
    """Test direct PDF processing to see what can be extracted"""
    try:
        # Try to use PyPDF2 or similar to see what's in the PDF
        try:
            import PyPDF2
            print("✅ PyPDF2 available - testing direct extraction")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                print(f"📄 PDF has {num_pages} pages")
                
                # Extract text from first few pages
                for i in range(min(3, num_pages)):
                    page = pdf_reader.pages[i]
                    text = page.extract_text()
                    print(f"\n📄 Page {i+1} content preview:")
                    print(f"   Length: {len(text)} characters")
                    if text.strip():
                        print(f"   Preview: {text[:200]}...")
                    else:
                        print("   ⚠️ No text extracted from this page")
                        
        except ImportError:
            print("⚠️ PyPDF2 not available - trying alternative methods")
            
            # Try pdfplumber if available
            try:
                import pdfplumber
                print("✅ pdfplumber available - testing extraction")
                
                with pdfplumber.open(pdf_path) as pdf:
                    print(f"📄 PDF has {len(pdf.pages)} pages")
                    
                    for i, page in enumerate(pdf.pages[:3]):
                        text = page.extract_text()
                        print(f"\n📄 Page {i+1} content preview:")
                        print(f"   Length: {len(text) if text else 0} characters")
                        if text and text.strip():
                            print(f"   Preview: {text[:200]}...")
                        else:
                            print("   ⚠️ No text extracted from this page")
                            
            except ImportError:
                print("⚠️ pdfplumber not available")
                print("💡 Consider installing: pip install PyPDF2 pdfplumber")
                
    except Exception as e:
        print(f"❌ Error in direct PDF processing: {e}")

def test_vector_search():
    """Test vector search to see what's actually stored"""
    print("\n🔍 Testing Vector Search...")
    
    try:
        # Try to get vector information
        response = requests.get('http://localhost:8000/manage/vectors', params={'limit': 10}, timeout=10)
        
        if response.status_code == 200:
            vectors = response.json()
            print(f"✅ Found {len(vectors)} vectors in system")
            
            # Look for recent vectors (likely our PDF)
            for i, vector in enumerate(vectors[:5], 1):
                if isinstance(vector, dict):
                    print(f"   Vector {i}: ID={vector.get('vector_id', 'N/A')}")
                    metadata = vector.get('metadata', {})
                    if metadata:
                        print(f"      Title: {metadata.get('title', 'N/A')}")
                        print(f"      Source: {metadata.get('source', 'N/A')}")
                        print(f"      Type: {metadata.get('document_type', 'N/A')}")
                else:
                    print(f"   Vector {i}: {str(vector)[:100]}")
        else:
            print(f"❌ Failed to get vectors: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting vectors: {e}")

if __name__ == "__main__":
    analyze_pdf_content()
    test_vector_search() 