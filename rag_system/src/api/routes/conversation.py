"""
Conversation API Routes
FastAPI endpoints for LangGraph conversation management with state persistence
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Create router
router = APIRouter(prefix="/conversation", tags=["Conversation"])
logger = logging.getLogger(__name__)

# Request/Response models
class ConversationStartRequest(BaseModel):
    thread_id: Optional[str] = Field(None, description="Optional thread ID for conversation")
    session_id: Optional[str] = Field(None, description="Deprecated: Use thread_id instead")
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ConversationMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation")
    session_id: Optional[str] = Field(None, description="Deprecated: Use thread_id instead")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ConversationResponse(BaseModel):
    response: str
    thread_id: str
    conversation_id: str
    turn_count: int
    current_phase: str
    confidence_score: float
    timestamp: str
    suggested_questions: Optional[List[str]] = None
    related_topics: Optional[List[str]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    total_sources: Optional[int] = None
    errors: Optional[List[str]] = None

class ConversationHistoryResponse(BaseModel):
    messages: List[Dict[str, Any]]
    thread_id: str
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
    """Start a new conversation using LangGraph state persistence"""
    try:
        if request is None:
            request = ConversationStartRequest()
        
        # Use thread_id if provided, otherwise fall back to session_id for backward compatibility
        thread_id = request.thread_id or request.session_id
        
        response = manager.start_conversation(thread_id)
        
        return {
            "status": "success",
            "message": "Conversation started with LangGraph state persistence",
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
    """Send a message in an existing conversation using LangGraph state persistence"""
    try:
        # Use thread_id if provided, otherwise fall back to session_id for backward compatibility
        thread_id = request.thread_id or request.session_id
        
        if not thread_id:
            raise HTTPException(status_code=400, detail="Either thread_id or session_id must be provided")
        
        response = manager.process_user_message(thread_id, request.message)
        
        # Validate response structure
        if 'error' in response:
            raise HTTPException(status_code=500, detail=response['error'])
        
        return ConversationResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.post("/message/stream")
async def send_message_stream(
    request: ConversationMessageRequest,
    background_tasks: BackgroundTasks,
    manager = Depends(get_conversation_manager)
):
    """Send a message in an existing conversation with streaming response"""
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response for conversation"""
        try:
            # Use thread_id if provided, otherwise fall back to session_id for backward compatibility
            thread_id = request.thread_id or request.session_id
            
            if not thread_id:
                yield f"data: {json.dumps({'error': 'Either thread_id or session_id must be provided'})}\n\n"
                return
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your message...'})}\n\n"
            
            # Process the message (this will be the complete response for now)
            # In the future, we can modify the conversation manager to support streaming
            response = manager.process_user_message(thread_id, request.message)
            
            # Validate response structure
            if 'error' in response:
                yield f"data: {json.dumps({'type': 'error', 'message': response['error']})}\n\n"
                return
            
            # Stream the response in chunks
            full_response = response.get('response', '')
            
            # Send metadata first
            metadata = {
                'type': 'metadata',
                'thread_id': response.get('thread_id', thread_id),
                'conversation_id': response.get('conversation_id', ''),
                'turn_count': response.get('turn_count', 0),
                'current_phase': response.get('current_phase', ''),
                'confidence_score': response.get('confidence_score', 0.0),
                'timestamp': response.get('timestamp', ''),
                'total_sources': response.get('total_sources', 0)
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream the response text in chunks
            chunk_size = 50  # Characters per chunk
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i + chunk_size]
                chunk_data = {
                    'type': 'content',
                    'chunk': chunk,
                    'chunk_index': i // chunk_size,
                    'is_final': i + chunk_size >= len(full_response)
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Add small delay to simulate streaming
                await asyncio.sleep(0.1)
            
            # Send suggestions and related topics
            if response.get('suggested_questions'):
                suggestions_data = {
                    'type': 'suggestions',
                    'suggested_questions': response['suggested_questions']
                }
                yield f"data: {json.dumps(suggestions_data)}\n\n"
            
            if response.get('related_topics'):
                topics_data = {
                    'type': 'topics',
                    'related_topics': response['related_topics']
                }
                yield f"data: {json.dumps(topics_data)}\n\n"
            
            if response.get('sources'):
                sources_data = {
                    'type': 'sources',
                    'sources': response['sources']
                }
                yield f"data: {json.dumps(sources_data)}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except HTTPException as he:
            yield f"data: {json.dumps({'type': 'error', 'message': str(he.detail)})}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming message: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to process message: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/history/{thread_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    thread_id: str,
    max_messages: int = 20,
    manager = Depends(get_conversation_manager)
):
    """Get conversation history for a thread using LangGraph state persistence"""
    try:
        history = manager.get_conversation_history(thread_id, max_messages)
        
        if 'error' in history:
            raise HTTPException(status_code=500, detail=history['error'])
        
        return ConversationHistoryResponse(**history)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

# Backward compatibility endpoint
@router.get("/history/session/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history_by_session(
    session_id: str,
    max_messages: int = 20,
    manager = Depends(get_conversation_manager)
):
    """Get conversation history by session_id (deprecated - use thread_id instead)"""
    logger.warning(f"Using deprecated session-based history endpoint for {session_id}")
    return await get_conversation_history(session_id, max_messages, manager)

@router.post("/end/{thread_id}")
async def end_conversation(
    thread_id: str,
    manager = Depends(get_conversation_manager)
):
    """End a conversation using LangGraph state persistence"""
    try:
        result = manager.end_conversation(thread_id)
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        logger.error(f"Error ending conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

# Backward compatibility endpoint
@router.post("/end/session/{session_id}")
async def end_conversation_by_session(
    session_id: str,
    manager = Depends(get_conversation_manager)
):
    """End a conversation by session_id (deprecated - use thread_id instead)"""
    logger.warning(f"Using deprecated session-based end endpoint for {session_id}")
    return await end_conversation(session_id, manager)

@router.get("/threads")
async def get_active_conversations(
    manager = Depends(get_conversation_manager)
):
    """Get information about active conversation threads"""
    try:
        conversations_info = manager.list_active_conversations()
        return {
            "status": "success",
            **conversations_info
        }
        
    except Exception as e:
        logger.error(f"Error getting active conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/sessions")
async def get_active_sessions(
    manager = Depends(get_conversation_manager)
):
    """Get information about active sessions (deprecated - use /threads instead)"""
    logger.warning("Using deprecated sessions endpoint - use /threads instead")
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
        
        # Check if LangGraph state persistence is working
        state_persistence_status = "enabled"
        try:
            # Try to access the checkpointer
            if hasattr(manager.conversation_graph, 'checkpointer') and manager.conversation_graph.checkpointer:
                state_persistence_status = "enabled"
            else:
                state_persistence_status = "disabled"
        except Exception as e:
            logger.error(f"Error checking state persistence status: {e}")
            state_persistence_status = "error"
        
        return {
            "status": "healthy",
            "service": "conversation",
            "langgraph_available": True,
            "state_persistence": state_persistence_status,
            "checkpointer_type": "MemorySaver",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        from datetime import datetime
        return {
            "status": "unhealthy",
            "service": "conversation", 
            "error": str(e),
            "langgraph_available": False,
            "state_persistence": "error",
            "timestamp": datetime.now().isoformat()
        } 