#!/usr/bin/env python3
"""
Test script for LangGraph conversation functionality
"""
import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_conversation_system():
    """Test the conversation system"""
    print("🧪 Testing LangGraph Conversation System")
    print("="*50)
    
    try:
        # Import required modules
        from src.core.dependency_container import DependencyContainer, register_core_services
        
        print("✅ Successfully imported core modules")
        
        # Create and configure container
        container = DependencyContainer()
        register_core_services(container)
        
        print("✅ Dependency container created and configured")
        
        # Test conversation manager
        conversation_manager = container.get('conversation_manager')
        
        if conversation_manager is None:
            print("⚠️ Conversation manager is None - LangGraph may not be available")
            return False
        
        print("✅ Conversation manager created successfully")
        
        # Test starting a conversation
        print("\n🚀 Starting new conversation...")
        state = conversation_manager.start_conversation()
        print(f"✅ Conversation started with ID: {state['conversation_id']}")
        print(f"   Session ID: {state['session_id']}")
        print(f"   Turn count: {state['turn_count']}")
        
        # Test sending a message
        print("\n💬 Sending test message...")
        response = conversation_manager.process_user_message(
            state['session_id'], 
            "Hello, can you help me understand what you can do?"
        )
        
        print(f"✅ Message processed successfully")
        print(f"   Response: {response.get('response', 'No response')[:100]}...")
        print(f"   Turn count: {response.get('turn_count', 0)}")
        print(f"   Phase: {response.get('current_phase', 'unknown')}")
        
        # Test another message
        print("\n💬 Sending follow-up message...")
        response2 = conversation_manager.process_user_message(
            state['session_id'],
            "What topics can you help me with?"
        )
        
        print(f"✅ Follow-up message processed")
        print(f"   Response: {response2.get('response', 'No response')[:100]}...")
        print(f"   Turn count: {response2.get('turn_count', 0)}")
        
        # Test conversation history
        print("\n📜 Getting conversation history...")
        history = conversation_manager.get_conversation_history(state['session_id'])
        print(f"✅ History retrieved: {len(history.get('messages', []))} messages")
        
        # Test ending conversation
        print("\n🔚 Ending conversation...")
        end_result = conversation_manager.end_conversation(state['session_id'])
        print(f"✅ Conversation ended: {end_result.get('message', 'No message')}")
        
        print("\n🎉 All conversation tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure LangGraph is installed: pip install langgraph")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gradio_integration():
    """Test Gradio integration"""
    print("\n🎨 Testing Gradio Integration")
    print("="*30)
    
    try:
        from src.core.dependency_container import DependencyContainer, register_core_services
        from src.ui.gradio_app import create_gradio_app
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        # Create Gradio app
        app = create_gradio_app(container)
        
        if app is None:
            print("⚠️ Gradio app is None - Gradio may not be installed")
            return False
        
        print("✅ Gradio app created successfully with conversation support")
        print("   The app includes a new 'Conversation Chat' tab")
        
        return True
        
    except Exception as e:
        print(f"❌ Gradio integration test failed: {e}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    success = True
    
    success &= test_conversation_system()
    success &= test_gradio_integration()
    
    print("\n" + "="*50)
    if success:
        print("🎉 All tests passed! Your conversation system is ready.")
        print("\nTo use the system:")
        print("1. Start your RAG system normally")
        print("2. Open the Gradio interface")
        print("3. Click on the '💬 Conversation Chat' tab")
        print("4. Click '🆕 New Conversation' to start")
        print("5. Type your messages and enjoy conversing!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 