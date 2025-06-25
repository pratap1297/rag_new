"""
Verification API Endpoints
Provides real-time verification monitoring and testing capabilities
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from ..core.pipeline_verifier import PipelineVerifier, PipelineStage, VerificationStatus
    from ..core.verified_ingestion_engine import VerifiedIngestionEngine
    from ..core.dependency_container import get_dependency_container
except ImportError:
    from rag_system.src.core.pipeline_verifier import PipelineVerifier, PipelineStage, VerificationStatus
    from rag_system.src.core.verified_ingestion_engine import VerifiedIngestionEngine
    from rag_system.src.core.dependency_container import get_dependency_container

# Router for verification endpoints
router = APIRouter(prefix="/api/verification", tags=["verification"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Active verification sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

# Request/Response models
class FileValidationRequest(BaseModel):
    file_path: str

class TestExtractionRequest(BaseModel):
    file_path: str

class TestChunkingRequest(BaseModel):
    text: str
    method: str = "semantic"

class TestEmbeddingRequest(BaseModel):
    text: str

class VerifiedIngestionRequest(BaseModel):
    file_path: str
    metadata: Optional[Dict[str, Any]] = None

class AnalyzeChunksRequest(BaseModel):
    file_id: str

class SimilarityTestRequest(BaseModel):
    query_text: str
    vector_id: int

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for connection testing
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# File validation endpoint
@router.post("/validate-file")
async def validate_file(request: FileValidationRequest):
    """Validate a file before processing"""
    try:
        verifier = PipelineVerifier()
        valid, results = verifier.verify_file_input(request.file_path)
        
        file_path = Path(request.file_path)
        file_info = {
            "path": request.file_path,
            "exists": file_path.exists(),
            "size_mb": file_path.stat().st_size / 1024 / 1024 if file_path.exists() else 0,
            "extension": file_path.suffix.lower() if file_path.exists() else None
        }
        
        return {
            "valid": valid,
            "checks": [r.to_dict() for r in results],
            "file_info": file_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File validation failed: {str(e)}")

# Test content extraction
@router.post("/test-extraction")
async def test_extraction(request: TestExtractionRequest):
    """Test content extraction without full ingestion"""
    try:
        container = get_dependency_container()
        ingestion_engine = container.get('ingestion_engine')
        
        if not ingestion_engine:
            raise HTTPException(status_code=500, detail="Ingestion engine not available")
        
        processor = ingestion_engine.processor_registry.get_processor(request.file_path)
        
        if not processor:
            return {
                "error": "No processor found for file type",
                "file_path": request.file_path,
                "file_extension": Path(request.file_path).suffix.lower()
            }
        
        result = processor.process(request.file_path)
        
        return {
            "processor": processor.__class__.__name__,
            "status": result.get("status"),
            "sheets": len(result.get("sheets", [])),
            "chunks": len(result.get("chunks", [])),
            "embedded_objects": len(result.get("embedded_objects", [])),
            "sample_chunk": result.get("chunks", [])[0] if result.get("chunks") else None,
            "file_path": request.file_path,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content extraction test failed: {str(e)}")

# Test chunking
@router.post("/test-chunking")
async def test_chunking(request: TestChunkingRequest):
    """Test text chunking with different methods"""
    try:
        container = get_dependency_container()
        
        if request.method == "semantic":
            try:
                from ..ingestion.semantic_chunker import SemanticChunker
            except ImportError:
                from rag_system.src.ingestion.semantic_chunker import SemanticChunker
            chunker = SemanticChunker()
        else:
            chunker = container.get('chunker')
        
        if not chunker:
            raise HTTPException(status_code=500, detail="Chunker not available")
        
        chunks = chunker.chunk_text(request.text)
        
        return {
            "method": request.method,
            "chunk_count": len(chunks),
            "chunk_sizes": [len(c.get("text", "")) for c in chunks],
            "avg_size": sum(len(c.get("text", "")) for c in chunks) / len(chunks) if chunks else 0,
            "chunks": chunks[:3],  # First 3 chunks as sample
            "text_length": len(request.text),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunking test failed: {str(e)}")

# Test embedding generation
@router.post("/test-embedding")
async def test_embedding(request: TestEmbeddingRequest):
    """Test embedding generation for a text sample"""
    try:
        container = get_dependency_container()
        embedder = container.get('embedder')
        
        if not embedder:
            raise HTTPException(status_code=500, detail="Embedder not available")
        
        embedding = embedder.embed_text(request.text)
        
        return {
            "text_length": len(request.text),
            "embedding_dimension": len(embedding),
            "embedding_sample": embedding[:10],  # First 10 values
            "stats": {
                "min": min(embedding),
                "max": max(embedding),
                "mean": sum(embedding) / len(embedding)
            },
            "text_preview": request.text[:100],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding test failed: {str(e)}")

# Verify specific vector in FAISS
@router.get("/verify-vectors/{vector_id}")
async def verify_vector(vector_id: int):
    """Verify a specific vector in FAISS"""
    try:
        container = get_dependency_container()
        faiss_store = container.get('faiss_store')
        embedder = container.get('embedder')
        
        if not faiss_store:
            raise HTTPException(status_code=500, detail="FAISS store not available")
        
        metadata = faiss_store.get_vector_metadata(vector_id)
        
        if not metadata:
            return {
                "error": "Vector not found",
                "vector_id": vector_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Test retrieval
        sample_query = metadata.get("text", "")[:100]
        similarity_test = None
        
        if sample_query and embedder:
            try:
                query_embedding = embedder.embed_text(sample_query)
                results = faiss_store.search(query_embedding, k=5)
                
                similarity_test = {
                    "query": sample_query,
                    "top_result_similarity": results[0]["similarity_score"] if results else 0,
                    "found_in_top_5": any(r.get("doc_id") == str(vector_id) for r in results)
                }
            except Exception as e:
                similarity_test = {"error": str(e)}
        
        return {
            "vector_id": vector_id,
            "metadata": metadata,
            "retrievable": True,
            "similarity_test": similarity_test,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector verification failed: {str(e)}")

# Background task for verified ingestion
async def run_verified_ingestion(session_id: str, file_path: str, metadata: Optional[Dict[str, Any]]):
    """Run verified ingestion in background"""
    try:
        container = get_dependency_container()
        ingestion_engine = container.get('ingestion_engine')
        
        # Create verifier with callback for real-time updates
        verifier = PipelineVerifier(debug_mode=True, save_intermediate=True)
        
        def verification_callback(event):
            # Update session status
            if session_id in active_sessions:
                active_sessions[session_id]["current_stage"] = event.get("data", {}).get("stage")
                active_sessions[session_id]["last_event"] = event
            
            # Broadcast to WebSocket connections
            asyncio.create_task(manager.broadcast({
                "session_id": session_id,
                "event": event
            }))
        
        verifier.add_event_callback(verification_callback)
        
        # Create verified engine
        verified_engine = VerifiedIngestionEngine(ingestion_engine, verifier)
        
        # Run ingestion
        result = verified_engine.ingest_file_with_verification(file_path, metadata)
        
        # Update session with results
        active_sessions[session_id].update({
            "status": "completed" if result["success"] else "failed",
            "result": result,
            "end_time": datetime.now().isoformat()
        })
        
        # Broadcast completion
        await manager.broadcast({
            "session_id": session_id,
            "event": {
                "type": "ingestion_completed",
                "data": {
                    "success": result["success"],
                    "file_path": file_path
                }
            }
        })
        
    except Exception as e:
        # Update session with error
        active_sessions[session_id].update({
            "status": "error",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
        
        # Broadcast error
        await manager.broadcast({
            "session_id": session_id,
            "event": {
                "type": "ingestion_error",
                "data": {
                    "error": str(e),
                    "file_path": file_path
                }
            }
        })

# Verified ingestion with real-time monitoring
@router.post("/ingest-with-verification")
async def ingest_with_verification(request: VerifiedIngestionRequest, background_tasks: BackgroundTasks):
    """Ingest file with comprehensive verification and real-time updates"""
    # Create session
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "session_id": session_id,
        "file_path": request.file_path,
        "metadata": request.metadata,
        "status": "started",
        "start_time": datetime.now().isoformat(),
        "current_stage": None,
        "last_event": None
    }
    
    # Start background task
    background_tasks.add_task(run_verified_ingestion, session_id, request.file_path, request.metadata)
    
    return {
        "session_id": session_id,
        "status": "started",
        "message": "Verification ingestion started",
        "websocket_url": "/api/verification/ws"
    }

# Get session status
@router.get("/session/{session_id}")
async def get_session_status(session_id: str):
    """Get status of a verification session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]

