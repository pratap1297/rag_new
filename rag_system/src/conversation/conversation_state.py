"""
Conversation State Management
Defines the state structure for LangGraph conversations
"""
from typing import Dict, List, Any, Optional, Literal
from typing_extensions import TypedDict
from datetime import datetime
from enum import Enum
import uuid

# Memory management constants
MAX_CONVERSATION_HISTORY = 20  # Maximum number of messages to keep in history
MAX_TOPICS_DISCUSSED = 10      # Maximum number of topics to track
MAX_ERROR_MESSAGES = 5         # Maximum number of error messages to keep
MAX_SUGGESTED_QUESTIONS = 5    # Maximum number of suggested questions to keep
MAX_RELATED_TOPICS = 5         # Maximum number of related topics to keep

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ConversationPhase(Enum):
    GREETING = "greeting"
    UNDERSTANDING = "understanding"
    SEARCHING = "searching"
    RESPONDING = "responding"
    CLARIFYING = "clarifying"
    FOLLOW_UP = "follow_up"
    ENDING = "ending"

class Message(TypedDict):
    """Single message in conversation"""
    id: str
    type: MessageType
    content: str
    metadata: Dict[str, Any]
    timestamp: str

class SearchResult(TypedDict):
    """Search result with relevance scoring"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]

class ConversationState(TypedDict):
    """Complete conversation state for LangGraph"""
    
    # Core conversation data
    conversation_id: str
    session_id: str
    messages: List[Message]
    
    # Current conversation context
    current_phase: ConversationPhase
    user_intent: Optional[str]
    confidence_score: float
    
    # Query processing
    original_query: str
    processed_query: str
    query_keywords: List[str]
    search_filters: Dict[str, Any]
    is_contextual: bool  # Added to track contextual queries
    
    # Topic tracking
    current_topic: Optional[str]  # Added for topic tracking
    topic_entities: List[str]  # Added for entity tracking
    
    # Search and retrieval results
    search_results: List[SearchResult]
    relevant_sources: List[Dict[str, Any]]
    context_chunks: List[str]
    original_search_result: Optional[Dict[str, Any]]
    
    # Response generation
    generated_response: str
    query_engine_response: str
    response_confidence: float
    requires_clarification: bool
    clarification_questions: List[str]
    
    # Conversation management
    turn_count: int
    last_activity: str
    conversation_summary: str
    topics_discussed: List[str]
    
    # Error handling
    has_errors: bool
    error_messages: List[str]
    retry_count: int
    
    # Follow-up and suggestions
    suggested_questions: List[str]
    related_topics: List[str]
    
    # Metadata
    user_preferences: Dict[str, Any]
    conversation_metadata: Dict[str, Any]

def create_conversation_state(thread_id: Optional[str] = None) -> ConversationState:
    """Create a new conversation state with default values"""
    return ConversationState(
        # Core conversation data
        conversation_id=str(uuid.uuid4()),
        session_id=thread_id or str(uuid.uuid4()),
        messages=[],
        
        # Current conversation context
        current_phase=ConversationPhase.GREETING,
        user_intent=None,
        confidence_score=0.0,
        
        # Query processing
        original_query="",
        processed_query="",
        query_keywords=[],
        search_filters={},
        is_contextual=False,
        
        # Topic tracking
        current_topic=None,
        topic_entities=[],
        
        # Search and retrieval results
        search_results=[],
        relevant_sources=[],
        context_chunks=[],
        original_search_result=None,
        
        # Response generation
        generated_response="",
        query_engine_response="",
        response_confidence=0.0,
        requires_clarification=False,
        clarification_questions=[],
        
        # Conversation management
        turn_count=0,
        last_activity=datetime.now().isoformat(),
        conversation_summary="",
        topics_discussed=[],
        
        # Error handling
        has_errors=False,
        error_messages=[],
        retry_count=0,
        
        # Follow-up and suggestions
        suggested_questions=[],
        related_topics=[],
        
        # Metadata
        user_preferences={},
        conversation_metadata={}
    )

def add_message_to_state(state: ConversationState, message_type: MessageType, content: str, metadata: Dict[str, Any] = None) -> ConversationState:
    """Add a new message to the conversation state with memory management"""
    message = Message(
        id=str(uuid.uuid4()),
        type=message_type,
        content=content,
        metadata=metadata or {},
        timestamp=datetime.now().isoformat()
    )
    
    # Create a new state with updated values
    new_state = state.copy()
    
    # Add message and limit history size
    new_state['messages'] = state['messages'][-MAX_CONVERSATION_HISTORY+1:] + [message]
    new_state['turn_count'] = state['turn_count'] + 1
    new_state['last_activity'] = datetime.now().isoformat()
    
    # Apply memory management to prevent leaks
    new_state = _apply_memory_management(new_state)
    
    return new_state

def _apply_memory_management(state: ConversationState) -> ConversationState:
    """Apply memory management to limit growing lists in conversation state"""
    managed_state = state.copy()
    
    # Limit topics discussed
    if 'topics_discussed' in managed_state and len(managed_state['topics_discussed']) > MAX_TOPICS_DISCUSSED:
        managed_state['topics_discussed'] = managed_state['topics_discussed'][-MAX_TOPICS_DISCUSSED:]
    
    # Limit error messages
    if 'error_messages' in managed_state and len(managed_state['error_messages']) > MAX_ERROR_MESSAGES:
        managed_state['error_messages'] = managed_state['error_messages'][-MAX_ERROR_MESSAGES:]
    
    # Limit suggested questions
    if 'suggested_questions' in managed_state and len(managed_state['suggested_questions']) > MAX_SUGGESTED_QUESTIONS:
        managed_state['suggested_questions'] = managed_state['suggested_questions'][-MAX_SUGGESTED_QUESTIONS:]
    
    # Limit related topics
    if 'related_topics' in managed_state and len(managed_state['related_topics']) > MAX_RELATED_TOPICS:
        managed_state['related_topics'] = managed_state['related_topics'][-MAX_RELATED_TOPICS:]
    
    # Limit search results (keep only top results)
    if 'search_results' in managed_state and len(managed_state['search_results']) > 10:
        managed_state['search_results'] = managed_state['search_results'][:10]
    
    # Limit context chunks
    if 'context_chunks' in managed_state and len(managed_state['context_chunks']) > 10:
        managed_state['context_chunks'] = managed_state['context_chunks'][:10]
    
    return managed_state

def get_conversation_history(state: ConversationState, max_messages: int = 10) -> List[Message]:
    """Get recent conversation history"""
    return state['messages'][-max_messages:] if state['messages'] else []

def get_context_summary(state: ConversationState) -> str:
    """Get a summary of the conversation context"""
    if not state['messages']:
        return "New conversation"
    
    recent_messages = get_conversation_history(state, 5)
    user_messages = [msg['content'] for msg in recent_messages if msg['type'] == MessageType.USER]
    
    if user_messages:
        topics = state['topics_discussed']
        return f"Recent topics: {', '.join(topics[-3:])}" if topics else f"Last user message: {user_messages[-1][:100]}"
    
    return "Ongoing conversation"

def should_end_conversation(state: ConversationState) -> bool:
    """Determine if conversation should end"""
    # End conversation criteria
    return (
        state['turn_count'] > 50 or  # Too many turns
        any("goodbye" in msg['content'].lower() or "bye" in msg['content'].lower() 
            for msg in state['messages'][-2:] if msg['type'] == MessageType.USER) or
        state['current_phase'] == ConversationPhase.ENDING
    )