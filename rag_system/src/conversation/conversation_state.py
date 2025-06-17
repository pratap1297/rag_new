"""
Conversation State Management
Defines the state structure for LangGraph conversations
"""
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

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

@dataclass
class Message:
    """Single message in conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.USER
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass 
class SearchResult:
    """Search result with relevance scoring"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationState:
    """Complete conversation state for LangGraph"""
    
    # Core conversation data
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    
    # Current conversation context
    current_phase: ConversationPhase = ConversationPhase.GREETING
    user_intent: Optional[str] = None
    confidence_score: float = 0.0
    
    # Query processing
    original_query: str = ""
    processed_query: str = ""
    query_keywords: List[str] = field(default_factory=list)
    search_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Search and retrieval results
    search_results: List[SearchResult] = field(default_factory=list)
    relevant_sources: List[Dict[str, Any]] = field(default_factory=list)
    context_chunks: List[str] = field(default_factory=list)
    original_search_result: Optional[Dict[str, Any]] = None
    
    # Response generation
    generated_response: str = ""
    response_confidence: float = 0.0
    requires_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)
    
    # Conversation management
    turn_count: int = 0
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    conversation_summary: str = ""
    topics_discussed: List[str] = field(default_factory=list)
    
    # Error handling
    has_errors: bool = False
    error_messages: List[str] = field(default_factory=list)
    retry_count: int = 0
    
    # Follow-up and suggestions
    suggested_questions: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    
    # Metadata
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message_type: MessageType, content: str, metadata: Dict[str, Any] = None) -> Message:
        """Add a new message to the conversation"""
        message = Message(
            type=message_type,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.turn_count += 1
        self.last_activity = datetime.now().isoformat()
        return message
    
    def get_conversation_history(self, max_messages: int = 10) -> List[Message]:
        """Get recent conversation history"""
        return self.messages[-max_messages:] if self.messages else []
    
    def get_context_summary(self) -> str:
        """Get a summary of the conversation context"""
        if not self.messages:
            return "New conversation"
        
        recent_messages = self.get_conversation_history(5)
        user_messages = [msg.content for msg in recent_messages if msg.type == MessageType.USER]
        
        if user_messages:
            return f"Recent topics: {', '.join(self.topics_discussed[-3:])}" if self.topics_discussed else f"Last user message: {user_messages[-1][:100]}"
        
        return "Ongoing conversation"
    
    def should_end_conversation(self) -> bool:
        """Determine if conversation should end"""
        # End conversation criteria
        return (
            self.turn_count > 50 or  # Too many turns
            any("goodbye" in msg.content.lower() or "bye" in msg.content.lower() 
                for msg in self.messages[-2:] if msg.type == MessageType.USER) or
            self.current_phase == ConversationPhase.ENDING
        ) 