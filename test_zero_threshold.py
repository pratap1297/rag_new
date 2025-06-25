#!/usr/bin/env python3
"""
Test Zero Threshold
Test with similarity threshold set to 0.0 to accept any results
"""
import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "rag_secure_key_12345_development"

def test_zero_threshold():
    """Test with zero similarity threshold"""
    print("🔧 Testing with Zero Similarity Threshold")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Wait for system to start
    print("⏳ Waiting for system to start...")
    time.sleep(15)
    
    # Test a simple query
    print("\n🔍 Testing simple query with zero threshold...")
    
    query_payload = {
        "query": "test",
        "max_results": 10
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query", 
            json=query_payload, 
            headers=headers, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get('sources', [])
            confidence = result.get('confidence_score', 0)
            response_text = result.get('response', '')
            
            print(f"✅ Query successful!")
            print(f"📚 Sources found: {len(sources)}")
            print(f"🎯 Confidence: {confidence:.3f}")
            print(f"💬 Response length: {len(response_text)}")
            
            if sources:
                print(f"\n🎉 SUCCESS! Found {len(sources)} sources with zero threshold!")
                
                # Show details of first few sources
                for i, source in enumerate(sources[:3], 1):
                    print(f"\n📄 Source {i}:")
                    print(f"   Doc ID: {source.get('doc_id', 'Unknown')}")
                    print(f"   Similarity: {source.get('similarity_score', 0):.6f}")
                    print(f"   Content: {source.get('text', '')[:150]}...")
                
                if response_text.strip():
                    print(f"\n💬 LLM Response: {response_text[:300]}...")
                
                print(f"\n✅ CONCLUSION: Vector search is working!")
                print(f"   The issue was the similarity threshold being too high.")
                print(f"   Minimum similarity scores found: {min(s.get('similarity_score', 0) for s in sources):.6f}")
                print(f"   Maximum similarity scores found: {max(s.get('similarity_score', 0) for s in sources):.6f}")
                
            else:
                print(f"\n❌ Still no sources found even with zero threshold!")
                print(f"   This indicates a deeper issue in the vector search mechanism.")
                print(f"   Possible causes:")
                print(f"   - FAISS index not being searched properly")
                print(f"   - Embedding generation failing for queries")
                print(f"   - Vector search returning empty results")
                print(f"   - Metadata filtering blocking all results")
        else:
            print(f"❌ Query failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error text: {response.text}")
                
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    test_zero_threshold() 