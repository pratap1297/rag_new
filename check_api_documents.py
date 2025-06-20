#!/usr/bin/env python3
"""
Check API documents directly to see all metadata
"""
import requests
import json

def check_api_documents():
    """Check documents via API directly"""
    print("=" * 60)
    print("CHECKING DOCUMENTS VIA API DIRECTLY")
    print("=" * 60)
    
    try:
        # Get documents from API
        response = requests.get("http://localhost:8000/documents", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API Response successful")
            print(f"📊 Total documents: {data.get('total_documents', 0)}")
            print(f"📋 Document list: {data.get('documents', [])}")
            
            document_details = data.get('document_details', [])
            print(f"\n📝 Document details ({len(document_details)} entries):")
            print("-" * 60)
            
            for i, doc in enumerate(document_details, 1):
                print(f"\n{i}. Document Detail:")
                print(f"   doc_id: {doc.get('doc_id', 'N/A')}")
                print(f"   doc_path: {doc.get('doc_path', 'N/A')}")
                print(f"   filename: {doc.get('filename', 'N/A')}")
                print(f"   chunks: {doc.get('chunks', 0)}")
                print(f"   source: {doc.get('source', 'N/A')}")
                print(f"   upload_timestamp: {doc.get('upload_timestamp', 'N/A')}")
                
                # Check for missing documents
                filename = (doc.get('filename') or '').lower()
                doc_id = (doc.get('doc_id') or '').lower()
                
                if 'building' in filename or 'building' in doc_id:
                    if 'buildingb' in filename or 'buildingb' in doc_id:
                        print(f"   🏢 BUILDING B DETECTED")
                    elif 'buildingc' in filename or 'buildingc' in doc_id:
                        print(f"   🏢 BUILDING C DETECTED")
                    else:
                        print(f"   🏢 BUILDING A DETECTED")
                
                if any(term in filename for term in ['excel', 'xlsx', 'facility', 'roster', 'manager']):
                    print(f"   📊 EXCEL/ROSTER DETECTED")
            
            print(f"\n" + "=" * 60)
            print("SUMMARY:")
            print(f"- Total unique documents: {data.get('total_documents', 0)}")
            print(f"- Document details entries: {len(document_details)}")
            print("=" * 60)
            
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_api_documents() 