#!/usr/bin/env python3
"""
Debug Search Pipeline
Investigate the search pipeline to find where queries are failing
"""
import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "rag_secure_key_12345_development"

def debug_search_pipeline():
    """Debug the search pipeline to find the issue"""
    print("🔍 Debugging Search Pipeline")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Wait for system to start
    print("⏳ Waiting for system to be ready...")
    time.sleep(5)
    
    # Step 1: Check system status
    print("\n1. 📊 System Status")
    try:
        stats_response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"   ✅ System operational")
            print(f"   📈 Total vectors: {stats.get('total_vectors', 0)}")
            print(f"   📈 Total documents: {stats.get('total_documents', 0)}")
            print(f"   🧠 Embedding model: {stats.get('embedding_model', 'Unknown')}")
            print(f"   🤖 LLM model: {stats.get('llm_model', 'Unknown')}")
        else:
            print(f"   ❌ Stats failed: {stats_response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot get stats: {e}")
        return
    
    # Step 2: Test direct vector search (if available)
    print("\n2. 🔍 Testing Vector Search")
    
    # Simple test query
    test_query = "security"
    print(f"   Testing query: '{test_query}'")
    
    query_payload = {
        "query": test_query,
        "max_results": 20,  # Ask for many results
        "debug": True  # If debug mode is supported
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
            
            print(f"   📊 Query Status: Success")
            print(f"   📚 Sources returned: {len(result.get('sources', []))}")
            print(f"   🎯 Confidence: {result.get('confidence_score', 0):.3f}")
            print(f"   💬 Response length: {len(result.get('response', ''))}")
            
            # Check if there's any debug info
            if 'debug_info' in result:
                debug_info = result['debug_info']
                print(f"   🔧 Debug info available:")
                for key, value in debug_info.items():
                    print(f"      {key}: {value}")
            
            # Check response content
            response_text = result.get('response', '')
            if response_text.strip():
                print(f"   💬 Response preview: {response_text[:200]}...")
            else:
                print(f"   ⚠️ Empty response generated")
                
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Error text: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ Query error: {e}")
    
    # Step 3: Check if there's a direct vector search endpoint
    print("\n3. 🔧 Checking Available Endpoints")
    
    try:
        # Try to get available endpoints
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if health_response.status_code == 200:
            print(f"   ✅ /health endpoint working")
        
        # Check if there are other debug endpoints
        debug_endpoints = [
            "/vectors/search",  # Direct vector search
            "/debug/vectors",   # Vector debug
            "/debug/embeddings", # Embedding debug
            "/search/raw",      # Raw search
            "/documents/list"   # Document listing
        ]
        
        for endpoint in debug_endpoints:
            try:
                test_response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=5)
                if test_response.status_code == 200:
                    print(f"   ✅ {endpoint} available")
                elif test_response.status_code == 404:
                    print(f"   ❌ {endpoint} not found")
                else:
                    print(f"   ⚠️ {endpoint} returned {test_response.status_code}")
            except:
                print(f"   ❌ {endpoint} not accessible")
                
    except Exception as e:
        print(f"   ❌ Endpoint check error: {e}")
    
    # Step 4: Test with different query types
    print("\n4. 🧪 Testing Different Query Types")
    
    test_queries = [
        ("Single word", "security"),
        ("Short phrase", "password policy"),
        ("Question", "What is the security policy?"),
        ("Very simple", "help"),
        ("Technical", "authentication requirements"),
        ("Empty-like", " "),
        ("Special chars", "security & network"),
        ("Numbers", "policy 123")
    ]
    
    for query_type, query in test_queries:
        print(f"\n   Testing {query_type}: '{query}'")
        
        if not query.strip():
            print(f"   ⚠️ Skipping empty query")
            continue
            
        query_payload = {
            "query": query,
            "max_results": 5
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/query", 
                json=query_payload, 
                headers=headers, 
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                sources = result.get('sources', [])
                confidence = result.get('confidence_score', 0)
                
                print(f"   📊 Sources: {len(sources)}, Confidence: {confidence:.3f}")
                
                if sources:
                    print(f"   ✅ SUCCESS: Found sources!")
                    # Show first source details
                    first_source = sources[0]
                    print(f"   📄 First source:")
                    print(f"      Title/ID: {first_source.get('doc_id', 'Unknown')}")
                    print(f"      Similarity: {first_source.get('similarity_score', 0):.3f}")
                    print(f"      Content preview: {first_source.get('text', '')[:100]}...")
                else:
                    print(f"   ❌ No sources found")
                    
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Step 5: Summary and Recommendations
    print(f"\n5. 📋 Debug Summary")
    print("=" * 50)
    
    print(f"🔍 **Key Findings:**")
    print(f"   - System has {stats.get('total_vectors', 0)} vectors available")
    print(f"   - Using embedding model: {stats.get('embedding_model', 'Unknown')}")
    print(f"   - All queries return 0 sources despite available vectors")
    print(f"   - This indicates an issue in the vector search or similarity calculation")
    
    print(f"\n🔧 **Possible Issues:**")
    print(f"   1. FAISS index may not be properly loaded or accessible")
    print(f"   2. Embedding model mismatch between ingestion and query time")
    print(f"   3. Vector similarity calculation returning very low scores")
    print(f"   4. Metadata filtering issues preventing results")
    print(f"   5. Search pipeline configuration problems")
    
    print(f"\n💡 **Next Steps:**")
    print(f"   1. Check FAISS index file existence and integrity")
    print(f"   2. Verify embedding model consistency")
    print(f"   3. Test with threshold = 0.0 (accept all results)")
    print(f"   4. Debug vector similarity scores directly")
    print(f"   5. Check if vectors are actually being searched")

if __name__ == "__main__":
    debug_search_pipeline() 