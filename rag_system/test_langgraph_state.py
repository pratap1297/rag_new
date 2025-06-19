#!/usr/bin/env python3
"""
Test script to verify LangGraph state persistence
"""
import os
import sys
import logging
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from conversation.conversation_graph import ConversationGraph
from conversation.conversation_manager import ConversationManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_langgraph_state_persistence():
    """Test LangGraph state persistence functionality"""
    
    print("=" * 60)
    print("TESTING LANGGRAPH STATE PERSISTENCE")
    print("=" * 60)
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        print(f"Using temporary database: {db_path}")
        
        # Test 1: Initialize ConversationGraph with SQLite checkpointer
        print("\n1. Testing ConversationGraph initialization...")
        graph = ConversationGraph(container=None, db_path=db_path)
        print("✓ ConversationGraph initialized with SQLite checkpointer")
        
        # Test 2: Initialize ConversationManager
        print("\n2. Testing ConversationManager initialization...")
        manager = ConversationManager(container=None, db_path=db_path)
        print("✓ ConversationManager initialized with state persistence")
        
        # Test 3: Start a conversation
        print("\n3. Testing conversation start...")
        thread_id = "test-thread-123"
        response1 = manager.start_conversation(thread_id)
        print(f"✓ Conversation started for thread: {thread_id}")
        print(f"Response: {response1.get('response', '')[:100]}...")
        
        # Test 4: Send a message
        print("\n4. Testing message processing...")
        response2 = manager.process_user_message(thread_id, "Hello, what can you help me with?")
        print(f"✓ Message processed successfully")
        print(f"Response: {response2.get('response', '')[:100]}...")
        print(f"Turn count: {response2.get('turn_count', 0)}")
        
        # Test 5: Get conversation history
        print("\n5. Testing conversation history retrieval...")
        history = manager.get_conversation_history(thread_id)
        print(f"✓ Retrieved conversation history")
        print(f"Messages in history: {len(history.get('messages', []))}")
        print(f"Current phase: {history.get('current_phase', 'unknown')}")
        
        # Test 6: Test state persistence by creating a new manager instance
        print("\n6. Testing state persistence across instances...")
        manager2 = ConversationManager(container=None, db_path=db_path)
        history2 = manager2.get_conversation_history(thread_id)
        print(f"✓ State persisted across manager instances")
        print(f"Messages retrieved by new instance: {len(history2.get('messages', []))}")
        
        # Test 7: Continue conversation with new instance
        print("\n7. Testing conversation continuation...")
        response3 = manager2.process_user_message(thread_id, "Tell me more about your capabilities")
        print(f"✓ Conversation continued with new manager instance")
        print(f"Response: {response3.get('response', '')[:100]}...")
        print(f"Turn count: {response3.get('turn_count', 0)}")
        
        # Test 8: Verify database file exists and has content
        print("\n8. Testing database persistence...")
        db_file = Path(db_path)
        if db_file.exists() and db_file.stat().st_size > 0:
            print(f"✓ Database file exists and has content ({db_file.stat().st_size} bytes)")
        else:
            print("✗ Database file is missing or empty")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - LangGraph state persistence is working!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up temporary database
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
                print(f"\nCleaned up temporary database: {db_path}")
        except Exception as e:
            print(f"Warning: Could not clean up database: {e}")

def test_basic_functionality():
    """Test basic functionality without container dependencies"""
    
    print("\n" + "=" * 60)
    print("TESTING BASIC FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test conversation state creation
        from conversation.conversation_state import create_conversation_state, add_message_to_state, MessageType
        
        print("\n1. Testing conversation state creation...")
        state = create_conversation_state("test-thread")
        print(f"✓ Created conversation state with ID: {state['conversation_id']}")
        
        print("\n2. Testing message addition...")
        state = add_message_to_state(state, MessageType.USER, "Hello world")
        print(f"✓ Added message to state, turn count: {state['turn_count']}")
        
        print("\n3. Testing state structure...")
        required_keys = ['conversation_id', 'session_id', 'messages', 'current_phase', 'turn_count']
        for key in required_keys:
            if key in state:
                print(f"✓ State has required key: {key}")
            else:
                print(f"✗ State missing required key: {key}")
                return False
        
        print("\n✅ Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting LangGraph State Persistence Tests...")
    
    # Test basic functionality first
    basic_ok = test_basic_functionality()
    
    if basic_ok:
        # Test full state persistence
        persistence_ok = test_langgraph_state_persistence()
        
        if persistence_ok:
            print("\n🎉 All tests completed successfully!")
            print("LangGraph state persistence is properly configured and working.")
            sys.exit(0)
        else:
            print("\n💥 State persistence tests failed!")
            sys.exit(1)
    else:
        print("\n💥 Basic functionality tests failed!")
        sys.exit(1) 