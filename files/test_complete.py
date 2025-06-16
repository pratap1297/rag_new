#!/usr/bin/env python3
"""
Complete RAG System Test
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def wait_for_server():
    print("🔄 Waiting for server...")
    for i in range(30):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server ready!")
                return True
        except:
            pass
        time.sleep(2)
    return False

def upload_documents():
    print("\n📁 Uploading test documents...")
    
    # Upload company policy
    try:
        with open("test_documents/company_policy.md", "rb") as f:
            files = {"file": f}
            metadata = json.dumps({"category": "policy", "department": "HR"})
            data = {"metadata": metadata}
            
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data, timeout=60)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Policy document: {result.get('chunks_created', 0)} chunks")
        else:
            print(f"❌ Policy upload failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Policy upload error: {e}")
    
    # Upload technical guide
    try:
        with open("test_documents/technical_guide.txt", "rb") as f:
            files = {"file": f}
            metadata = json.dumps({"category": "technical", "department": "Engineering"})
            data = {"metadata": metadata}
            
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data, timeout=60)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Technical guide: {result.get('chunks_created', 0)} chunks")
        else:
            print(f"❌ Technical upload failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Technical upload error: {e}")

def test_queries():
    print("\n🔍 Testing queries...")
    
    queries = [
        "What is the remote work policy?",
        "How many vacation days do employees get?",
        "What embedding model is used in the RAG system?",
        "How can I optimize performance?",
        "What benefits are offered?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        
        try:
            data = {"query": query, "top_k": 3}
            response = requests.post(f"{BASE_URL}/query", json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Sources: {result.get('total_sources', 0)}")
                print(f"   Response: {result.get('response', '')[:100]}...")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("🧪 RAG SYSTEM TEST")
    print("="*30)
    
    if not wait_for_server():
        print("❌ Server not available")
        return
    
    upload_documents()
    time.sleep(3)  # Wait for indexing
    test_queries()
    
    print("\n🎉 Test completed!")
    print("Visit http://localhost:8000/docs for API documentation")

if __name__ == "__main__":
    main() 