#!/usr/bin/env python3
"""
Upload missing documents to the vector store
"""
import requests
import os
from datetime import datetime

def upload_document(file_path, doc_path):
    """Upload a single document"""
    try:
        print(f"\n📤 Uploading: {os.path.basename(file_path)}")
        print(f"   Path: {file_path}")
        print(f"   Doc Path: {doc_path}")
        
        # Prepare metadata
        metadata = {
            "doc_path": doc_path,
            "operation": "upload",
            "source": "auto_upload_script",
            "upload_timestamp": datetime.now().isoformat(),
            "original_filename": os.path.basename(file_path)
        }
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Upload via file endpoint
        files = {'file': (os.path.basename(file_path), file_content, 'application/octet-stream')}
        data = {'metadata': str(metadata).replace("'", '"')}
        
        response = requests.post("http://localhost:8000/upload", files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            chunks_created = result.get('chunks_created', 0)
            print(f"   ✅ Success! Created {chunks_created} chunks")
            return True
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def upload_missing_documents():
    """Upload all missing documents"""
    print("=" * 60)
    print("UPLOADING MISSING DOCUMENTS")
    print("=" * 60)
    
    # Define documents to upload
    documents = [
        {
            "file_path": "document_generator/test_data/BuildingB_Network_Layout.pdf",
            "doc_path": "/docs/BuildingB_Network_Layout"
        },
        {
            "file_path": "document_generator/test_data/BuildingC_Network_Layout.pdf", 
            "doc_path": "/docs/BuildingC_Network_Layout"
        },
        {
            "file_path": "document_generator/test_data/Facility_Managers_2024.xlsx",
            "doc_path": "/docs/Facility_Managers_2024"
        }
    ]
    
    success_count = 0
    total_count = len(documents)
    
    for doc in documents:
        file_path = doc["file_path"]
        doc_path = doc["doc_path"]
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"\n❌ File not found: {file_path}")
            continue
            
        # Upload the document
        if upload_document(file_path, doc_path):
            success_count += 1
    
    print(f"\n" + "=" * 60)
    print(f"UPLOAD SUMMARY:")
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    print("=" * 60)
    
    if success_count > 0:
        print(f"\n🔄 Now checking updated document list...")
        
        # Wait a moment for processing
        import time
        time.sleep(2)
        
        # Check updated documents
        try:
            response = requests.get("http://localhost:8000/documents", timeout=10)
            if response.status_code == 200:
                data = response.json()
                total_docs = data.get('total_documents', 0)
                print(f"📊 Total documents now: {total_docs}")
                
                # Show document list
                document_details = data.get('document_details', [])
                building_docs = []
                excel_docs = []
                
                for doc in document_details:
                    filename = (doc.get('filename') or '').lower()
                    if 'building' in filename:
                        building_docs.append(doc.get('filename', 'Unknown'))
                    if any(term in filename for term in ['excel', 'xlsx', 'facility', 'manager']):
                        excel_docs.append(doc.get('filename', 'Unknown'))
                
                print(f"\n🏢 Building documents: {len(building_docs)}")
                for doc in building_docs:
                    print(f"   - {doc}")
                    
                print(f"\n📊 Excel/Roster documents: {len(excel_docs)}")
                for doc in excel_docs:
                    print(f"   - {doc}")
                    
        except Exception as e:
            print(f"❌ Error checking updated documents: {e}")

if __name__ == "__main__":
    upload_missing_documents() 