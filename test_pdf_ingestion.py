#!/usr/bin/env python3
"""
Test PDF Data Extraction and Ingestion
Complete workflow test: Extract PDF -> Process -> Ingest -> Query
"""

import sys
import os
import requests
import json
from pathlib import Path

def test_pdf_workflow():
    """Test complete PDF workflow: extract, process, ingest, query"""
    
    print("📄 Testing Complete PDF Workflow")
    print("=" * 50)
    
    # PDF file path
    pdf_path = r"C:\Users\jaideepvm\Downloads\USAMReport-21-40-1-5.pdf"
    
    # Step 1: Check if PDF exists
    print("\n1️⃣ Checking PDF File...")
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
    print(f"✅ PDF found: {Path(pdf_path).name}")
    print(f"   Size: {file_size:.2f} MB")
    
    # Step 2: Test RAG API availability
    print("\n2️⃣ Checking RAG API...")
    if not check_api_health():
        print("❌ RAG API not available - cannot continue test")
        return
    
    print("✅ RAG API is running")
    
    # Step 3: Ingest PDF using file upload endpoint
    print("\n3️⃣ Ingesting PDF into RAG System...")
    ingestion_result = ingest_pdf_file(pdf_path)
    
    if not ingestion_result or ingestion_result.get('status') != 'success':
        print("❌ PDF ingestion failed - cannot test queries")
        if ingestion_result:
            print(f"   Error: {ingestion_result}")
        return
    
    print(f"✅ PDF successfully ingested")
    print(f"   File ID: {ingestion_result.get('file_id', 'N/A')}")
    print(f"   Chunks created: {ingestion_result.get('chunks_created', 0)}")
    print(f"   Vectors stored: {ingestion_result.get('vectors_stored', 0)}")
    
    # Step 4: Test queries on ingested PDF
    print("\n4️⃣ Testing Queries on PDF Content...")
    test_queries = [
        "What is this document about?",
        "What are the main topics covered?",
        "Tell me about any findings or conclusions",
        "What recommendations are made?",
        "Summarize the key points from this report"
    ]
    
    query_results = []
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        result = query_rag_system(query)
        query_results.append({'query': query, 'result': result})
        
        if result and 'error' not in str(result):
            print(f"✅ Query successful")
            print(f"📄 Response preview: {str(result)[:200]}...")
        else:
            print(f"❌ Query failed: {result}")
    
    # Step 5: Test specific PDF content search
    print("\n5️⃣ Testing PDF-Specific Content Search...")
    pdf_specific_queries = [
        f"What information is in the {Path(pdf_path).name} document?",
        "Show me content from the USAM report",
        "What are the details in this PDF file?"
    ]
    
    for query in pdf_specific_queries:
        print(f"\n🔍 PDF Query: {query}")
        result = query_rag_system(query)
        
        if result and 'error' not in str(result):
            print(f"✅ PDF query successful")
            print(f"📄 Response preview: {str(result)[:200]}...")
        else:
            print(f"❌ PDF query failed: {result}")
    
    # Step 6: Summary
    print("\n" + "=" * 50)
    print("📊 PDF WORKFLOW TEST SUMMARY")
    print("=" * 50)
    print(f"PDF File: {Path(pdf_path).name}")
    print(f"File Size: {file_size:.2f} MB")
    print(f"Ingestion Status: {'✅ Success' if ingestion_result else '❌ Failed'}")
    print(f"Chunks Created: {ingestion_result.get('chunks_created', 0) if ingestion_result else 0}")
    print(f"Vectors Stored: {ingestion_result.get('vectors_stored', 0) if ingestion_result else 0}")
    print(f"Queries Tested: {len(test_queries) + len(pdf_specific_queries)}")
    print(f"Successful Queries: {len([r for r in query_results if r['result'] and 'error' not in str(r['result'])])}")
    
    return {
        'pdf_file': Path(pdf_path).name,
        'file_size_mb': file_size,
        'ingestion_success': bool(ingestion_result and ingestion_result.get('status') == 'success'),
        'chunks_created': ingestion_result.get('chunks_created', 0) if ingestion_result else 0,
        'vectors_stored': ingestion_result.get('vectors_stored', 0) if ingestion_result else 0,
        'queries_successful': len([r for r in query_results if r['result'] and 'error' not in str(r['result'])])
    }

def check_api_health():
    """Check if RAG API is running"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def ingest_pdf_file(pdf_path):
    """Ingest PDF file using the upload endpoint"""
    try:
        api_base_url = "http://localhost:8000"
        
        # Prepare metadata
        metadata = {
            "title": Path(pdf_path).stem.replace('-', ' ').replace('_', ' ').title(),
            "source": "pdf_upload",
            "document_type": "pdf_report",
            "file_type": "pdf",
            "original_path": pdf_path,
            "description": f"PDF document: {Path(pdf_path).name}"
        }
        
        print(f"   📤 Uploading: {Path(pdf_path).name}")
        print(f"   📋 Metadata: {metadata['title']}")
        
        # Upload file
        with open(pdf_path, 'rb') as f:
            files = {
                'file': (Path(pdf_path).name, f, 'application/pdf')
            }
            data = {
                'metadata': json.dumps(metadata)
            }
            
            response = requests.post(
                f"{api_base_url}/upload",
                files=files,
                data=data,
                timeout=300  # 5 minutes for PDF processing
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Upload successful")
            return result
        else:
            print(f"   ❌ Upload failed: HTTP {response.status_code}")
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
            except:
                print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error uploading PDF: {e}")
        return None

def query_rag_system(query):
    """Query the RAG system"""
    try:
        api_base_url = "http://localhost:8000"
        
        response = requests.post(
            f"{api_base_url}/query",
            json={"query": query, "max_results": 3},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', result.get('answer', str(result)))
        else:
            return f"Query error: HTTP {response.status_code}"
            
    except Exception as e:
        return f"Query error: {str(e)}"

def test_pdf_extraction_methods():
    """Test different PDF extraction methods available in the system"""
    print("\n🔧 Testing PDF Extraction Methods...")
    
    pdf_path = r"C:\Users\jaideepvm\Downloads\USAMReport-21-40-1-5.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Test 1: Check if PDF processors are available
    try:
        sys.path.append('rag_system/src')
        from ingestion.processors.pdf_processor import PDFProcessor
        
        print("✅ PDFProcessor available")
        
        # Test basic PDF processing
        processor = PDFProcessor()
        print("✅ PDFProcessor initialized")
        
        # Test if we can process the PDF
        try:
            result = processor.process_file(pdf_path)
            if result:
                print(f"✅ PDF processing test successful")
                print(f"   Chunks generated: {len(result.get('chunks', []))}")
                if result.get('chunks'):
                    first_chunk = result['chunks'][0]
                    print(f"   First chunk preview: {first_chunk.get('text', '')[:100]}...")
            else:
                print("❌ PDF processing returned no result")
        except Exception as e:
            print(f"❌ PDF processing failed: {e}")
            
    except ImportError as e:
        print(f"❌ PDFProcessor not available: {e}")
    except Exception as e:
        print(f"❌ Error testing PDF processor: {e}")

if __name__ == "__main__":
    # Test PDF extraction methods first
    test_pdf_extraction_methods()
    
    # Then test complete workflow
    print("\n" + "=" * 60)
    test_pdf_workflow() 