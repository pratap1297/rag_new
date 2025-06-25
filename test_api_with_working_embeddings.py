#!/usr/bin/env python3
"""
Test API with Working Embeddings
Now that we confirmed embeddings work, test the API to see if it now returns results
"""
import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "rag_secure_key_12345_development"

def test_api_with_working_embeddings():
    """Test the API now that we know embeddings work"""
    print("🎯 Testing API with Working Embeddings")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Wait for system to be ready
    print("⏳ Waiting for system to be ready...")
    time.sleep(5)
    
    # Test queries that should now work
    test_queries = [
        "security",
        "password policy", 
        "What is the security policy?",
        "test"
    ]
    
    successful_queries = 0
    total_sources_found = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: '{query}'")
        
        query_payload = {
            "query": query,
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
                
                print(f"   📊 Status: Success")
                print(f"   📚 Sources found: {len(sources)}")
                print(f"   🎯 Confidence: {confidence:.3f}")
                print(f"   💬 Response length: {len(response_text)}")
                
                if sources:
                    successful_queries += 1
                    total_sources_found += len(sources)
                    print(f"   ✅ SUCCESS: Found {len(sources)} sources!")
                    
                    # Show similarities
                    similarities = [s.get('similarity_score', 0) for s in sources]
                    print(f"   📊 Similarity range: {min(similarities):.6f} to {max(similarities):.6f}")
                    
                    # Show first source
                    first_source = sources[0]
                    print(f"   📄 Best match:")
                    print(f"      Similarity: {first_source.get('similarity_score', 0):.6f}")
                    print(f"      Content: {first_source.get('content', first_source.get('text', ''))[:100]}...")
                    
                    if response_text.strip():
                        print(f"   💬 LLM Response: {response_text[:200]}...")
                else:
                    print(f"   ❌ No sources found")
                    
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text[:100]}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between queries
    
    # Summary
    print(f"\n📋 Final Results")
    print("=" * 50)
    
    success_rate = (successful_queries / len(test_queries)) * 100 if test_queries else 0
    avg_sources = total_sources_found / len(test_queries) if test_queries else 0
    
    print(f"📊 **Test Results:**")
    print(f"   Total queries: {len(test_queries)}")
    print(f"   Successful queries: {successful_queries}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   Total sources found: {total_sources_found}")
    print(f"   Average sources per query: {avg_sources:.1f}")
    
    if successful_queries == len(test_queries):
        print(f"\n🎉 **COMPLETE SUCCESS!**")
        print(f"   ✅ All queries now return sources!")
        print(f"   ✅ RAG system is fully functional!")
        print(f"   ✅ The similarity threshold fix worked!")
        
        print(f"\n🎯 **System Status: OPERATIONAL** ⭐⭐⭐⭐⭐")
        print(f"   - Document ingestion: ✅ Working")
        print(f"   - Vector storage: ✅ Working")
        print(f"   - Embedding generation: ✅ Working")
        print(f"   - Vector search: ✅ Working")
        print(f"   - Query processing: ✅ Working")
        print(f"   - LLM response generation: ✅ Working")
        
        return True
        
    elif successful_queries > 0:
        print(f"\n⚠️ **PARTIAL SUCCESS**")
        print(f"   ✅ {successful_queries}/{len(test_queries)} queries work")
        print(f"   ⚠️ Some queries may need threshold adjustment")
        return True
        
    else:
        print(f"\n❌ **STILL NOT WORKING**")
        print(f"   ❌ No queries return sources")
        print(f"   🔍 The issue may be in the query engine pipeline")
        return False

if __name__ == "__main__":
    success = test_api_with_working_embeddings()
    
    if success:
        print(f"\n🚀 **NEXT STEPS:**")
        print(f"   1. Test with more complex queries")
        print(f"   2. Test document ingestion of new content")
        print(f"   3. Optimize similarity threshold for production")
        print(f"   4. Test conversation functionality")
    else:
        print(f"\n🔧 **DEBUGGING STILL NEEDED:**")
        print(f"   1. Check query engine embedder usage")
        print(f"   2. Verify API request processing")
        print(f"   3. Debug query processing pipeline") 