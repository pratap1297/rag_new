"""
LangGraph Conversation Flow
Defines the conversation flow graph using LangGraph
"""
import logging
from typing import Dict, Any, Literal, List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
import os

from .conversation_state import (
    ConversationState, ConversationPhase, MessageType,
    add_message_to_state, _apply_memory_management
)
from .conversation_nodes import ConversationNodes

class ConversationGraph:
    """LangGraph-based conversation flow manager"""
    
    def __init__(self, container=None, db_path: str = None):
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # Initialize nodes
        self.nodes = ConversationNodes(container)
        
        # Set up checkpointer for state persistence
        if db_path is None:
            # Default to data directory
            data_dir = os.path.join(os.path.dirname(__file__), "../../../data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "conversations.db")
        
        self.checkpointer = MemorySaver()
        self.logger.info(f"Initialized Memory checkpointer for state persistence")
        
        # Build graph
        self.graph = self._build_graph()
        
        self.logger.info("ConversationGraph initialized with state persistence")
    
    def _build_graph(self) -> StateGraph:
        """Build the conversation flow graph"""
        
        # Create the graph using ConversationState directly
        workflow = StateGraph(ConversationState)
        
        # Add nodes directly without wrappers
        workflow.add_node("greet", self.nodes.greet_user)
        workflow.add_node("understand", self.nodes.understand_intent) 
        workflow.add_node("search", self.nodes.search_knowledge)
        workflow.add_node("respond", self.nodes.generate_response)
        workflow.add_node("clarify", self.nodes.handle_clarification)
        
        # Define the flow logic
        workflow.set_entry_point("greet")
        
        # From greet, go to understand
        workflow.add_edge("greet", "understand")
        
        # From understand, route based on intent
        workflow.add_conditional_edges(
            "understand",
            self._route_after_understanding,
            {
                "search": "search",
                "respond": "respond", 
                "end": END
            }
        )
        
        # From search, route based on results
        workflow.add_conditional_edges(
            "search",
            self._route_after_search,
            {
                "respond": "respond",
                "clarify": "clarify"
            }
        )
        
        # From respond, conditionally end or continue the conversation
        workflow.add_conditional_edges(
            "respond",
            self._route_conversation_end,
            {
                "continue": "understand",
                "end": END
            }
        )
        
        # From clarify, go back to understand for next turn
        workflow.add_edge("clarify", "understand")
        
        # Compile the graph with Memory checkpointer for state persistence
        compiled_graph = workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=None,
            interrupt_after=None,
            debug=False
        )
        
        self.logger.info("Conversation graph compiled successfully with Memory state persistence")
        return compiled_graph
    
    def _route_after_understanding(self, state: ConversationState) -> Literal["search", "respond", "end"]:
        """Route after understanding user intent"""
        
        try:
            user_intent = state.get('user_intent', 'general')
            turn_count = state.get('turn_count', 0)
            
            self.logger.info(f"Routing after understanding - intent: {user_intent}, turn: {turn_count}")
            
            # Check if this is a goodbye message
            if user_intent == "goodbye":
                return "end"
                
            # For greetings and help, go directly to respond
            elif user_intent in ["greeting", "help"]:
                return "respond"
                
            # For information seeking or any query that might need knowledge retrieval
            elif user_intent in ["information_seeking", "question", "search", "explanation"]:
                return "search"
                
            # For follow-up questions, always search to maintain context
            elif user_intent == "follow_up" or state.get('is_contextual', False):
                return "search"
                
            # Default to search for most intents to provide knowledge-based responses
            else:
                return "search"
                
        except Exception as e:
            self.logger.error(f"Error in routing after understanding: {e}")
            return "respond"
    
    def _route_after_search(self, state: ConversationState) -> Literal["respond", "clarify"]:
        """Route after searching knowledge base"""
        
        try:
            requires_clarification = state.get('requires_clarification', False)
            search_results = state.get('search_results', [])
            
            # Only go to clarify if explicitly requested, not just because no results
            if requires_clarification:
                return "clarify"
            else:
                # Always go to respond - let the response generator handle no results case
                return "respond"
        except Exception as e:
            self.logger.error(f"Error in routing after search: {e}")
            return "respond"
    
    def _route_conversation_end(self, state: ConversationState) -> Literal["continue", "end"]:
        """Route to determine if conversation should end"""
        
        try:
            current_phase = state.get('current_phase', ConversationPhase.UNDERSTANDING)
            user_intent = state.get('user_intent', None)
            turn_count = state.get('turn_count', 0)
            
            # End conversation if:
            # 1. Explicitly in ending phase or goodbye intent
            # 2. Too many turns (to prevent infinite loops)
            # 3. Error count is too high
            # 4. Single-turn question has been answered (for API calls)
            if (current_phase == ConversationPhase.ENDING or 
                user_intent == "goodbye" or
                turn_count > 20 or  # Limit total turns to prevent loops
                state.get('retry_count', 0) > 3 or  # Too many retries
                len(state.get('error_messages', [])) > 5 or  # Too many errors
                current_phase == ConversationPhase.RESPONDING):  # End after response is generated
                
                self.logger.info(f"Ending conversation: phase={current_phase}, intent={user_intent}, turns={turn_count}")
                return "end"
            else:
                return "continue"
        except Exception as e:
            self.logger.error(f"Error in routing conversation end: {e}")
            # Default to ending conversation on error to prevent loops
            return "end"
    
    def process_message(self, thread_id: str, user_message: str, config: Dict[str, Any] = None) -> ConversationState:
        """Process a user message through the conversation graph using LangGraph state management"""
        
        try:
            # Create config with thread_id for LangGraph state management
            if config is None:
                config = {}
            config["configurable"] = {"thread_id": thread_id}
            # Set recursion limit to prevent infinite loops
            config["recursion_limit"] = 100
            
            # Get current state from checkpointer or create new one
            current_state = self._get_or_create_state(thread_id)
            
            # Add user message to state if it's not empty (for initial greeting)
            if user_message.strip():
                current_state = add_message_to_state(current_state, MessageType.USER, user_message)
            
            # Run the graph with LangGraph state management
            result = self.graph.invoke(
                current_state, 
                config=config
            )
            
            # Apply memory management to prevent leaks
            result = _apply_memory_management(result)
            
            # Safely access current_phase with a default value if it doesn't exist
            current_phase = result.get('current_phase', 'UNKNOWN')
            self.logger.info(f"Conversation processed successfully for thread {thread_id}, phase: {current_phase}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing conversation: {e}")
            
            # Handle error gracefully
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            
            # Try to get current state for error handling
            try:
                current_state = self._get_or_create_state(thread_id)
            except:
                # If we can't get state, create a minimal one
                from .conversation_state import create_conversation_state
                current_state = create_conversation_state(thread_id)
            
            error_state = add_message_to_state(current_state, MessageType.ASSISTANT, error_response)
            error_state['has_errors'] = True
            error_state['error_messages'] = current_state.get('error_messages', []) + [str(e)]
            
            # Apply memory management to error state as well
            error_state = _apply_memory_management(error_state)
            
            return error_state
    
    def _get_or_create_state(self, thread_id: str) -> ConversationState:
        """Get existing state from checkpointer or create new conversation state"""
        
        try:
            # Try to get existing state from checkpointer
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = self.checkpointer.get_tuple(config)
            
            if checkpoint and checkpoint.checkpoint:
                # Return existing state
                state = checkpoint.checkpoint.get("channel_values", {})
                if state:
                    self.logger.info(f"Retrieved existing conversation state for thread {thread_id}")
                    return state
            
            # Create new state if none exists
            from .conversation_state import create_conversation_state
            new_state = create_conversation_state(thread_id)
            self.logger.info(f"Created new conversation state for thread {thread_id}")
            return new_state
            
        except Exception as e:
            self.logger.error(f"Error getting/creating state for thread {thread_id}: {e}")
            # Fallback to creating new state
            from .conversation_state import create_conversation_state
            return create_conversation_state(thread_id)
    
    def get_conversation_history(self, thread_id: str, max_messages: int = 20) -> Dict[str, Any]:
        """Get conversation history for a thread using LangGraph state"""
        
        try:
            state = self._get_or_create_state(thread_id)
            
            messages = state.get('messages', [])[-max_messages:] if state.get('messages') else []
            
            return {
                'messages': [
                    {
                        'type': msg['type'].value if hasattr(msg['type'], 'value') else str(msg['type']),
                        'content': msg['content'],
                        'timestamp': msg['timestamp'],
                        'metadata': msg['metadata']
                    }
                    for msg in messages
                ],
                'thread_id': thread_id,
                'conversation_id': state.get('conversation_id', ''),
                'turn_count': state.get('turn_count', 0),
                'current_phase': state.get('current_phase', ConversationPhase.UNDERSTANDING).value if hasattr(state.get('current_phase'), 'value') else str(state.get('current_phase', 'understanding')),
                'topics_discussed': state.get('topics_discussed', [])
            }
        except Exception as e:
            self.logger.error(f"Error getting conversation history for thread {thread_id}: {e}")
            return {
                'messages': [],
                'thread_id': thread_id,
                'conversation_id': '',
                'turn_count': 0,
                'current_phase': 'understanding',
                'topics_discussed': []
            }
    
    def list_conversation_threads(self) -> List[str]:
        """List all conversation threads stored in checkpointer"""
        
        try:
            # Get all stored threads from checkpointer
            if not self.checkpointer or not hasattr(self.checkpointer, 'client'):
                self.logger.warning("Checkpointer not available or missing client attribute")
                return []
                
            # Try to access the SQLite database directly
            try:
                # This assumes SQLiteSaver is being used
                conn = self.checkpointer.client.conn
                cursor = conn.cursor()
                
                # Query for unique thread_ids in the configurable column
                cursor.execute("SELECT DISTINCT json_extract(configurable, '$.thread_id') FROM checkpoints")
                thread_ids = [row[0] for row in cursor.fetchall() if row[0]]
                
                self.logger.info(f"Found {len(thread_ids)} conversation threads in database")
                return thread_ids
                
            except Exception as db_error:
                self.logger.error(f"Database query error: {db_error}")
                # Fallback to empty list if database query fails
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing conversation threads: {e}")
            return []