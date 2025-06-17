"""
LangGraph Conversation Flow
Defines the conversation flow graph using LangGraph
"""
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .conversation_state import ConversationState, ConversationPhase
from typing_extensions import TypedDict
from .conversation_nodes import ConversationNodes

# Simple state for LangGraph compatibility
class GraphState(TypedDict):
    """Simplified state for LangGraph"""
    conversation_state: ConversationState

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
    
    def _wrap_node(self, node_func):
        """Wrap node function to handle GraphState"""
        def wrapper(state: GraphState) -> GraphState:
            # Extract conversation state
            conversation_state = state.get("conversation_state")
            if not conversation_state:
                # Create new state if missing
                conversation_state = ConversationState()
            
            # Call the node function
            updated_state = node_func(conversation_state)
            
            # Return wrapped state
            return {"conversation_state": updated_state}
        
        return wrapper
    
    def _build_graph(self) -> StateGraph:
        """Build the conversation flow graph"""
        
        # Create the graph with our state schema
        workflow = StateGraph(GraphState)
        
        # Add nodes with wrappers
        workflow.add_node("greet", self._wrap_node(self.nodes.greet_user))
        workflow.add_node("understand", self._wrap_node(self.nodes.understand_intent)) 
        workflow.add_node("search", self._wrap_node(self.nodes.search_knowledge))
        workflow.add_node("respond", self._wrap_node(self.nodes.generate_response))
        workflow.add_node("clarify", self._wrap_node(self.nodes.handle_clarification))
        
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
    
    def _route_after_understanding(self, state: GraphState) -> Literal["search", "respond", "end"]:
        """Route after understanding user intent"""
        
        try:
            conversation_state = state.get("conversation_state")
            if not conversation_state:
                return "respond"
                
            user_intent = getattr(conversation_state, 'user_intent', 'general')
            turn_count = getattr(conversation_state, 'turn_count', 0)
            
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
    
    def _route_after_search(self, state: GraphState) -> Literal["respond", "clarify"]:
        """Route after searching knowledge base"""
        
        try:
            conversation_state = state.get("conversation_state")
            if not conversation_state:
                return "respond"
                
            requires_clarification = getattr(conversation_state, 'requires_clarification', False)
            search_results = getattr(conversation_state, 'search_results', [])
            
            # Only go to clarify if explicitly requested, not just because no results
            if requires_clarification:
                return "clarify"
            else:
                # Always go to respond - let the response generator handle no results case
                return "respond"
        except Exception as e:
            self.logger.error(f"Error in routing after search: {e}")
            return "respond"
    
    def _route_conversation_end(self, state: GraphState) -> Literal["continue", "end"]:
        """Route to determine if conversation should end"""
        
        try:
            conversation_state = state.get("conversation_state")
            if not conversation_state:
                return "end"
                
            current_phase = getattr(conversation_state, 'current_phase', ConversationPhase.UNDERSTANDING)
            user_intent = getattr(conversation_state, 'user_intent', None)
            
            # Only end if explicitly in ending phase or goodbye intent
            if (current_phase == ConversationPhase.ENDING or 
                user_intent == "goodbye" or
                (hasattr(conversation_state, 'should_end_conversation') and conversation_state.should_end_conversation())):
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
                from .conversation_state import MessageType
                state.add_message(MessageType.USER, user_message)
            
            # Wrap state for LangGraph
            graph_state = {"conversation_state": state}
            
            # Run the graph with recursion limit
            result = self.graph.invoke(
                graph_state, 
                config={"recursion_limit": 50}
            )
            
            # Extract conversation state from result
            updated_state = result.get("conversation_state", state)
            
            self.logger.info(f"Conversation processed successfully, phase: {updated_state.current_phase}")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error processing conversation: {e}")
            
            # Handle error gracefully
            from .conversation_state import MessageType
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            state.add_message(MessageType.ASSISTANT, error_response)
            state.has_errors = True
            state.error_messages.append(str(e))
            
            return state 