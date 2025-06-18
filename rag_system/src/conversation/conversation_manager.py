"""
Conversation Manager
High-level manager for LangGraph conversations
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .conversation_state import (
    ConversationState, MessageType, ConversationPhase,
    create_conversation_state, add_message_to_state, get_conversation_history
)
from .conversation_graph import ConversationGraph

class ConversationManager:
    """Manages conversations using LangGraph"""
    
    def __init__(self, container=None, session_timeout_minutes: int = 30):
        self.container = container
        self.session_timeout_minutes = session_timeout_minutes
        self.logger = logging.getLogger(__name__)
        
        # Active conversations by session ID
        self.active_conversations: Dict[str, ConversationState] = {}
        
        # Initialize conversation graph
        self.conversation_graph = ConversationGraph(container)
        
        self.logger.info("ConversationManager initialized")
    
    def start_conversation(self, session_id: Optional[str] = None) -> ConversationState:
        """Start a new conversation"""
        
        # Create new conversation state
        state = create_conversation_state(session_id)
        
        # Store in active conversations
        self.active_conversations[state['session_id']] = state
        
        # Directly add initial greeting instead of processing empty message
        greeting = "Hello! I'm your AI assistant. I can help you find information, answer questions, and have a conversation about various topics. What would you like to know?"
        state = add_message_to_state(state, MessageType.ASSISTANT, greeting)
        state['current_phase'] = ConversationPhase.UNDERSTANDING
        
        # Update stored state
        self.active_conversations[state['session_id']] = state
        
        self.logger.info(f"Started new conversation: {state['conversation_id']}")
        return state
    
    def process_user_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process a user message and return response"""
        
        try:
            # Get or create conversation state
            state = self.get_or_create_conversation(session_id)
            
            # Clean up expired conversations
            self._cleanup_expired_conversations()
            
            # Process message through graph
            updated_state = self.conversation_graph.process_message(state, message)
            
            # Update stored state
            self.active_conversations[session_id] = updated_state
            
            # Format response
            response = self._format_response(updated_state)
            
            self.logger.info(f"Processed message for session {session_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return {
                'response': "I apologize, but I encountered an error. Please try again.",
                'error': str(e),
                'session_id': session_id
            }
    
    def get_conversation_history(self, session_id: str, max_messages: int = 20) -> Dict[str, Any]:
        """Get conversation history for a session"""
        
        state = self.active_conversations.get(session_id)
        if not state:
            return {'messages': [], 'session_id': session_id}
        
        messages = get_conversation_history(state, max_messages)
        
        return {
            'messages': [
                {
                    'type': msg['type'].value,
                    'content': msg['content'],
                    'timestamp': msg['timestamp'],
                    'metadata': msg['metadata']
                }
                for msg in messages
            ],
            'session_id': session_id,
            'conversation_id': state['conversation_id'],
            'turn_count': state['turn_count'],
            'current_phase': state['current_phase'].value,
            'topics_discussed': state['topics_discussed']
        }
    
    def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End a conversation"""
        
        if session_id in self.active_conversations:
            state = self.active_conversations[session_id]
            
            # Add farewell message
            farewell = "Thank you for the conversation! Feel free to start a new chat anytime."
            state = add_message_to_state(state, MessageType.ASSISTANT, farewell)
            
            # Generate conversation summary
            summary = self._generate_conversation_summary(state)
            
            # Remove from active conversations
            del self.active_conversations[session_id]
            
            self.logger.info(f"Ended conversation for session {session_id}")
            
            return {
                'message': 'Conversation ended',
                'summary': summary,
                'session_id': session_id,
                'total_turns': state['turn_count']
            }
        
        return {'message': 'No active conversation found', 'session_id': session_id}
    
    def get_or_create_conversation(self, session_id: str) -> ConversationState:
        """Get existing conversation or create new one"""
        
        if session_id in self.active_conversations:
            state = self.active_conversations[session_id]
            
            # Check if conversation has expired
            last_activity = datetime.fromisoformat(state['last_activity'])
            if datetime.now() - last_activity > timedelta(minutes=self.session_timeout_minutes):
                # Conversation expired, create new one
                del self.active_conversations[session_id]
                return self.start_conversation(session_id)
            
            return state
        else:
            # Create new conversation
            return self.start_conversation(session_id)
    
    def _format_response(self, state: ConversationState) -> Dict[str, Any]:
        """Format conversation state into response"""
        
        # Get the latest assistant message
        assistant_messages = [msg for msg in state['messages'] if msg['type'] == MessageType.ASSISTANT]
        latest_response = assistant_messages[-1]['content'] if assistant_messages else ""
        
        response = {
            'response': latest_response,
            'session_id': state['session_id'],
            'conversation_id': state['conversation_id'],
            'turn_count': state['turn_count'],
            'current_phase': state['current_phase'].value,
            'confidence_score': state['response_confidence'],
            'confidence': state['response_confidence'],  # Add alias for compatibility
            'timestamp': datetime.now().isoformat()
        }
        
        # Add optional fields if available
        if state['suggested_questions']:
            response['suggested_questions'] = state['suggested_questions']
        
        if state['related_topics']:
            response['related_topics'] = state['related_topics']
        
        if state['search_results']:
            response['sources'] = [
                {
                    'content': result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                    'score': result['score'],
                    'source': result['source']
                }
                for result in state['search_results'][:3]
            ]
            response['total_sources'] = len(state['search_results'])
        else:
            response['total_sources'] = 0
        
        if state['has_errors']:
            response['errors'] = state['error_messages']
        
        return response
    
    def _cleanup_expired_conversations(self):
        """Remove expired conversations"""
        
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, state in self.active_conversations.items():
            last_activity = datetime.fromisoformat(state['last_activity'])
            if current_time - last_activity > timedelta(minutes=self.session_timeout_minutes):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_conversations[session_id]
            self.logger.info(f"Cleaned up expired conversation: {session_id}")
    
    def _generate_conversation_summary(self, state: ConversationState) -> str:
        """Generate a summary of the conversation"""
        
        if not state['messages']:
            return "No conversation content"
        
        user_messages = [msg['content'] for msg in state['messages'] if msg['type'] == MessageType.USER]
        topics = state['topics_discussed']
        
        summary_parts = []
        
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(topics[-5:])}")
        
        if user_messages:
            summary_parts.append(f"Total user messages: {len(user_messages)}")
        
        summary_parts.append(f"Conversation turns: {state['turn_count']}")
        
        return "; ".join(summary_parts)
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get information about active sessions"""
        
        return {
            'active_count': len(self.active_conversations),
            'sessions': [
                {
                    'session_id': session_id,
                    'conversation_id': state['conversation_id'],
                    'turn_count': state['turn_count'],
                    'last_activity': state['last_activity'],
                    'current_phase': state['current_phase'].value
                }
                for session_id, state in self.active_conversations.items()
            ]
        } 