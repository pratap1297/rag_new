#!/usr/bin/env python3
"""
Test Document Ingestion Script
Demonstrates how to ingest various document types into the RAG system
"""
import requests
import json
import os
import time
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "rag_secure_key_12345_development"  # From .env file

def test_api_connection():
    """Test if the RAG API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API is healthy: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Make sure the RAG system is running at {API_BASE_URL}")
        return False

def ingest_text_document(file_path, metadata=None):
    """Ingest a text document using the text ingestion endpoint"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Default metadata
        if metadata is None:
            metadata = {
                "title": Path(file_path).stem.replace('_', ' ').title(),
                "source": "test_documents",
                "file_type": Path(file_path).suffix,
                "ingestion_method": "text_api"
            }
        
        payload = {
            "text": text_content,
            "metadata": metadata
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"📝 Ingesting text: {file_path}")
        response = requests.post(
            f"{API_BASE_URL}/ingest",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: {result.get('chunks_created', 0)} chunks created")
            return result
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
            except:
                print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def ingest_file_document(file_path, metadata=None):
    """Ingest a file document using the file upload endpoint"""
    try:
        # Default metadata
        if metadata is None:
            metadata = {
                "title": Path(file_path).stem.replace('_', ' ').title(),
                "source": "test_documents",
                "file_type": Path(file_path).suffix,
                "ingestion_method": "file_upload"
            }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }
        
        print(f"📄 Uploading file: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(file_path), f, 'application/octet-stream')
            }
            data = {
                'metadata': json.dumps(metadata)
            }
            
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=300
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: {result.get('chunks_created', 0)} chunks created")
            return result
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
            except:
                print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_query(query, max_results=3):
    """Test querying the RAG system"""
    try:
        payload = {
            "query": query,
            "max_results": max_results
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"🔍 Query: {query}")
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=payload,
            headers=headers,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📝 Answer: {result.get('response', 'No response')[:200]}...")
            
            sources = result.get('sources', [])
            if sources:
                print(f"   📚 Sources ({len(sources)}):")
                for i, source in enumerate(sources[:3], 1):
                    doc_id = source.get('doc_id', 'Unknown')
                    score = source.get('score', 0)
                    print(f"      {i}. {doc_id} (Score: {score:.3f})")
            else:
                print("   📚 No sources found")
            
            return result
        else:
            print(f"   ❌ Query failed: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Query error: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 RAG System Document Ingestion Test")
    print("=" * 50)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Cannot proceed without API connection")
        return
    
    print(f"\n📁 Current directory: {os.getcwd()}")
    
    # Define test documents with metadata
    test_documents = [
        {
            "file": "sample_knowledge_base.txt",
            "method": "text",
            "metadata": {
                "title": "Technical Knowledge Base",
                "description": "Comprehensive technical troubleshooting and procedures",
                "department": "IT",
                "category": "technical",
                "tags": ["troubleshooting", "procedures", "technical"]
            }
        },
        {
            "file": "api_documentation.md",
            "method": "text",
            "metadata": {
                "title": "API Documentation",
                "description": "Complete API reference and examples",
                "department": "Engineering",
                "category": "documentation",
                "tags": ["api", "documentation", "reference"]
            }
        },
        {
            "file": "employee_handbook.pdf",
            "method": "file",
            "metadata": {
                "title": "Employee Handbook",
                "description": "Company policies and procedures for employees",
                "department": "HR",
                "category": "policy",
                "tags": ["hr", "policy", "handbook"]
            }
        },
        {
            "file": "it_security_guidelines.docx",
            "method": "file",
            "metadata": {
                "title": "IT Security Guidelines",
                "description": "Security policies and best practices",
                "department": "IT",
                "category": "security",
                "tags": ["security", "policy", "guidelines"]
            }
        }
    ]
    
    # Ingest documents
    print(f"\n📥 Ingesting {len(test_documents)} test documents...")
    print("-" * 50)
    
    ingestion_results = []
    for doc_info in test_documents:
        file_path = doc_info["file"]
        
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue
        
        if doc_info["method"] == "text":
            result = ingest_text_document(file_path, doc_info["metadata"])
        else:
            result = ingest_file_document(file_path, doc_info["metadata"])
        
        if result:
            ingestion_results.append(result)
        
        # Small delay between ingestions
        time.sleep(1)
    
    print(f"\n✅ Ingestion completed: {len(ingestion_results)} documents processed")
    
    # Test queries
    print(f"\n🔍 Testing queries...")
    print("-" * 50)
    
    test_queries = [
        "How do I reset my password?",
        "What is the company vacation policy?",
        "How do I configure SSL certificates?",
        "What are the password requirements?",
        "How do I report a security incident?",
        "What is multi-factor authentication?",
        "How do I use the API?",
        "What are the emergency procedures?"
    ]
    
    for query in test_queries:
        test_query(query)
        print()  # Empty line for readability
        time.sleep(1)  # Small delay between queries
    
    # Get system stats
    print("📊 Getting system statistics...")
    print("-" * 50)
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("System Statistics:")
            
            if 'documents' in stats:
                doc_stats = stats['documents']
                print(f"  📄 Documents: {doc_stats.get('total', 0)}")
            
            if 'vectors' in stats:
                vec_stats = stats['vectors']
                print(f"  🔢 Vectors: {vec_stats.get('total', 0)}")
            
            if 'storage' in stats:
                storage_stats = stats['storage']
                print(f"  💾 Storage: {storage_stats.get('index_size', 'N/A')}")
        else:
            print(f"❌ Failed to get stats: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    
    print(f"\n🎉 Test completed successfully!")
    print("\nNext steps:")
    print("1. Try the Gradio UI at http://localhost:7860")
    print("2. Test more complex queries")
    print("3. Upload your own documents")

if __name__ == "__main__":
    main() 