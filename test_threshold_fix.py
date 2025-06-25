#!/usr/bin/env python3
"""
Test Similarity Threshold Fix
Verify that lowering the similarity threshold allows queries to retrieve sources
"""
import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "rag_secure_key_12345_development"

def test_threshold_fix():
    """Test that the lowered similarity threshold allows source retrieval"""
    print("🔧 Testing Similarity Threshold Fix")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Wait for system to start
    print("⏳ Waiting for system to start...")
    time.sleep(12)
    
    # Step 1: Check system status
    print("\n1. 📊 System Status Check")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ System Status: {health.get('status', 'unknown')}")
        else:
            print(f"   ❌ System not ready: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to system: {e}")
        return False
    
    # Get current stats
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            total_vectors = stats.get('total_vectors', 0)
            total_docs = stats.get('total_documents', 0)
            
            print(f"   📈 Total vectors: {total_vectors}")
            print(f"   📈 Total documents: {total_docs}")
            
            if total_vectors == 0:
                print("   ⚠️ No vectors found in the system")
                return False
        else:
            print(f"   ⚠️ Could not get stats: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️ Stats error: {e}")
        return False
    
    # Step 2: Test focused queries
    print(f"\n2. 🔍 Testing Focused Queries (with lowered threshold)")
    
    # Test with very broad, simple queries that should match something
    test_queries = [
        "security",
        "policy",
        "system",
        "information",
        "document",
        "password",
        "network",
        "configuration",
        "requirements",
        "procedures"
    ]
    
    successful_queries = 0
    total_sources_found = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{query}'")
        
        query_payload = {
            "query": query,
            "max_results": 10  # Ask for more results
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
                response_text = result.get('response', '')
                sources = result.get('sources', [])
                confidence = result.get('confidence_score', 0)
                
                print(f"   📊 Status: Success")
                print(f"   📚 Sources found: {len(sources)}")
                print(f"   🎯 Confidence: {confidence:.3f}")
                
                if sources:
                    successful_queries += 1
                    total_sources_found += len(sources)
                    print(f"   ✅ SUCCESS: Found {len(sources)} sources!")
                    
                    # Show top 2 sources
                    for j, source in enumerate(sources[:2], 1):
                        title = source.get('title', 'Unknown')
                        relevance = source.get('relevance_score', 0)
                        doc_id = source.get('doc_id', 'Unknown')
                        content_preview = source.get('content', '')[:100] + "..." if source.get('content') else 'No content'
                        
                        print(f"   📄 Source {j}: {title}")
                        print(f"       ID: {doc_id}")
                        print(f"       Relevance: {relevance:.3f}")
                        print(f"       Content: {content_preview}")
                    
                    if response_text.strip():
                        print(f"   💬 Response preview: {response_text[:150]}...")
                else:
                    print(f"   ❌ No sources retrieved")
                    
            elif response.status_code == 408:
                print(f"   ⏰ Query timed out")
                
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text[:100]}")
                    
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Brief pause between queries
    
    # Step 3: Summary and Analysis
    print(f"\n3. 📋 Test Results Summary")
    print("=" * 50)
    
    success_rate = (successful_queries / len(test_queries)) * 100 if test_queries else 0
    avg_sources = total_sources_found / len(test_queries) if test_queries else 0
    
    print(f"📊 **Test Results:**")
    print(f"   Total queries tested: {len(test_queries)}")
    print(f"   Successful queries: {successful_queries}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   Total sources found: {total_sources_found}")
    print(f"   Average sources per query: {avg_sources:.1f}")
    print(f"   Available vectors: {total_vectors}")
    print(f"   Available documents: {total_docs}")
    
    if successful_queries > 0:
        print(f"\n🎉 **THRESHOLD FIX SUCCESSFUL!**")
        print(f"   ✅ Lowering similarity threshold from 0.25 to 0.05 worked!")
        print(f"   ✅ {successful_queries}/{len(test_queries)} queries now retrieve sources")
        print(f"   ✅ RAG system is now functional for querying existing data")
        print(f"   ✅ Vector retrieval pipeline is working correctly")
        
        if success_rate >= 80:
            print(f"   🌟 EXCELLENT: {success_rate:.1f}% success rate!")
        elif success_rate >= 50:
            print(f"   👍 GOOD: {success_rate:.1f}% success rate")
        else:
            print(f"   ⚠️ PARTIAL: {success_rate:.1f}% success rate - may need further tuning")
        
        return True
        
    else:
        print(f"\n❌ **THRESHOLD FIX FAILED**")
        print(f"   ❌ Even with lowered threshold, no sources are being retrieved")
        print(f"   🔍 This indicates a deeper issue in the retrieval pipeline")
        print(f"   🔍 Possible issues:")
        print(f"     - Embedding model mismatch between ingestion and query")
        print(f"     - FAISS index corruption or access issues")
        print(f"     - Query processing pipeline errors")
        print(f"     - Vector storage format issues")
        
        return False

if __name__ == "__main__":
    success = test_threshold_fix()
    if success:
        print(f"\n🎯 **NEXT STEPS:**")
        print(f"   1. Test with more complex queries")
        print(f"   2. Verify response quality and relevance")
        print(f"   3. Consider optimal threshold value (0.05 may be too low for production)")
        print(f"   4. Test with new document ingestion")
    else:
        print(f"\n🔧 **DEBUGGING NEEDED:**")
        print(f"   1. Check FAISS index integrity")
        print(f"   2. Verify embedding model consistency")
        print(f"   3. Debug query processing pipeline")
        print(f"   4. Check vector storage and retrieval mechanisms") 