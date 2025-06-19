#!/usr/bin/env python3
"""Test script for improved conversation suggestions"""

import requests
import json
import time

def test_suggestions():
    """Test the improved suggestions system"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Improved Conversation Suggestions System")
    print("=" * 60)
    
    # Start a new conversation
    print("\n1. Starting new conversation...")
    try:
        response = requests.post(f"{base_url}/api/conversation/start", json={})
        if response.status_code == 200:
            data = response.json()
            thread_id = data.get("thread_id")
            print(f"✅ Started conversation with thread ID: {thread_id}")
        else:
            print(f"❌ Failed to start conversation: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error starting conversation: {e}")
        return
    
    # Test with "Who is Maria Garcia?" question
    print("\n2. Testing 'Who is Maria Garcia?' question...")
    try:
        message_data = {
            "message": "Who is Maria Garcia?",
            "thread_id": thread_id
        }
        
        response = requests.post(
            f"{base_url}/api/conversation/message", 
            json=message_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got response with status: {response.status_code}")
            
            # Check the response
            response_text = data.get("response", "")
            print(f"📝 Response: {response_text[:200]}...")
            
            # Check suggested questions
            suggested_questions = data.get("suggested_questions", [])
            print(f"\n💡 Suggested Questions ({len(suggested_questions)}):")
            for i, question in enumerate(suggested_questions, 1):
                print(f"   {i}. {question}")
            
            # Check related topics
            related_topics = data.get("related_topics", [])
            print(f"\n🔗 Related Topics ({len(related_topics)}):")
            for topic in related_topics:
                print(f"   • {topic}")
            
            # Check sources
            sources = data.get("sources", [])
            print(f"\n📚 Sources Found: {len(sources)}")
            for i, source in enumerate(sources[:3], 1):
                score = source.get("score", 0)
                content = source.get("content", "")[:100]
                print(f"   {i}. Score: {score:.3f} - {content}...")
            
            # Check if suggestions are improved
            print(f"\n🔍 Analyzing Suggestion Quality:")
            generic_patterns = ["would you like to know more about", "how does", "relate to your specific needs"]
            improved_suggestions = []
            generic_suggestions = []
            
            for question in suggested_questions:
                is_generic = any(pattern in question.lower() for pattern in generic_patterns)
                if is_generic:
                    generic_suggestions.append(question)
                else:
                    improved_suggestions.append(question)
            
            print(f"   ✅ Improved suggestions: {len(improved_suggestions)}")
            print(f"   ⚠️  Generic suggestions: {len(generic_suggestions)}")
            
            if improved_suggestions:
                print("   🎯 Examples of improved suggestions:")
                for suggestion in improved_suggestions[:2]:
                    print(f"      • {suggestion}")
            
            if generic_suggestions:
                print("   📝 Generic suggestions still present:")
                for suggestion in generic_suggestions[:2]:
                    print(f"      • {suggestion}")
            
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return
    
    print("\n" + "=" * 60)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_suggestions() 