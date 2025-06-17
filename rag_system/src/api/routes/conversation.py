"""
Conversation API Routes
FastAPI endpoints for LangGraph conversation management
"""
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

# Create router
router = APIRouter(prefix="/conversation", tags=["Conversation"])
logger = logging.getLogger(__name__)

# Request/Response models
class ConversationStartRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Optional session ID")
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ConversationMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., description="Session ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ConversationResponse(BaseModel):
    response: str
    session_id: str
    conversation_id: str
    turn_count: int
    current_phase: str
    confidence_score: float
    timestamp: str
    suggested_questions: Optional[List[str]] = None
    related_topics: Optional[List[str]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[str]] = None

class ConversationHistoryResponse(BaseModel):
    messages: List[Dict[str, Any]]
    session_id: str
    conversation_id: str
    turn_count: int
    current_phase: str
    topics_discussed: List[str]

# Global conversation manager - will be set by the container
conversation_manager = None

def get_conversation_manager():
    """Get conversation manager from container"""
    global conversation_manager
    if conversation_manager is None:
        try:
            # Try to get it from the dependency container
            from ...core.dependency_container import get_dependency_container
            container = get_dependency_container()
            conversation_manager = container.get('conversation_manager')
            
            if conversation_manager is None:
                logger.warning("ConversationManager not available in container")
                raise HTTPException(status_code=503, detail="Conversation service not available")
            
            logger.info("ConversationManager initialized from container")
        except Exception as e:
            logger.error(f"Failed to get ConversationManager: {e}")
            raise HTTPException(status_code=503, detail="Conversation service unavailable")
    
    return conversation_manager

@router.post("/start", response_model=Dict[str, Any])
async def start_conversation(
    request: ConversationStartRequest = None,
    manager = Depends(get_conversation_manager)
):
    """Start a new conversation"""
    try:
        if request is None:
            request = ConversationStartRequest()
        
        state = manager.start_conversation(request.session_id)
        
        # Apply user preferences if provided
        if request.user_preferences:
            state.user_preferences.update(request.user_preferences)
        
        # Get the initial greeting response
        response = manager._format_response(state)
        
        return {
            "status": "success",
            "message": "Conversation started",
            **response
        }
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/message", response_model=ConversationResponse)
async def send_message(
    request: ConversationMessageRequest,
    background_tasks: BackgroundTasks,
    manager = Depends(get_conversation_manager)
):
    """Send a message in an existing conversation"""
    try:
        response = manager.process_user_message(request.session_id, request.message)
        
        # Validate response structure
        if 'error' in response:
            raise HTTPException(status_code=500, detail=response['error'])
        
        return ConversationResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    max_messages: int = 20,
    manager = Depends(get_conversation_manager)
):
    """Get conversation history for a session"""
    try:
        history = manager.get_conversation_history(session_id, max_messages)
        return ConversationHistoryResponse(**history)
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.post("/end/{session_id}")
async def end_conversation(
    session_id: str,
    manager = Depends(get_conversation_manager)
):
    """End a conversation"""
    try:
        result = manager.end_conversation(session_id)
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        logger.error(f"Error ending conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

@router.get("/sessions")
async def get_active_sessions(
    manager = Depends(get_conversation_manager)
):
    """Get information about active conversation sessions"""
    try:
        sessions_info = manager.get_active_sessions()
        return {
            "status": "success",
            **sessions_info
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.get("/health")
async def conversation_health_check():
    """Health check for conversation service"""
    try:
        manager = get_conversation_manager()
        from datetime import datetime
        return {
            "status": "healthy",
            "service": "conversation",
            "langgraph_available": True,
            "active_conversations": len(manager.active_conversations) if manager else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        from datetime import datetime
        return {
            "status": "unhealthy",
            "service": "conversation", 
            "error": str(e),
            "langgraph_available": False,
            "timestamp": datetime.now().isoformat()
        } 