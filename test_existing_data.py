#!/usr/bin/env python3
"""
Test Existing Data Queries
Test queries against the already ingested data in the RAG system
"""
import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "rag_secure_key_12345_development"

def test_existing_data_queries():
    """Test queries against existing ingested data"""
    print("🔍 Testing Queries on Existing Ingested Data")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Wait for system to start
    print("⏳ Waiting for system to start...")
    time.sleep(10)
    
    # Step 1: Check system health and stats
    print("\n1. 📊 Checking system status...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ System Status: {health.get('status', 'unknown')}")
        else:
            print(f"   ❌ System not ready: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to system: {e}")
        return
    
    # Get current stats
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            total_vectors = stats.get('total_vectors', 0)
            total_docs = stats.get('total_documents', 0)
            embedding_model = stats.get('embedding_model', 'Unknown')
            
            print(f"   📈 Total vectors: {total_vectors}")
            print(f"   📈 Total documents: {total_docs}")
            print(f"   🧠 Embedding model: {embedding_model}")
            
            if total_vectors == 0:
                print("   ⚠️ No vectors found in the system")
                return
        else:
            print(f"   ⚠️ Could not get stats: {response.status_code}")
            return
    except Exception as e:
        print(f"   ⚠️ Stats error: {e}")
        return
    
    # Step 2: Test various queries on existing data
    print(f"\n2. 🔍 Testing queries on {total_vectors} existing vectors...")
    
    # Test queries that might match existing data
    test_queries = [
        # General queries
        "What is this document about?",
        "Tell me about security",
        "What are the requirements?",
        "How do I configure something?",
        "What are the procedures?",
        
        # Specific technical queries
        "password",
        "network",
        "security policy",
        "authentication",
        "configuration",
        
        # Very broad queries
        "help",
        "information",
        "guide",
        "documentation",
        "system"
    ]
    
    successful_queries = 0
    queries_with_sources = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{query}'")
        
        query_payload = {
            "query": query,
            "max_results": 5
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/query", 
                json=query_payload, 
                headers=headers, 
                timeout=25
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
                    queries_with_sources += 1
                    print(f"   📝 Response length: {len(response_text)} chars")
                    if response_text.strip():
                        print(f"   💬 Response preview: {response_text[:100]}...")
                        successful_queries += 1
                    
                    # Show top sources
                    for j, source in enumerate(sources[:2], 1):
                        title = source.get('title', 'Unknown')
                        relevance = source.get('relevance_score', 0)
                        print(f"   📄 Source {j}: {title} (relevance: {relevance:.3f})")
                        
                else:
                    print(f"   ⚠️ No sources retrieved")
                    
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
    
    # Step 3: Test with lower similarity threshold (if possible)
    print(f"\n3. 🔧 Testing with broader search parameters...")
    
    broad_query = {
        "query": "document information",
        "max_results": 10  # Ask for more results
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query", 
            json=broad_query, 
            headers=headers, 
            timeout=25
        )
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get('sources', [])
            print(f"   📚 Broad search found {len(sources)} sources")
            
            if sources:
                print("   🎯 Top sources from broad search:")
                for i, source in enumerate(sources[:3], 1):
                    title = source.get('title', 'Unknown')
                    relevance = source.get('relevance_score', 0)
                    doc_id = source.get('doc_id', 'Unknown')
                    print(f"     {i}. {title} (ID: {doc_id}, relevance: {relevance:.3f})")
        else:
            print(f"   ❌ Broad search failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Broad search error: {e}")
    
    # Step 4: Summary
    print(f"\n4. 📋 Query Test Summary")
    print("=" * 60)
    
    success_rate = (successful_queries / len(test_queries)) * 100 if test_queries else 0
    source_rate = (queries_with_sources / len(test_queries)) * 100 if test_queries else 0
    
    print(f"📊 **Results Overview:**")
    print(f"   Total queries tested: {len(test_queries)}")
    print(f"   Queries with sources: {queries_with_sources} ({source_rate:.1f}%)")
    print(f"   Successful responses: {successful_queries} ({success_rate:.1f}%)")
    print(f"   Available vectors: {total_vectors}")
    print(f"   Available documents: {total_docs}")
    
    if successful_queries > 0:
        print(f"\n🎉 **SUCCESS**: RAG system is retrieving from existing data!")
        print(f"   ✅ Vectors are accessible and searchable")
        print(f"   ✅ Query processing pipeline is working")
        print(f"   ✅ LLM is generating responses from retrieved content")
        
    elif queries_with_sources > 0:
        print(f"\n⚠️ **PARTIAL SUCCESS**: Sources found but responses need improvement")
        print(f"   ✅ Vector retrieval is working")
        print(f"   ⚠️ LLM response generation may need tuning")
        
    else:
        print(f"\n❌ **INVESTIGATION NEEDED**: No sources retrieved")
        print(f"   🔍 Similarity threshold may be too high")
        print(f"   🔍 Embedding model consistency needs checking")
        print(f"   🔍 Query processing pipeline needs debugging")
    
    print(f"\n💡 **Key Findings:**")
    print(f"   - System has {total_vectors} vectors ready for querying")
    print(f"   - Embedding model: {embedding_model}")
    print(f"   - Query success rate: {success_rate:.1f}%")
    
    if source_rate < 50:
        print(f"\n🔧 **Recommendations:**")
        print(f"   1. Check similarity threshold configuration (current: likely 0.25)")
        print(f"   2. Verify embedding model consistency between ingestion and query")
        print(f"   3. Test with more specific queries that match ingested content")
        print(f"   4. Consider lowering similarity threshold temporarily for testing")

if __name__ == "__main__":
    test_existing_data_queries() 