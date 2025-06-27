#!/usr/bin/env python3
"""
Test the fixed conversation system
"""
import sys
import os
sys.path.insert(0, 'src')

def test_fixed_conversation():
    """Test the conversation system after the search_knowledge fix"""
    print("🔧 Testing Fixed Conversation System")
    print("=" * 50)
    
    try:
        from src.core.dependency_container import DependencyContainer
        from src.core.system_init import register_core_services
        
        container = DependencyContainer()
        register_core_services(container)
        
        conversation_manager = container.get('conversation_manager')
        if not conversation_manager:
            print("❌ Conversation manager not available")
            return
        
        print("✅ Conversation manager available")
        
        # Start conversation
        result = conversation_manager.start_conversation()
        thread_id = result.get('thread_id')
        print(f"✅ Started conversation: {thread_id}")
        
        # Test queries that should work
        test_queries = [
            "Who is Sarah Johnson?",
            "Sarah Johnson Shipping Manager", 
            "Tell me about Sarah Johnson",
            "What is Sarah Johnson's role?"
        ]
        
        for query in test_queries:
            print(f"\n💬 Testing: '{query}'")
            try:
                response = conversation_manager.process_user_message(thread_id, query)
                response_text = response.get('response', 'No response')
                print(f"✅ Response received ({len(response_text)} chars)")
                
                # Check if we got Sarah Johnson information
                if 'sarah johnson' in response_text.lower():
                    if 'shipping manager' in response_text.lower() or 'emp004' in response_text.lower():
                        print("🎯 Found Sarah Johnson's detailed information!")
                    else:
                        print("📝 Found Sarah Johnson mention")
                else:
                    print("⚠️  No Sarah Johnson information found")
                    
                # Show first 200 chars of response
                print(f"Response preview: {response_text[:200]}...")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_conversation() 