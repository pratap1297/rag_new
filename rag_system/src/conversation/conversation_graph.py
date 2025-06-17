"""
LangGraph Conversation Flow
Defines the conversation flow graph using LangGraph
"""
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .conversation_state import (
    ConversationState, ConversationPhase, MessageType,
    add_message_to_state
)
from .conversation_nodes import ConversationNodes

class ConversationGraph:
    """LangGraph-based conversation flow manager"""
    
    def __init__(self, container=None):
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # Initialize nodes
        self.nodes = ConversationNodes(container)
        
        # Build graph
        self.graph = self._build_graph()
        
        self.logger.info("ConversationGraph initialized")
    
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
        
        # From respond, end the conversation (don't loop back)
        workflow.add_edge("respond", END)
        
        # From clarify, go back to understand for next turn
        workflow.add_edge("clarify", "understand")
        
        # Compile the graph with recursion limit
        compiled_graph = workflow.compile(
            checkpointer=None,
            interrupt_before=None,
            interrupt_after=None,
            debug=False
        )
        
        self.logger.info("Conversation graph compiled successfully")
        return compiled_graph
    
    def _route_after_understanding(self, state: ConversationState) -> Literal["search", "respond", "end"]:
        """Route after understanding user intent"""
        
        try:
            user_intent = state.get('user_intent', 'general')
            turn_count = state.get('turn_count', 0)
            
            if user_intent == "goodbye":
                return "end"
            elif user_intent in ["greeting", "help"]:
                return "respond"
            elif user_intent == "information_seeking":
                # Always search for information seeking queries
                return "search"
            else:
                return "respond"
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
            
            # Only end if explicitly in ending phase or goodbye intent
            if (current_phase == ConversationPhase.ENDING or 
                user_intent == "goodbye"):
                return "end"
            else:
                return "continue"
        except Exception as e:
            self.logger.error(f"Error in routing conversation end: {e}")
            # Default to continuing conversation on error
            return "continue"
    
    def process_message(self, state: ConversationState, user_message: str) -> ConversationState:
        """Process a user message through the conversation graph"""
        
        try:
            # Add user message to state if it's not empty (for initial greeting)
            if user_message.strip():
                state = add_message_to_state(state, MessageType.USER, user_message)
            
            # Run the graph directly with ConversationState
            result = self.graph.invoke(
                state, 
                config={"recursion_limit": 50}
            )
            
            self.logger.info(f"Conversation processed successfully, phase: {result['current_phase']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing conversation: {e}")
            
            # Handle error gracefully
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            error_state = add_message_to_state(state, MessageType.ASSISTANT, error_response)
            error_state['has_errors'] = True
            error_state['error_messages'] = state.get('error_messages', []) + [str(e)]
            
            return error_state 