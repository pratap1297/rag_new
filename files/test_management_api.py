#!/usr/bin/env python3
"""
Test script for RAG System Management API
Tests all management endpoints to ensure they work correctly
"""
import requests
import json
import time
from typing import Dict, Any

class ManagementAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_endpoint(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test an API endpoint and return results"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "data": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "data": None,
                "error": str(e)
            }
    
    def run_all_tests(self):
        """Run comprehensive tests of the management API"""
        print("🧪 Testing RAG System Management API")
        print("=" * 50)
        
        # Test 1: System Health
        print("\n1. Testing System Health...")
        health = self.test_endpoint("GET", "/health")
        if health["success"]:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {health['error']}")
            return
        
        # Test 2: Basic Stats
        print("\n2. Testing Basic Stats...")
        stats = self.test_endpoint("GET", "/stats")
        if stats["success"]:
            print("✅ Stats endpoint working")
            print(f"   Vectors: {stats['data'].get('faiss_store', {}).get('vector_count', 0)}")
        else:
            print(f"❌ Stats failed: {stats['error']}")
        
        # Test 3: Detailed Stats
        print("\n3. Testing Detailed Stats...")
        detailed_stats = self.test_endpoint("GET", "/manage/stats/detailed")
        if detailed_stats["success"]:
            print("✅ Detailed stats working")
            print(f"   Documents: {detailed_stats['data'].get('total_documents', 0)}")
            print(f"   Unknown docs: {detailed_stats['data'].get('unknown_documents', 0)}")
        else:
            print(f"❌ Detailed stats failed: {detailed_stats['error']}")
        
        # Test 4: List Documents
        print("\n4. Testing Document Listing...")
        docs = self.test_endpoint("GET", "/manage/documents", params={"limit": 5})
        if docs["success"]:
            print(f"✅ Document listing working ({len(docs['data'])} documents)")
            if docs['data']:
                print(f"   Sample doc: {docs['data'][0].get('doc_id', 'N/A')}")
        else:
            print(f"❌ Document listing failed: {docs['error']}")
        
        # Test 5: List Vectors
        print("\n5. Testing Vector Listing...")
        vectors = self.test_endpoint("GET", "/manage/vectors", params={"limit": 5})
        if vectors["success"]:
            print(f"✅ Vector listing working ({len(vectors['data'])} vectors)")
            if vectors['data']:
                print(f"   Sample vector: {vectors['data'][0].get('vector_id', 'N/A')}")
        else:
            print(f"❌ Vector listing failed: {vectors['error']}")
        
        # Test 6: Ingest Test Document
        print("\n6. Testing Document Ingestion...")
        test_doc = {
            "text": "This is a test document for the management API testing. It contains information about network security and system administration.",
            "metadata": {
                "title": "Management API Test Document",
                "description": "Test document for API validation",
                "author": "API Tester",
                "category": "test"
            }
        }
        
        ingest = self.test_endpoint("POST", "/ingest", json=test_doc)
        if ingest["success"]:
            print("✅ Document ingestion working")
            print(f"   Chunks created: {ingest['data'].get('chunks_created', 0)}")
        else:
            print(f"❌ Document ingestion failed: {ingest['error']}")
        
        # Test 7: Query System
        print("\n7. Testing Query System...")
        query = self.test_endpoint("POST", "/query", json={
            "query": "test document management API",
            "max_results": 2
        })
        if query["success"]:
            print("✅ Query system working")
            print(f"   Sources found: {len(query['data'].get('sources', []))}")
            if query['data'].get('sources'):
                print(f"   Top result: {query['data']['sources'][0].get('doc_id', 'N/A')}")
        else:
            print(f"❌ Query failed: {query['error']}")
        
        # Test 8: Document Details
        if docs["success"] and docs['data']:
            print("\n8. Testing Document Details...")
            sample_doc_id = docs['data'][0].get('doc_id')
            if sample_doc_id:
                doc_details = self.test_endpoint("GET", f"/manage/document/{sample_doc_id}")
                if doc_details["success"]:
                    print("✅ Document details working")
                    print(f"   Chunks: {doc_details['data'].get('chunk_count', 0)}")
                else:
                    print(f"❌ Document details failed: {doc_details['error']}")
        
        # Test 9: Cleanup Operations (non-destructive)
        print("\n9. Testing Cleanup Operations...")
        
        # Test reindexing (safe operation)
        reindex = self.test_endpoint("POST", "/manage/reindex/doc_ids")
        if reindex["success"]:
            print("✅ Document ID reindexing working")
            print(f"   Updated: {reindex['data'].get('affected_count', 0)} documents")
        else:
            print(f"❌ Reindexing failed: {reindex['error']}")
        
        # Test 10: Update Metadata (safe test)
        print("\n10. Testing Metadata Updates...")
        if vectors["success"] and vectors['data']:
            sample_vector_id = vectors['data'][0].get('vector_id')
            if sample_vector_id:
                update = self.test_endpoint("PUT", "/manage/update", json={
                    "vector_ids": [sample_vector_id],
                    "updates": {"test_flag": "api_test_" + str(int(time.time()))}
                })
                if update["success"]:
                    print("✅ Metadata update working")
                    print(f"   Updated: {update['data'].get('updated_count', 0)} vectors")
                else:
                    print(f"❌ Metadata update failed: {update['error']}")
        
        print("\n" + "=" * 50)
        print("🎉 Management API testing completed!")
        print("\nNext steps:")
        print("1. Start the Gradio UI: python launch_ui.py")
        print("2. Open http://localhost:7860 in your browser")
        print("3. Use the web interface to manage your RAG system")

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG System Management API")
    parser.add_argument(
        "--api-url", 
        default="http://localhost:8000",
        help="Base URL of the RAG system API"
    )
    
    args = parser.parse_args()
    
    tester = ManagementAPITester(args.api_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main() 