#!/usr/bin/env python3
"""
Test API queries to see if RAG system is working
"""

import requests
import json
import time

def test_api_queries():
    """Test various API queries"""
    
    print("🔍 Testing API Queries")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"❌ API returned status: {response.status_code}")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API on localhost:8000")
        print("   Please start the RAG system: python src/main_managed.py")
        return
    
    # Test queries
    test_queries = [
        "How many ServiceNow incidents are in the system?",
        "Who works with Maria Garcia?",
        "What documents are available?",
        "Tell me about network incidents"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing query: {query}")
        print("-" * 40)
        
        try:
            response = requests.post(
                'http://localhost:8000/api/chat',
                json={
                    'message': query,
                    'conversation_id': f'test_{int(time.time())}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'No response')
                sources = result.get('sources', [])
                
                print(f"✅ Response: {answer[:200]}...")
                print(f"📄 Sources: {len(sources)}")
                for j, source in enumerate(sources[:3], 1):  # Show first 3 sources
                    print(f"   {j}. {source}")
                if len(sources) > 3:
                    print(f"   ... and {len(sources) - 3} more sources")
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ Query timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)  # Small delay between queries

if __name__ == "__main__":
    test_api_queries() 