# List all active sessions
@router.get("/sessions")
async def list_sessions():
    """List all active verification sessions"""
    return {
        "sessions": list(active_sessions.values()),
        "count": len(active_sessions)
    }

# Analyze chunks for a file
@router.post("/analyze-chunks")
async def analyze_chunks(request: AnalyzeChunksRequest):
    """Analyze chunks for a specific file"""
    try:
        container = get_dependency_container()
        metadata_store = container.get('metadata_store')
        
        if not metadata_store:
            raise HTTPException(status_code=500, detail="Metadata store not available")
        
        # Get file chunks
        try:
            chunks = metadata_store.get_file_chunks(request.file_id)
        except:
            # Try alternative method
            file_metadata = metadata_store.get_file_metadata(request.file_id)
            if not file_metadata:
                raise HTTPException(status_code=404, detail="File not found")
            chunks = []
        
        if not chunks:
            return {
                "file_id": request.file_id,
                "error": "No chunks found for this file",
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze chunk sizes
        sizes = [len(chunk.get('text', '')) for chunk in chunks]
        
        # Check for empty chunks
        empty_chunks = [i for i, size in enumerate(sizes) if size == 0]
        
        # Analyze overlap (simple approach)
        overlaps = []
        for i in range(len(chunks) - 1):
            text1 = chunks[i].get('text', '')
            text2 = chunks[i + 1].get('text', '')
            
            # Simple overlap detection
            for j in range(min(200, len(text1))):
                if text1[-(j+1):] == text2[:j+1]:
                    overlaps.append(j+1)
                    break
        
        return {
            "file_id": request.file_id,
            "total_chunks": len(chunks),
            "chunk_size_stats": {
                "min": min(sizes) if sizes else 0,
                "max": max(sizes) if sizes else 0,
                "avg": sum(sizes) / len(sizes) if sizes else 0,
                "total_chars": sum(sizes)
            },
            "empty_chunks": {
                "count": len(empty_chunks),
                "indices": empty_chunks
            },
            "overlap_analysis": {
                "avg_overlap": sum(overlaps) / len(overlaps) if overlaps else 0,
                "max_overlap": max(overlaps) if overlaps else 0,
                "overlapping_pairs": len(overlaps)
            },
            "sample_chunks": chunks[:3],  # First 3 chunks
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunk analysis failed: {str(e)}")

# Test similarity between query and vector
@router.post("/test-similarity")
async def test_similarity(request: SimilarityTestRequest):
    """Test similarity between a query and specific vector"""
    try:
        container = get_dependency_container()
        faiss_store = container.get('faiss_store')
        embedder = container.get('embedder')
        
        if not faiss_store or not embedder:
            raise HTTPException(status_code=500, detail="FAISS store or embedder not available")
        
        # Get vector metadata
        vector_metadata = faiss_store.get_vector_metadata(request.vector_id)
        if not vector_metadata:
            raise HTTPException(status_code=404, detail="Vector not found")
        
        # Generate query embedding
        query_embedding = embedder.embed_text(request.query_text)
        
        # Search for similar vectors
        results = faiss_store.search(query_embedding, k=10)
        
        # Find the specific vector in results
        target_result = None
        for i, result in enumerate(results):
            if result.get("doc_id") == str(request.vector_id):
                target_result = {
                    "rank": i + 1,
                    "similarity_score": result.get("similarity_score", 0),
                    "found": True
                }
                break
        
        if not target_result:
            target_result = {"found": False, "rank": None, "similarity_score": None}
        
        return {
            "query_text": request.query_text,
            "vector_id": request.vector_id,
            "vector_text": vector_metadata.get("text", "")[:200],
            "target_result": target_result,
            "top_results": results[:5],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity test failed: {str(e)}")

# Performance statistics
@router.get("/performance-stats")
async def get_performance_stats():
    """Get performance statistics for recent verifications"""
    try:
        # Calculate stats from active sessions
        completed_sessions = [s for s in active_sessions.values() if s.get("status") == "completed"]
        failed_sessions = [s for s in active_sessions.values() if s.get("status") == "failed"]
        
        stats = {
            "total_sessions": len(active_sessions),
            "completed_sessions": len(completed_sessions),
            "failed_sessions": len(failed_sessions),
            "success_rate": len(completed_sessions) / len(active_sessions) if active_sessions else 0,
            "recent_activity": list(active_sessions.values())[-10:],  # Last 10 sessions
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

# Debug file access
@router.get("/debug/file-access/{file_path:path}")
async def debug_file_access(file_path: str):
    """Debug file access issues"""
    try:
        file_obj = Path(file_path)
        
        return {
            "file_path": file_path,
            "exists": file_obj.exists(),
            "is_file": file_obj.is_file() if file_obj.exists() else False,
            "is_readable": file_obj.is_file() and file_obj.stat().st_size > 0 if file_obj.exists() else False,
            "size_bytes": file_obj.stat().st_size if file_obj.exists() else 0,
            "extension": file_obj.suffix.lower(),
            "parent_exists": file_obj.parent.exists(),
            "absolute_path": str(file_obj.absolute()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Health check for verification system
@router.get("/health")
async def verification_health_check():
    """Health check for verification system"""
    try:
        container = get_dependency_container()
        
        components = {
            "ingestion_engine": container.get('ingestion_engine') is not None,
            "embedder": container.get('embedder') is not None,
            "faiss_store": container.get('faiss_store') is not None,
            "metadata_store": container.get('metadata_store') is not None,
            "chunker": container.get('chunker') is not None
        }
        
        all_healthy = all(components.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": components,
            "active_sessions": len(active_sessions),
            "websocket_connections": len(manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Add this endpoint after the existing endpoints
@router.get("/dashboard", response_class=HTMLResponse)
async def get_verification_dashboard():
    """Serve the verification dashboard HTML"""
    dashboard_path = Path(__file__).parent.parent / "ui" / "verification_dashboard.html"
    
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    with open(dashboard_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content) 