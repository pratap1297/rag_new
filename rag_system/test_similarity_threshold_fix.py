#!/usr/bin/env python3
"""
Test script to verify similarity threshold bypass functionality
"""

import sys
import os
import asyncio
import aiohttp
import json
from datetime import datetime

# Add the parent directory to sys.path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_direct_query_endpoint():
    """Test the direct query endpoint"""
    print("=" * 60)
    print("TESTING DIRECT QUERY ENDPOINT")
    print("=" * 60)
    
    query_data = {
        "query": "What types of access points are used in Building A?"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"Status: {response.status}")
                result = await response.json()
                
                print(f"Response: {result.get('response', 'No response')[:200]}...")
                print(f"Sources found: {len(result.get('sources', []))}")
                print(f"Confidence: {result.get('confidence_score', 0)}")
                
                if result.get('sources'):
                    print("\nSource details:")
                    for i, source in enumerate(result['sources'][:3]):
                        print(f"  Source {i+1}: Score={source.get('similarity_score', 0):.3f}")
                        print(f"    Content: {source.get('text', '')[:100]}...")
                
                return result
                
        except Exception as e:
            print(f"Direct query failed: {e}")
            return None

async def test_conversation_endpoint():
    """Test the conversation endpoint"""
    print("\n" + "=" * 60)
    print("TESTING CONVERSATION ENDPOINT")
    print("=" * 60)
    
    conversation_data = {
        "message": "What types of access points are used in Building A?",
        "session_id": "test_threshold_fix"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/conversation/chat",
                json=conversation_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"Status: {response.status}")
                result = await response.json()
                
                print(f"Response: {result.get('response', 'No response')[:200]}...")
                print(f"Sources found: {len(result.get('sources', []))}")
                print(f"Confidence: {result.get('confidence_score', 0)}")
                
                if result.get('sources'):
                    print("\nSource details:")
                    for i, source in enumerate(result['sources'][:3]):
                        print(f"  Source {i+1}: Score={source.get('similarity_score', 0):.3f}")
                        print(f"    Content: {source.get('text', '')[:100]}...")
                else:
                    print("No sources returned - this indicates the threshold bypass may not be working")
                
                return result
                
        except Exception as e:
            print(f"Conversation query failed: {e}")
            return None

async def test_comparison():
    """Compare results between direct and conversation endpoints"""
    print("\n" + "=" * 60)
    print("COMPARISON ANALYSIS")
    print("=" * 60)
    
    # Test both endpoints
    direct_result = await test_direct_query_endpoint()
    conversation_result = await test_conversation_endpoint()
    
    if direct_result and conversation_result:
        direct_sources = len(direct_result.get('sources', []))
        conversation_sources = len(conversation_result.get('sources', []))
        
        print(f"\nCOMPARISON RESULTS:")
        print(f"Direct query sources: {direct_sources}")
        print(f"Conversation sources: {conversation_sources}")
        
        if conversation_sources >= direct_sources and conversation_sources > 0:
            print("✅ SUCCESS: Conversation system now returns sources!")
            print("✅ The similarity threshold bypass is working correctly.")
        elif conversation_sources > 0:
            print("⚠️  PARTIAL SUCCESS: Conversation system returns some sources.")
            print(f"   But fewer than direct query ({conversation_sources} vs {direct_sources})")
        else:
            print("❌ FAILURE: Conversation system still returns no sources.")
            print("   The threshold bypass may not be working.")
        
        # Check if responses are meaningful
        conv_response = conversation_result.get('response', '')
        if 'couldn\'t find' in conv_response.lower() or 'no relevant' in conv_response.lower():
            print("❌ Conversation response still indicates no information found")
        else:
            print("✅ Conversation response appears to contain actual information")
            
    else:
        print("❌ Could not complete comparison - one or both endpoints failed")

async def main():
    """Run all tests"""
    print("SIMILARITY THRESHOLD BYPASS TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("\nThis test verifies that the conversation system now bypasses")
    print("the similarity threshold to match the direct query behavior.\n")
    
    await test_comparison()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 