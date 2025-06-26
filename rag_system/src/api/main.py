"""
FastAPI Application
Main API application for the RAG system
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
import asyncio
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import atexit

logger = logging.getLogger(__name__)

# Import modules with fallback mechanism
def safe_import(relative_import, absolute_import):
    """Safely import with fallback from relative to absolute import"""
    try:
        return relative_import()
    except ImportError:
        try:
            return absolute_import()
        except ImportError as e:
            logging.warning(f"Failed to import module: {e}")
            return None

# Import required modules
try:
    from .models.requests import QueryRequest, UploadRequest
    from .models.responses import QueryResponse, UploadResponse, HealthResponse
except ImportError:
    from rag_system.src.api.models.requests import QueryRequest, UploadRequest
    from rag_system.src.api.models.responses import QueryResponse, UploadResponse, HealthResponse

try:
    from ..core.error_handling import RAGSystemError, QueryError, EmbeddingError, LLMError
    from ..core.unified_error_handling import (
        ErrorCode, ErrorInfo, ErrorContext, Result, UnifiedError,
        format_api_response, get_http_status_code, QueryErrorHandler
    )
    from ..core.resource_manager import get_global_app, ManagedThreadPool
    from ..storage.feedback_store import FeedbackStore
except ImportError:
    from rag_system.src.core.error_handling import RAGSystemError, QueryError, EmbeddingError, LLMError
    from rag_system.src.core.unified_error_handling import (
        ErrorCode, ErrorInfo, ErrorContext, Result, UnifiedError,
        format_api_response, get_http_status_code, QueryErrorHandler
    )
    from rag_system.src.core.resource_manager import get_global_app, ManagedThreadPool
    from rag_system.src.storage.feedback_store import FeedbackStore

try:
    from .management_api import create_management_router
    from .verification_endpoints import router as verification_router
except ImportError:
    try:
        from rag_system.src.api.management_api import create_management_router
        from rag_system.src.api.verification_endpoints import router as verification_router
    except ImportError as e:
        logging.warning(f"Could not import API routers: {e}")
        create_management_router = None
        verification_router = None

try:
    from ..core.progress_tracker import ProgressTracker
    from ..ui.progress_monitor import ProgressMonitor
except ImportError:
    try:
        from rag_system.src.core.progress_tracker import ProgressTracker
        from rag_system.src.ui.progress_monitor import ProgressMonitor
    except ImportError:
        ProgressTracker = None
        ProgressMonitor = None

# Global heartbeat monitor - will be set by main.py
heartbeat_monitor = None

# Try to import folder monitor at module level
try:
    from ..monitoring.folder_monitor import folder_monitor, initialize_folder_monitor
except ImportError:
    try:
        from rag_system.src.monitoring.folder_monitor import folder_monitor, initialize_folder_monitor
    except ImportError:
        # If folder monitor is not available, create dummy objects
        folder_monitor = None
        initialize_folder_monitor = None
        logging.warning("Folder monitor module not available")

# Managed thread pool for CPU-intensive tasks
app_lifecycle = None
thread_pool = None

# Constants
DEFAULT_TIMEOUT = 30.0

# Import enhanced folder endpoints
try:
    from .simple_enhanced_endpoints import router as enhanced_folder_router
except ImportError:
    try:
        from .enhanced_folder_endpoints import router as enhanced_folder_router
    except ImportError:
        enhanced_folder_router = None

def create_api_app(container, monitoring=None, heartbeat_monitor_instance=None, folder_monitor_instance=None, enhanced_folder_monitor_instance=None) -> FastAPI:
    """Create and configure FastAPI application with resource management"""
    
    # Initialize managed resources
    global heartbeat_monitor, app_lifecycle, thread_pool, folder_monitor
    
    # Get managed application instance
    app_lifecycle = get_global_app()
    
    # Create managed thread pool for API operations
    thread_pool = app_lifecycle.create_custom_thread_pool('api_operations', 8)
    
    # Set the global heartbeat monitor
    if heartbeat_monitor_instance:
        heartbeat_monitor = heartbeat_monitor_instance
        logging.info(f"✅ Heartbeat monitor set in API: {type(heartbeat_monitor)}")
    else:
        logging.warning("⚠️ No heartbeat monitor instance provided to API")
    
    # Set the global folder monitor
    if folder_monitor_instance:
        folder_monitor = folder_monitor_instance
        # Also update the module-level variable
        try:
            import rag_system.src.monitoring.folder_monitor as fm_module
        except ImportError:
            from ..monitoring import folder_monitor as fm_module
        fm_module.folder_monitor = folder_monitor_instance
        logging.info(f"✅ Folder monitor set in API: {type(folder_monitor)}")
    else:
        logging.warning("⚠️ No folder monitor instance provided to API")
    
    # Get configuration
    config_manager = container.get('config_manager')
    config = config_manager.get_config()
    
    # Initialize feedback store
    feedback_store = FeedbackStore(storage_path="data/feedback_store.db")
    
    # Create FastAPI app
    app = FastAPI(
        title="RAG System API",
        description="Enterprise RAG System with FastAPI, FAISS, and LangGraph",
        version="1.0.0",
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None
    )
    
    # Store monitors in app state for reliable access
    app.state.heartbeat_monitor = heartbeat_monitor
    app.state.enhanced_folder_monitor = enhanced_folder_monitor_instance
    
    # Add CORS middleware
    cors_origins = getattr(config.api, 'cors_origins', [])
    if not cors_origins:
        # Default CORS for development
        cors_origins = ["*"] if config.debug else ["http://localhost:3000", "http://localhost:8080"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Performance tracking storage
    query_performance_log = []
    MAX_PERFORMANCE_LOG_SIZE = 1000
    
    def log_query_performance(query_data: dict):
        """Log query performance data"""
        nonlocal query_performance_log
        
        # Add timestamp
        query_data['timestamp'] = datetime.now().isoformat()
        
        # Add to log
        query_performance_log.append(query_data)
        
        # Keep only recent entries
        if len(query_performance_log) > MAX_PERFORMANCE_LOG_SIZE:
            query_performance_log = query_performance_log[-MAX_PERFORMANCE_LOG_SIZE:]

    # Dependency to get services
    def get_query_engine():
        return container.get('query_engine')
    
    def get_ingestion_engine():
        return container.get('ingestion_engine')
    
    def get_config():
        return config
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        try:
            from datetime import datetime
            # Simple health check without external API calls
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'api': {'status': 'healthy'},
                    'container': {'status': 'healthy', 'services': len(container.list_services())}
                },
                'issues': []
            }
            return HealthResponse(**health_status)
        except Exception as e:
            from datetime import datetime
            return HealthResponse(
                status="error",
                timestamp=datetime.now().isoformat(),
                components={},
                issues=[str(e)]
            )
    
    async def _process_query_async(query_text: str, max_results: int = 3) -> Dict[str, Any]:
        """Process query asynchronously with timeout and proper error handling"""
        def _process_query():
            try:
                # Get components directly from container
                embedder = container.get('embedder')
                faiss_store = container.get('faiss_store')
                llm_client = container.get('llm_client')
                metadata_store = container.get('metadata_store')
                
                # Generate query embedding with timeout
                try:
                    query_embedding = embedder.embed_text(query_text)
                except Exception as e:
                    raise Exception(f"Failed to generate embedding: {str(e)}")
                
                # Search FAISS index with proper metadata formatting
                try:
                    search_results = faiss_store.search_with_metadata(query_embedding, k=max_results)
                except Exception as e:
                    raise Exception(f"Failed to search vectors: {str(e)}")
                
                # Retrieve context and sources
                context_texts = []
                sources = []
                
                for result in search_results:
                    # Extract text and metadata from FAISS result
                    text = result.get('text', '')
                    score = result.get('similarity_score', 0.0)
                    doc_id = result.get('doc_id', 'unknown')
                    
                    if text:
                        context_texts.append(text)
                        sources.append({
                            "doc_id": doc_id,
                            "text": text[:200],
                            "score": float(score),
                            "metadata": result
                        })
                
                # Generate LLM response with timeout
                if context_texts:
                    context = "\n\n".join(context_texts)
                    prompt = f"""Based on the following context, answer the question: {query_text}

Context:
{context}

Answer:"""
                    
                    try:
                        response = llm_client.generate(prompt, max_tokens=500)
                    except Exception as e:
                        raise Exception(f"Failed to generate response: {str(e)}")
                else:
                    response = "I couldn't find relevant information to answer your question."
                
                # Generate unique response ID for feedback tracking
                import uuid
                response_id = str(uuid.uuid4())
                
                return {
                    "response": response,
                    "response_id": response_id,
                    "sources": sources,
                    "query": query_text,
                    "context_used": len(context_texts)
                }
                
            except Exception as e:
                logging.error(f"Query processing error: {e}")
                raise e
        
        # Run with timeout and proper error handling
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(thread_pool, _process_query),
                timeout=DEFAULT_TIMEOUT
            )
            return result
        except asyncio.TimeoutError:
            logging.error("Query processing timed out")
            raise HTTPException(status_code=408, detail="Query processing timed out")
        except Exception as e:
            logging.error(f"Query processing failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Query endpoint - simplified to avoid import issues
    @app.post("/query")
    async def query(request: dict):
        """Process a query and return response with sources"""
        start_time = time.time()
        try:
            query_text = request.get("query", "").strip()
            max_results = min(int(request.get("max_results", 3)), 10)  # Limit max results
            
            if not query_text:
                return JSONResponse({
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Query text is required"
                    }
                }, status_code=400)
            
            # Process query using async function
            result = await _process_query_async(query_text, max_results)
            
            # Log performance data
            total_time = time.time() - start_time
            performance_data = {
                'query': query_text,
                'response_time': total_time,
                'sources_count': len(result.get('sources', [])),
                'success': True
            }
            log_query_performance(performance_data)
            
            return JSONResponse({
                "success": True,
                "data": result
            }, status_code=200)
                
        except ValueError as e:
            # Log failed query performance
            total_time = time.time() - start_time
            performance_data = {
                'query': request.get('query', ''),
                'response_time': total_time,
                'success': False,
                'error': 'Invalid parameter: ' + str(e)
            }
            log_query_performance(performance_data)
            
            return JSONResponse({
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "Invalid max_results value",
                    "details": {"error": str(e)}
                }
            }, status_code=400)
        except Exception as e:
            logging.error(f"Unexpected error in query endpoint: {e}")
            
            # Log failed query performance
            total_time = time.time() - start_time
            performance_data = {
                'query': request.get('query', ''),
                'response_time': total_time,
                'success': False,
                'error': str(e)
            }
            log_query_performance(performance_data)
            
            return JSONResponse({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": {"error": str(e)}
                }
            }, status_code=500)
    
    async def _process_text_ingestion_async(text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process text ingestion asynchronously with timeout"""
        def _process_text():
            try:
                # Get components directly from container
                embedder = container.get('embedder')
                chunker = container.get('chunker')
                faiss_store = container.get('faiss_store')
                metadata_store = container.get('metadata_store')
                
                # Check for existing documents and delete old vectors
                old_vectors_deleted = 0
                doc_path = metadata.get('doc_path')
                if doc_path:
                    # Search for existing vectors with this doc_path
                    existing_vectors = []
                    for vector_id, vector_metadata in faiss_store.id_to_metadata.items():
                        if (not vector_metadata.get('deleted', False) and 
                            vector_metadata.get('doc_path') == doc_path):
                            existing_vectors.append(vector_id)
                    
                    if existing_vectors:
                        logging.info(f"Found {len(existing_vectors)} existing vectors for doc_path: {doc_path}")
                        faiss_store.delete_vectors(existing_vectors)
                        old_vectors_deleted = len(existing_vectors)
                        logging.info(f"Deleted {old_vectors_deleted} old vectors for text update")
                
                # Process the text
                chunks = chunker.chunk_text(text)
                
                if not chunks:
                    return {
                        "status": "error",
                        "message": "No chunks generated from text"
                    }
                
                # Generate embeddings
                chunk_texts = [chunk.get('text', str(chunk)) for chunk in chunks]
                embeddings = embedder.embed_texts(chunk_texts)
                
                # Store in FAISS
                chunk_metadata_list = []
                
                # Generate a better document identifier
                def generate_doc_id(metadata, chunk_index):
                    """Generate a meaningful document ID that includes doc_path"""
                    doc_path = metadata.get('doc_path', '')
                    
                    if doc_path:
                        # Use doc_path as the base for the ID
                        # Remove leading slash and replace special chars
                        doc_id_base = doc_path.strip('/').replace('/', '_').replace(' ', '_')
                        return f"{doc_id_base}_chunk_{chunk_index}"
                    
                    # Fallback to existing logic if no doc_path
                    title = metadata.get('title', '').strip()
                    filename = metadata.get('filename', '').strip()
                    description = metadata.get('description', '').strip()
                    
                    if title:
                        doc_name = title.replace(' ', '_').replace('/', '_').replace('\\', '_')[:50]
                    elif filename:
                        import os
                        doc_name = os.path.splitext(filename)[0].replace(' ', '_').replace('/', '_').replace('\\', '_')[:50]
                    elif description:
                        words = description.split()[:5]
                        doc_name = '_'.join(words).replace('/', '_').replace('\\', '_')[:50]
                    else:
                        import hashlib
                        import time
                        content_hash = hashlib.md5(str(metadata).encode()).hexdigest()[:8]
                        timestamp = str(int(time.time()))[-6:]
                        doc_name = f"doc_{timestamp}_{content_hash}"
                    
                    return f"{doc_name}_chunk_{chunk_index}"
                
                for i, chunk in enumerate(chunks):
                    chunk_text = chunk.get('text', str(chunk))
                    # Create flat metadata structure - no nesting
                    chunk_meta = {
                        'text': chunk_text,
                        'chunk_index': i,
                        'doc_id': generate_doc_id(metadata, i),
                        'doc_path': metadata.get('doc_path'),  # Ensure doc_path is at top level
                        'filename': metadata.get('filename'),
                        'title': metadata.get('title'),
                        'description': metadata.get('description'),
                        'source_type': metadata.get('source_type', 'text'),
                        'timestamp': metadata.get('timestamp', time.time()),
                        'operation': metadata.get('operation', 'ingest'),
                        'source': metadata.get('source', 'api')
                    }
                    # Don't nest metadata within metadata
                    chunk_metadata_list.append(chunk_meta)
                
                vector_ids = faiss_store.add_vectors(embeddings, chunk_metadata_list)
                
                # Store metadata
                file_id = metadata_store.add_file_metadata("text_input", metadata)
                for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                    chunk_text = chunk.get('text', str(chunk))
                    chunk_metadata = {
                        "file_id": file_id,
                        "chunk_index": i,
                        "text": chunk_text,
                        "vector_id": vector_id,
                        "doc_id": generate_doc_id(metadata, i)
                    }
                    metadata_store.add_chunk_metadata(chunk_metadata)
                
                return {
                    "status": "success",
                    "file_id": file_id,
                    "chunks_created": len(chunks),
                    "embeddings_generated": len(embeddings),
                    "is_update": old_vectors_deleted > 0,
                    "old_vectors_deleted": old_vectors_deleted
                }
                
            except Exception as e:
                logging.error(f"Text ingestion error: {e}")
                raise e
        
        # Run with timeout
        loop = asyncio.get_event_loop()
        try:
            # Get configurable timeout from config manager
            config_manager = container.get('config_manager')
            config = config_manager.get_config()
            ingestion_timeout = getattr(config.ingestion, 'timeout', 300.0)  # 5 minutes default
            
            result = await asyncio.wait_for(
                loop.run_in_executor(thread_pool, _process_text),
                timeout=ingestion_timeout
            )
            return result
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Text ingestion timed out")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Text ingestion failed: {str(e)}")
    
    # Text ingestion endpoint
    @app.post("/ingest")
    async def ingest_text(request: dict):
        """Ingest text directly"""
        text = request.get("text", "")
        metadata = request.get("metadata", {})
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        return await _process_text_ingestion_async(text, metadata)
    
    async def _process_file_upload_async(file_content: bytes, filename: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process file upload asynchronously with timeout"""
        def _process_file():
            try:
                import tempfile
                import os
                
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                    tmp_file.write(file_content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Get ingestion engine
                    ingestion_engine = container.get('ingestion_engine')
                    
                    # Ensure original filename is preserved in metadata
                    if 'original_filename' not in metadata:
                        metadata['original_filename'] = filename
                    
                    # Process file
                    result = ingestion_engine.ingest_file(tmp_file_path, metadata)
                    return result
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                        
            except Exception as e:
                logging.error(f"File upload processing error: {e}")
                raise e
        
        # Run with timeout
        loop = asyncio.get_event_loop()
        try:
            # Get configurable timeout from config manager
            config_manager = container.get('config_manager')
            config = config_manager.get_config()
            file_processing_timeout = getattr(config.ingestion, 'file_timeout', 600.0)  # 10 minutes default for files
            
            result = await asyncio.wait_for(
                loop.run_in_executor(thread_pool, _process_file),
                timeout=file_processing_timeout
            )
            return result
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="File processing timed out")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

    # File upload endpoint
    @app.post("/upload", response_model=UploadResponse)
    async def upload_file(
        file: UploadFile = File(...),
        metadata: Optional[str] = None
    ):
        """Upload and process a file"""
        try:
            # Read file content
            file_content = await file.read()
            
            # Parse metadata if provided
            file_metadata = {}
            if metadata:
                import json
                try:
                    file_metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    file_metadata = {"description": metadata}
            
            # Add file info to metadata
            file_metadata.update({
                "filename": file.filename,
                "original_filename": file.filename,  # Add original filename for source labels
                "content_type": file.content_type,
                "file_size": len(file_content)
            })
            
            # Debug: Log the metadata being passed
            logging.info(f"Upload metadata being passed to ingestion: {file_metadata}")
            
            # Process file
            result = await _process_file_upload_async(file_content, file.filename, file_metadata)
            
            return UploadResponse(
                status="success" if result.get("status") == "success" else "error",
                file_id=result.get("file_id"),
                file_path=result.get("file_path"),
                chunks_created=result.get("chunks_created", 0),
                vectors_stored=result.get("vectors_stored"),
                reason=result.get("reason"),
                is_update=result.get("is_update"),
                old_vectors_deleted=result.get("old_vectors_deleted")
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"File upload error: {e}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    # Detailed health check endpoint
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with component testing"""
        try:
            from datetime import datetime
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {},
                'issues': []
            }
            
            # Test components with timeout
            try:
                # Test embedder
                embedder = container.get('embedder')
                config_manager = container.get('config_manager')
                config = config_manager.get_config()
                health_check_timeout = getattr(config.api, 'health_check_timeout', 10.0)
                
                test_embedding = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        thread_pool, 
                        lambda: embedder.embed_text("test")
                    ),
                    timeout=health_check_timeout
                )
                health_status['components']['embedder'] = {
                    'status': 'healthy',
                    'dimension': len(test_embedding)
                }
            except Exception as e:
                health_status['components']['embedder'] = {'status': 'error', 'error': str(e)}
                health_status['issues'].append(f"Embedder error: {e}")
            
            # Test FAISS store
            try:
                faiss_store = container.get('faiss_store')
                stats = faiss_store.get_stats()
                health_status['components']['faiss_store'] = {
                    'status': 'healthy',
                    'vector_count': stats.get('vector_count', 0)
                }
            except Exception as e:
                health_status['components']['faiss_store'] = {'status': 'error', 'error': str(e)}
                health_status['issues'].append(f"FAISS store error: {e}")
            
            # Test LLM client
            try:
                llm_client = container.get('llm_client')
                llm_test_timeout = getattr(config.api, 'llm_test_timeout', 15.0)
                
                test_response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        thread_pool,
                        lambda: llm_client.generate("Hello", max_tokens=5)
                    ),
                    timeout=llm_test_timeout
                )
                health_status['components']['llm_client'] = {
                    'status': 'healthy',
                    'test_response_length': len(test_response) if test_response else 0
                }
            except Exception as e:
                health_status['components']['llm_client'] = {'status': 'error', 'error': str(e)}
                health_status['issues'].append(f"LLM client error: {e}")
            
            # Set overall status
            if health_status['issues']:
                health_status['status'] = 'degraded' if len(health_status['issues']) < 3 else 'unhealthy'
            
            return health_status
            
        except Exception as e:
            from datetime import datetime
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'components': {},
                'issues': [str(e)]
            }

    @app.get("/stats")
    async def get_stats():
        """Get system statistics"""
        try:
            # Get stats with timeout
            def _get_stats():
                faiss_store = container.get('faiss_store')
                metadata_store = container.get('metadata_store')
                embedder = container.get('embedder')
                
                faiss_stats = faiss_store.get_stats()
                metadata_stats = metadata_store.get_stats()
                
                # Get unique documents
                unique_docs = set()
                for vector_id, metadata in faiss_store.id_to_metadata.items():
                    if not metadata.get('deleted', False):
                        doc_id = metadata.get('doc_id', 'unknown')
                        unique_docs.add(doc_id)
                
                # Enhanced stats
                enhanced_stats = {
                    'faiss_store': faiss_stats,
                    'metadata_store': metadata_stats,
                    'timestamp': time.time(),
                    'total_vectors': faiss_stats.get('active_vectors', 0),
                    'total_documents': len(unique_docs),
                    'total_chunks': faiss_stats.get('active_vectors', 0),
                    'embedding_model': getattr(embedder, 'model_name', getattr(embedder, 'model', 'sentence-transformers')),
                    'vector_dimensions': faiss_stats.get('dimension', 384),
                    'index_type': faiss_stats.get('index_type', 'FAISS'),
                    'documents': sorted(list(unique_docs))
                }
                
                return enhanced_stats
            
            loop = asyncio.get_event_loop()
            config_manager = container.get('config_manager')
            config = config_manager.get_config()
            stats_timeout = getattr(config.api, 'stats_timeout', 10.0)
            
            stats = await asyncio.wait_for(
                loop.run_in_executor(thread_pool, _get_stats),
                timeout=stats_timeout
            )
            return stats
            
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Stats request timed out")
        except Exception as e:
            logging.error(f"Stats error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

    @app.get("/documents")
    async def get_documents():
        """Get list of all documents in the vector store"""
        try:
            def _get_documents():
                faiss_store = container.get('faiss_store')
                
                # Get unique documents
                unique_docs = set()
                doc_details = {}
                
                for vector_id, metadata in faiss_store.id_to_metadata.items():
                    # Safely handle None metadata
                    if metadata is None:
                        metadata = {}
                    
                    if not metadata.get('deleted', False):
                        doc_id = metadata.get('doc_id', 'unknown')
                        unique_docs.add(doc_id)
                        
                        # Collect document details with safe extraction
                        if doc_id not in doc_details:
                            doc_details[doc_id] = {
                                'doc_id': doc_id,
                                'chunks': 0,
                                'doc_path': metadata.get('doc_path', '') if metadata else '',
                                'filename': metadata.get('filename', '') if metadata else '',
                                'upload_timestamp': metadata.get('upload_timestamp', '') if metadata else '',
                                'source': metadata.get('source', '') if metadata else ''
                            }
                        doc_details[doc_id]['chunks'] += 1
                
                return {
                    "documents": sorted(list(unique_docs)),
                    "total_documents": len(unique_docs),
                    "document_details": list(doc_details.values())
                }
            
            loop = asyncio.get_event_loop()
            config_manager = container.get('config_manager')
            config = config_manager.get_config()
            stats_timeout = getattr(config.api, 'stats_timeout', 10.0)
            
            result = await asyncio.wait_for(
                loop.run_in_executor(thread_pool, _get_documents),
                timeout=stats_timeout
            )
            return result
            
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Documents request timed out")
        except Exception as e:
            logging.error(f"Documents error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

    @app.get("/config")
    async def get_config_info(config=Depends(get_config)):
        """Get configuration information"""
        return {
            'environment': config.environment,
            'debug': config.debug,
            'api': {
                'host': config.api.host,
                'port': config.api.port
            },
            'embedding': {
                'provider': config.embedding.provider,
                'model': config.embedding.model
            },
            'llm': {
                'provider': config.llm.provider,
                'model': config.llm.model
            }
        }

    # ========== COMPREHENSIVE HEARTBEAT ENDPOINTS ==========
    
    @app.get("/heartbeat")
    async def get_heartbeat():
        """Get comprehensive system heartbeat"""
        try:
            if heartbeat_monitor:
                health = await heartbeat_monitor.comprehensive_health_check()
                return health.to_dict()
            else:
                raise HTTPException(status_code=503, detail="Heartbeat monitor not initialized")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health/summary")
    async def get_health_summary():
        """Get health summary (no auth required for monitoring tools)"""
        try:
            if heartbeat_monitor:
                summary = heartbeat_monitor.get_health_summary()
                return summary
            else:
                return {"status": "unknown", "message": "Heartbeat monitor not initialized"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health/components")
    async def get_component_health():
        """Get detailed component health status"""
        try:
            if heartbeat_monitor:
                if not heartbeat_monitor.last_health_check:
                    health = await heartbeat_monitor.comprehensive_health_check()
                else:
                    health = heartbeat_monitor.last_health_check
                
                return {
                    "components": [comp.to_dict() for comp in health.components],
                    "timestamp": health.timestamp
                }
            else:
                raise HTTPException(status_code=503, detail="Heartbeat monitor not initialized")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health/history")
    async def get_health_history(limit: int = 24):
        """Get health check history"""
        try:
            if heartbeat_monitor:
                history = heartbeat_monitor.health_history
                
                # Return recent history
                recent_history = history[-limit:] if len(history) > limit else history
                
                return {
                    "history": recent_history,
                    "total_checks": len(history),
                    "returned_checks": len(recent_history)
                }
            else:
                return {"history": [], "total_checks": 0, "returned_checks": 0}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/health/check")
    async def trigger_health_check():
        """Manually trigger health check"""
        try:
            if heartbeat_monitor:
                health = await heartbeat_monitor.comprehensive_health_check()
                return {
                    "message": "Health check completed",
                    "overall_status": health.overall_status.value,
                    "timestamp": health.timestamp,
                    "component_count": len(health.components)
                }
            else:
                raise HTTPException(status_code=503, detail="Heartbeat monitor not initialized")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/heartbeat/start")
    async def start_heartbeat():
        """Start heartbeat monitoring"""
        try:
            # Try to get heartbeat monitor from multiple sources
            monitor = heartbeat_monitor or getattr(app.state, 'heartbeat_monitor', None)
            if monitor:
                # Check if monitor has the start_monitoring method
                if hasattr(monitor, 'start_monitoring'):
                    monitor.start_monitoring()
                    return {
                        "message": "Heartbeat monitoring started",
                        "status": "active",
                        "timestamp": time.time()
                    }
                else:
                    raise HTTPException(status_code=500, detail="Heartbeat monitor does not support start_monitoring")
            else:
                raise HTTPException(status_code=503, detail="Heartbeat monitor not initialized")
        except Exception as e:
            logging.error(f"Error starting heartbeat: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to start heartbeat: {str(e)}")

    @app.post("/heartbeat/stop")
    async def stop_heartbeat():
        """Stop heartbeat monitoring"""
        try:
            # Try to get heartbeat monitor from multiple sources
            monitor = heartbeat_monitor or getattr(app.state, 'heartbeat_monitor', None)
            if monitor:
                # Check if monitor has the stop_monitoring method
                if hasattr(monitor, 'stop_monitoring'):
                    monitor.stop_monitoring()
                    return {
                        "message": "Heartbeat monitoring stopped",
                        "status": "inactive",
                        "timestamp": time.time()
                    }
                else:
                    raise HTTPException(status_code=500, detail="Heartbeat monitor does not support stop_monitoring")
            else:
                raise HTTPException(status_code=503, detail="Heartbeat monitor not initialized")
        except Exception as e:
            logging.error(f"Error stopping heartbeat: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stop heartbeat: {str(e)}")

    @app.get("/heartbeat/status")
    async def get_heartbeat_status():
        """Get heartbeat monitoring status"""
        try:
            # Try to get heartbeat monitor from multiple sources
            monitor = heartbeat_monitor or getattr(app.state, 'heartbeat_monitor', None)
            logging.info(f"🔍 Heartbeat status check - global: {heartbeat_monitor}, app.state: {getattr(app.state, 'heartbeat_monitor', None)}")
            if monitor:
                is_running = getattr(monitor, 'is_running', False)
                return {
                    "enabled": is_running,
                    "status": "active" if is_running else "inactive",
                    "interval_seconds": getattr(monitor, 'interval', 30),
                    "last_check": getattr(monitor, 'last_check_time', None),
                    "total_checks": len(getattr(monitor, 'health_history', [])),
                    "timestamp": time.time()
                }
            else:
                return {
                    "enabled": False,
                    "status": "not_initialized",
                    "timestamp": time.time()
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/heartbeat/logs")
    async def get_heartbeat_logs(limit: int = 50):
        """Get recent heartbeat logs"""
        try:
            if heartbeat_monitor:
                history = getattr(heartbeat_monitor, 'health_history', [])
                recent_logs = history[-limit:] if len(history) > limit else history
                
                # Format logs for display
                formatted_logs = []
                for log_entry in recent_logs:
                    if isinstance(log_entry, dict):
                        formatted_logs.append({
                            "timestamp": log_entry.get("timestamp", "Unknown"),
                            "status": log_entry.get("overall_status", "Unknown"),
                            "components": len(log_entry.get("components", [])),
                            "message": f"Health check completed - {log_entry.get('overall_status', 'Unknown')}"
                        })
                    else:
                        formatted_logs.append({
                            "timestamp": getattr(log_entry, 'timestamp', 'Unknown'),
                            "status": getattr(log_entry, 'overall_status', 'Unknown'),
                            "components": len(getattr(log_entry, 'components', [])),
                            "message": f"Health check completed - {getattr(log_entry, 'overall_status', 'Unknown')}"
                        })
                
                return {
                    "logs": formatted_logs,
                    "total_logs": len(history),
                    "returned_logs": len(formatted_logs),
                    "timestamp": time.time()
                }
            else:
                return {
                    "logs": [],
                    "total_logs": 0,
                    "returned_logs": 0,
                    "message": "Heartbeat monitor not initialized"
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Folder Monitoring Endpoints
    @app.get("/folder-monitor/status")
    async def get_folder_monitor_status():
        """Get folder monitoring status"""
        try:
            # Get the current folder monitor instance
            current_folder_monitor = None
            
            # Try to get from the global variable first
            from ..monitoring.folder_monitor import folder_monitor as global_folder_monitor
            current_folder_monitor = global_folder_monitor
            
            # If not available, try to initialize on-demand
            if not current_folder_monitor and initialize_folder_monitor:
                try:
                    config_manager = container.get('config_manager')
                    if config_manager:
                        current_folder_monitor = initialize_folder_monitor(container, config_manager)
                        # Update the global variable
                        try:
                            import rag_system.src.monitoring.folder_monitor as fm_module
                        except ImportError:
                            from ..monitoring import folder_monitor as fm_module
                        fm_module.folder_monitor = current_folder_monitor
                        logging.info("✅ Folder monitor initialized on-demand")
                except Exception as init_e:
                    logging.error(f"Failed to initialize folder monitor on-demand: {init_e}")
            
            if current_folder_monitor:
                status = current_folder_monitor.get_status()
                return {
                    "success": True,
                    "status": status,
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "error": "Folder monitor not initialized",
                    "timestamp": time.time()
                }
        except Exception as e:
            logging.error(f"Error in folder monitor status endpoint: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Folder monitor status error: {str(e)}")

    @app.post("/folder-monitor/add")
    async def add_monitored_folder(request: dict):
        """Add a folder to monitoring"""
        try:
            folder_path = request.get('folder_path')
            if not folder_path:
                raise HTTPException(status_code=400, detail="folder_path is required")
            
            from ..monitoring.folder_monitor import folder_monitor, initialize_folder_monitor
            
            # If folder monitor is not initialized, try to initialize it
            if not folder_monitor:
                try:
                    config_manager = container.get('config_manager')
                    if config_manager:
                        global_folder_monitor = initialize_folder_monitor(container, config_manager)
                        # Update the global variable
                        try:
                            import rag_system.src.monitoring.folder_monitor as fm_module
                        except ImportError:
                            from ..monitoring import folder_monitor as fm_module
                        fm_module.folder_monitor = global_folder_monitor
                        logging.info("✅ Folder monitor initialized on-demand for add operation")
                except Exception as init_e:
                    logging.error(f"Failed to initialize folder monitor on-demand: {init_e}")
                    raise HTTPException(status_code=503, detail=f"Folder monitor initialization failed: {init_e}")
            
            # Try again after initialization
            from ..monitoring.folder_monitor import folder_monitor
            
            if not folder_monitor:
                raise HTTPException(status_code=503, detail="Folder monitor not initialized")
            
            result = folder_monitor.add_folder(folder_path)
            
            if result.get('success'):
                # Automatically trigger a scan after adding folder for immediate feedback
                try:
                    scan_result = folder_monitor.force_scan()
                    scan_info = {
                        "immediate_scan": True,
                        "changes_detected": scan_result.get('changes_detected', 0),
                        "files_tracked": scan_result.get('files_tracked', 0)
                    }
                except Exception as scan_e:
                    logging.warning(f"Failed to trigger immediate scan after adding folder: {scan_e}")
                    scan_info = {"immediate_scan": False, "scan_error": str(scan_e)}
                
                return {
                    "success": True,
                    "message": result.get('message'),
                    "files_found": result.get('files_found', 0),
                    "folder_path": folder_path,
                    "timestamp": time.time(),
                    **scan_info
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add folder'))
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/folder-monitor/remove")
    async def remove_monitored_folder(request: dict):
        """Remove a folder from monitoring"""
        try:
            folder_path = request.get('folder_path')
            if not folder_path:
                raise HTTPException(status_code=400, detail="folder_path is required")
            
            from ..monitoring.folder_monitor import folder_monitor
            
            if not folder_monitor:
                raise HTTPException(status_code=503, detail="Folder monitor not initialized")
            
            result = folder_monitor.remove_folder(folder_path)
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": result.get('message'),
                    "files_removed": result.get('files_removed', 0),
                    "folder_path": folder_path,
                    "timestamp": time.time()
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Failed to remove folder'))
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/folder-monitor/folders")
    async def get_monitored_folders():
        """Get list of monitored folders"""
        try:
            from ..monitoring.folder_monitor import folder_monitor
            
            if folder_monitor:
                folders = folder_monitor.get_monitored_folders()
                return {
                    "success": True,
                    "folders": folders,
                    "count": len(folders),
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "folders": [],
                    "count": 0,
                    "error": "Folder monitor not initialized",
                    "timestamp": time.time()
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/folder-monitor/start")
    async def start_folder_monitoring():
        """Start folder monitoring"""
        try:
            from ..monitoring.folder_monitor import folder_monitor
            
            if not folder_monitor:
                raise HTTPException(status_code=503, detail="Folder monitor not initialized")
            
            result = folder_monitor.start_monitoring()
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": result.get('message'),
                    "folders": result.get('folders', []),
                    "interval": result.get('interval', 60),
                    "timestamp": time.time()
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Failed to start monitoring'))
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/folder-monitor/stop")
    async def stop_folder_monitoring():
        """Stop folder monitoring"""
        try:
            from ..monitoring.folder_monitor import folder_monitor
            
            if not folder_monitor:
                raise HTTPException(status_code=503, detail="Folder monitor not initialized")
            
            result = folder_monitor.stop_monitoring()
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": result.get('message'),
                    "timestamp": time.time()
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Failed to stop monitoring'))
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/folder-monitor/scan")
    async def force_folder_scan():
        """Force an immediate scan of all monitored folders"""
        try:
            from ..monitoring.folder_monitor import folder_monitor
            
            if not folder_monitor:
                raise HTTPException(status_code=503, detail="Folder monitor not initialized")
            
            result = folder_monitor.force_scan()
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": result.get('message'),
                    "changes_detected": result.get('changes_detected', 0),
                    "files_tracked": result.get('files_tracked', 0),
                    "timestamp": time.time()
                }
            else:
                raise HTTPException(status_code=500, detail=result.get('error', 'Scan failed'))
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/folder-monitor/files")
    async def get_monitored_files():
        """Get status of all monitored files"""
        try:
            from ..monitoring.folder_monitor import folder_monitor
            
            if folder_monitor:
                file_states = folder_monitor.get_file_states()
                return {
                    "success": True,
                    "files": file_states,
                    "count": len(file_states),
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "files": {},
                    "count": 0,
                    "error": "Folder monitor not initialized",
                    "timestamp": time.time()
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/documents/{doc_path:path}")
    async def delete_document(doc_path: str):
        """Delete a specific document and its vectors from the system"""
        try:
            faiss_store = container.get('faiss_store')
            metadata_store = container.get('metadata_store')
            
            # Find vectors associated with this document
            vectors_to_delete = []
            for vector_id, metadata in faiss_store.id_to_metadata.items():
                if (not metadata.get('deleted', False) and 
                    metadata.get('doc_path') == doc_path):
                    vectors_to_delete.append(vector_id)
            
            if not vectors_to_delete:
                return {
                    "status": "warning",
                    "message": f"No vectors found for document: {doc_path}",
                    "vectors_deleted": 0,
                    "doc_path": doc_path
                }
            
            # Delete the vectors
            deleted_count = faiss_store.delete_vectors(vectors_to_delete)
            
            return {
                "status": "success",
                "message": f"Document deleted successfully: {doc_path}",
                "vectors_deleted": deleted_count,
                "doc_path": doc_path,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logging.error(f"Error deleting document {doc_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

    @app.post("/clear")
    async def clear_vector_store():
        """Clear all vectors and documents from the system"""
        try:
            faiss_store = container.get('faiss_store')
            metadata_store = container.get('metadata_store')
            
            # Get stats before clearing
            stats_before = faiss_store.get_stats()
            vectors_before = stats_before.get('active_vectors', 0)
            
            # Get document count before clearing
            documents_before = len(set(
                metadata.get('doc_id', 'unknown') 
                for metadata in faiss_store.id_to_metadata.values()
                if not metadata.get('deleted', False)
            ))
            
            # Get chunk count before clearing
            chunks_before = len([
                metadata for metadata in faiss_store.id_to_metadata.values()
                if not metadata.get('deleted', False)
            ])
            
            # Clear the FAISS store
            faiss_store.clear_index()
            
            # Clear metadata store if it has a clear method
            try:
                if hasattr(metadata_store, 'clear_all_data'):
                    metadata_store.clear_all_data()
                elif hasattr(metadata_store, 'clear'):
                    metadata_store.clear()
            except Exception as e:
                logging.warning(f"Could not clear metadata store: {e}")
            
            return {
                "status": "success",
                "message": "Vector store cleared successfully",
                "vectors_deleted": vectors_before,
                "documents_deleted": documents_before,
                "chunks_deleted": chunks_before,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logging.error(f"Error clearing vector store: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to clear vector store: {str(e)}")

    @app.get("/health/performance")
    async def get_performance_metrics():
        """Get detailed performance metrics"""
        try:
            if heartbeat_monitor:
                # Get current performance metrics
                metrics = await heartbeat_monitor._get_performance_metrics()
                
                # Add additional metrics if available
                try:
                    faiss_store = container.get('faiss_store')
                    stats = faiss_store.get_stats()
                    metrics.update({
                        'vector_store_metrics': stats
                    })
                except Exception:
                    pass
                
                return metrics
            else:
                raise HTTPException(status_code=503, detail="Heartbeat monitor not initialized")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Feedback endpoints
    @app.post("/feedback")
    async def submit_feedback(request: dict):
        """Collect user feedback on responses"""
        try:
            # Extract feedback data
            query = request.get('query', '')
            response_id = request.get('response_id', '')
            response_text = request.get('response_text', '')
            helpful = request.get('helpful', False)
            feedback_text = request.get('feedback_text', '')
            confidence_score = request.get('confidence_score', 0.0)
            confidence_level = request.get('confidence_level', 'unknown')
            sources_count = request.get('sources_count', 0)
            user_id = request.get('user_id', 'anonymous')
            session_id = request.get('session_id', '')
            
            # Additional metadata
            metadata = {
                'user_agent': request.get('user_agent', ''),
                'processing_time': request.get('processing_time', 0),
                'sources': request.get('sources', [])
            }
            
            # Validate required fields
            if not query:
                raise HTTPException(status_code=400, detail="Query is required")
            
            # Store feedback
            feedback_data = {
                'query': query,
                'response_id': response_id,
                'response_text': response_text,
                'helpful': bool(helpful),
                'feedback_text': feedback_text,
                'confidence_score': float(confidence_score),
                'confidence_level': confidence_level,
                'sources_count': int(sources_count),
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                **metadata
            }
            
            feedback_id = feedback_store.add_feedback(feedback_data)
            
            # Use feedback to improve system (placeholder for future ML integration)
            if not helpful and feedback_text:
                logger.info(f"Negative feedback received for query: '{query[:50]}...' - {feedback_text}")
                # TODO: Integrate with reranking model or query enhancement
            
            return {
                "status": "feedback received",
                "feedback_id": feedback_id,
                "message": "Thank you for your feedback! It helps us improve the system."
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to process feedback")
    
    @app.get("/feedback/stats")
    async def get_feedback_stats(days: int = 30):
        """Get feedback statistics"""
        try:
            stats = feedback_store.get_feedback_stats(days=days)
            return stats
        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get feedback statistics")
    
    @app.get("/feedback/suggestions")
    async def get_improvement_suggestions():
        """Get system improvement suggestions based on feedback"""
        try:
            suggestions = feedback_store.get_improvement_suggestions()
            return {
                "suggestions": suggestions,
                "count": len(suggestions),
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get improvement suggestions: {e}")
            raise HTTPException(status_code=500, detail="Failed to get improvement suggestions")
    
    @app.get("/feedback/recent")
    async def get_recent_feedback(limit: int = 50, helpful_only: bool = False):
        """Get recent feedback entries"""
        try:
            feedback_list = feedback_store.get_recent_feedback(limit=limit, helpful_only=helpful_only)
            return {
                "feedback": feedback_list,
                "count": len(feedback_list),
                "limit": limit,
                "helpful_only": helpful_only
            }
        except Exception as e:
            logger.error(f"Failed to get recent feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to get recent feedback")
    
    @app.post("/feedback/export")
    async def export_feedback(request: dict):
        """Export feedback data for analysis"""
        try:
            output_path = request.get('output_path', 'feedback_export.json')
            format_type = request.get('format', 'json')
            
            success = feedback_store.export_feedback(output_path, format_type)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Feedback exported to {output_path}",
                    "format": format_type
                }
            else:
                raise HTTPException(status_code=500, detail="Export failed")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to export feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to export feedback")

    # ========================================================================================
    # VECTOR INDEX MANAGEMENT ENDPOINTS
    # ========================================================================================
    
    @app.get("/vectors")
    async def get_vectors_paginated(
        page: int = 1,
        page_size: int = 20,
        include_content: bool = False,
        include_embeddings: bool = False,
        doc_filter: Optional[str] = None,
        source_type_filter: Optional[str] = None
    ):
        """Get paginated list of vectors with metadata"""
        # Ensure page and page_size are integers
        try:
            page = int(page)
        except Exception:
            page = 1
        try:
            page_size = int(page_size)
        except Exception:
            page_size = 20
        try:
            def _get_vectors():
                faiss_store = container.get('faiss_store')
                metadata_store = container.get('metadata_store')
                
                # Get all vector metadata
                all_metadata = faiss_store.get_all_metadata()
                
                # Apply filters
                filtered_metadata = []
                for vector_id, metadata in all_metadata.items():
                    if doc_filter and doc_filter.lower() not in metadata.get('doc_path', '').lower():
                        continue
                    if source_type_filter and metadata.get('source_type') != source_type_filter:
                        continue
                    
                    vector_info = {
                        'vector_id': vector_id,
                        'doc_id': metadata.get('doc_id', 'unknown'),
                        'doc_path': metadata.get('doc_path', 'unknown'),
                        'source_type': metadata.get('source_type', 'unknown'),
                        'chunk_index': metadata.get('chunk_index', 0),
                        'similarity_score': metadata.get('similarity_score', 0.0),
                        'timestamp': metadata.get('timestamp', ''),
                        'metadata': {k: v for k, v in metadata.items() if k not in ['content', 'embedding']}
                    }
                    
                    # Include content if requested
                    if include_content and 'content' in metadata:
                        vector_info['content'] = metadata['content'][:500] + "..." if len(metadata.get('content', '')) > 500 else metadata.get('content', '')
                        vector_info['content_length'] = len(metadata.get('content', ''))
                    
                    # Include embeddings if requested
                    if include_embeddings and 'embedding' in metadata:
                        vector_info['embedding_preview'] = metadata['embedding'][:10] if isinstance(metadata['embedding'], list) else str(metadata['embedding'])[:100]
                        vector_info['embedding_dimension'] = len(metadata['embedding']) if isinstance(metadata['embedding'], list) else 'unknown'
                    
                    filtered_metadata.append(vector_info)
                
                # Sort by timestamp (newest first)
                filtered_metadata.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                # Pagination
                total_vectors = len(filtered_metadata)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_vectors = filtered_metadata[start_idx:end_idx]
                
                # Get summary statistics
                source_types = {}
                doc_paths = {}
                for metadata in filtered_metadata:
                    source_type = metadata.get('source_type', 'unknown')
                    doc_path = metadata.get('doc_path', 'unknown')
                    source_types[source_type] = source_types.get(source_type, 0) + 1
                    doc_paths[doc_path] = doc_paths.get(doc_path, 0) + 1
                
                return {
                    'success': True,
                    'data': {
                        'vectors': paginated_vectors,
                        'pagination': {
                            'page': page,
                            'page_size': page_size,
                            'total_vectors': total_vectors,
                            'total_pages': (total_vectors + page_size - 1) // page_size,
                            'has_next': end_idx < total_vectors,
                            'has_previous': page > 1
                        },
                        'filters': {
                            'doc_filter': doc_filter,
                            'source_type_filter': source_type_filter,
                            'include_content': include_content,
                            'include_embeddings': include_embeddings
                        },
                        'summary': {
                            'total_vectors': total_vectors,
                            'source_types': source_types,
                            'unique_documents': len(doc_paths),
                            'top_documents': dict(sorted(doc_paths.items(), key=lambda x: x[1], reverse=True)[:10])
                        }
                    }
                }
            
            # Execute with timeout
            result = await asyncio.get_event_loop().run_in_executor(
                thread_pool, _get_vectors
            )
            return result
            
        except Exception as e:
            logging.error(f"Error getting vectors: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    @app.get("/vectors/{vector_id}")
    async def get_vector_details(vector_id: str, include_embedding: bool = False):
        """Get detailed information about a specific vector"""
        try:
            def _get_vector_details():
                faiss_store = container.get('faiss_store')
                
                # Get vector metadata
                metadata = faiss_store.get_metadata(vector_id)
                if not metadata:
                    return {
                        'success': False,
                        'error': f'Vector {vector_id} not found'
                    }
                
                vector_info = {
                    'vector_id': vector_id,
                    'metadata': metadata,
                    'doc_id': metadata.get('doc_id', 'unknown'),
                    'doc_path': metadata.get('doc_path', 'unknown'),
                    'source_type': metadata.get('source_type', 'unknown'),
                    'chunk_index': metadata.get('chunk_index', 0),
                    'content': metadata.get('content', ''),
                    'content_length': len(metadata.get('content', '')),
                    'timestamp': metadata.get('timestamp', ''),
                    'similarity_score': metadata.get('similarity_score', 0.0)
                }
                
                # Include embedding if requested
                if include_embedding and 'embedding' in metadata:
                    embedding = metadata['embedding']
                    vector_info['embedding'] = embedding
                    vector_info['embedding_stats'] = {
                        'dimension': len(embedding) if isinstance(embedding, list) else 'unknown',
                        'norm': sum(x*x for x in embedding)**0.5 if isinstance(embedding, list) else 'unknown',
                        'min_value': min(embedding) if isinstance(embedding, list) else 'unknown',
                        'max_value': max(embedding) if isinstance(embedding, list) else 'unknown',
                        'mean_value': sum(embedding)/len(embedding) if isinstance(embedding, list) else 'unknown'
                    }
                
                # Find similar vectors
                try:
                    if 'embedding' in metadata:
                        similar_results = faiss_store.search_with_metadata(metadata['embedding'], k=6)
                        similar_vectors = []
                        for result in similar_results[1:]:  # Skip the first one (itself)
                            similar_vectors.append({
                                'vector_id': result.get('vector_id', 'unknown'),
                                'doc_id': result.get('doc_id', 'unknown'),
                                'similarity': result.get('similarity', 0.0),
                                'content_preview': result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                            })
                        vector_info['similar_vectors'] = similar_vectors[:5]
                except Exception as e:
                    vector_info['similar_vectors'] = []
                    vector_info['similarity_error'] = str(e)
                
                return {
                    'success': True,
                    'data': vector_info
                }
            
            # Execute with timeout
            result = await asyncio.get_event_loop().run_in_executor(
                thread_pool, _get_vector_details
            )
            return result
            
        except Exception as e:
            logging.error(f"Error getting vector details: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    @app.get("/vectors/search")
    async def search_vectors(
        query: str,
        k: int = 10,
        similarity_threshold: float = 0.0,
        doc_filter: Optional[str] = None,
        include_embeddings: bool = False
    ):
        """Search vectors by query with detailed results"""
        try:
            def _search_vectors():
                query_engine = container.get('query_engine')
                faiss_store = container.get('faiss_store')
                embedder = container.get('embedder')
                
                # Generate query embedding
                query_embedding = embedder.embed_text(query)
                
                # Search vectors
                search_results = faiss_store.search_with_metadata(query_embedding, k=k*2)  # Get more for filtering
                
                # Filter results
                filtered_results = []
                for result in search_results:
                    if result.get('similarity', 0) < similarity_threshold:
                        continue
                    if doc_filter and doc_filter.lower() not in result.get('doc_path', '').lower():
                        continue
                    
                    result_info = {
                        'vector_id': result.get('vector_id', 'unknown'),
                        'doc_id': result.get('doc_id', 'unknown'),
                        'doc_path': result.get('doc_path', 'unknown'),
                        'similarity': result.get('similarity', 0.0),
                        'content': result.get('content', ''),
                        'content_preview': result.get('content', '')[:200] + "..." if len(result.get('content', '')) > 200 else result.get('content', ''),
                        'chunk_index': result.get('chunk_index', 0),
                        'source_type': result.get('source_type', 'unknown'),
                        'timestamp': result.get('timestamp', '')
                    }
                    
                    if include_embeddings and 'embedding' in result:
                        result_info['embedding_preview'] = result['embedding'][:10] if isinstance(result['embedding'], list) else str(result['embedding'])[:100]
                    
                    filtered_results.append(result_info)
                    
                    if len(filtered_results) >= k:
                        break
                
                # Calculate search statistics
                similarities = [r['similarity'] for r in filtered_results]
                search_stats = {
                    'total_results': len(filtered_results),
                    'avg_similarity': sum(similarities) / len(similarities) if similarities else 0,
                    'max_similarity': max(similarities) if similarities else 0,
                    'min_similarity': min(similarities) if similarities else 0,
                    'results_above_threshold': len([s for s in similarities if s > similarity_threshold])
                }
                
                return {
                    'success': True,
                    'data': {
                        'query': query,
                        'results': filtered_results,
                        'search_params': {
                            'k': k,
                            'similarity_threshold': similarity_threshold,
                            'doc_filter': doc_filter,
                            'include_embeddings': include_embeddings
                        },
                        'statistics': search_stats
                    }
                }
            
            # Execute with timeout
            result = await asyncio.get_event_loop().run_in_executor(
                thread_pool, _search_vectors
            )
            return result
            
        except Exception as e:
            logging.error(f"Error searching vectors: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    # ========================================================================================
    # QUERY PERFORMANCE MONITORING ENDPOINTS
    # ========================================================================================
    

    
    @app.get("/performance/queries")
    async def get_query_performance(
        limit: int = 50,
        include_details: bool = True,
        time_range_hours: int = 24
    ):
        """Get query performance metrics"""
        try:
            from datetime import datetime, timedelta
            
            # Filter by time range
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            filtered_logs = [
                log for log in query_performance_log
                if datetime.fromisoformat(log['timestamp']) > cutoff_time
            ]
            
            # Get recent queries
            recent_queries = filtered_logs[-limit:] if filtered_logs else []
            
            # Calculate performance statistics
            if filtered_logs:
                response_times = [log.get('response_time', 0) for log in filtered_logs]
                embedding_times = [log.get('embedding_time', 0) for log in filtered_logs if log.get('embedding_time')]
                search_times = [log.get('search_time', 0) for log in filtered_logs if log.get('search_time')]
                llm_times = [log.get('llm_time', 0) for log in filtered_logs if log.get('llm_time')]
                
                performance_stats = {
                    'total_queries': len(filtered_logs),
                    'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
                    'min_response_time': min(response_times) if response_times else 0,
                    'max_response_time': max(response_times) if response_times else 0,
                    'avg_embedding_time': sum(embedding_times) / len(embedding_times) if embedding_times else 0,
                    'avg_search_time': sum(search_times) / len(search_times) if search_times else 0,
                    'avg_llm_time': sum(llm_times) / len(llm_times) if llm_times else 0,
                    'success_rate': len([log for log in filtered_logs if log.get('success', False)]) / len(filtered_logs) * 100,
                    'error_rate': len([log for log in filtered_logs if not log.get('success', True)]) / len(filtered_logs) * 100
                }
                
                # Query complexity analysis
                query_lengths = [len(log.get('query', '')) for log in filtered_logs]
                sources_returned = [log.get('sources_count', 0) for log in filtered_logs]
                
                complexity_stats = {
                    'avg_query_length': sum(query_lengths) / len(query_lengths) if query_lengths else 0,
                    'avg_sources_returned': sum(sources_returned) / len(sources_returned) if sources_returned else 0,
                    'max_sources_returned': max(sources_returned) if sources_returned else 0
                }
                
                # Error analysis
                errors = [log.get('error', '') for log in filtered_logs if log.get('error')]
                error_types = {}
                for error in errors:
                    error_type = error.split(':')[0] if ':' in error else error
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
            else:
                performance_stats = {
                    'total_queries': 0,
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'avg_embedding_time': 0,
                    'avg_search_time': 0,
                    'avg_llm_time': 0,
                    'success_rate': 0,
                    'error_rate': 0
                }
                complexity_stats = {
                    'avg_query_length': 0,
                    'avg_sources_returned': 0,
                    'max_sources_returned': 0
                }
                error_types = {}
            
            response_data = {
                'performance_stats': performance_stats,
                'complexity_stats': complexity_stats,
                'error_analysis': {
                    'total_errors': len(errors) if 'errors' in locals() else 0,
                    'error_types': error_types
                },
                'time_range_hours': time_range_hours,
                'data_points': len(filtered_logs)
            }
            
            if include_details:
                response_data['recent_queries'] = recent_queries
            
            return {
                'success': True,
                'data': response_data
            }
            
        except Exception as e:
            logging.error(f"Error getting query performance: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    @app.post("/performance/test")
    async def test_query_performance(request: dict):
        """Test query performance with detailed timing"""
        try:
            query_text = request.get('query', 'test query')
            max_results = request.get('max_results', 3)
            
            # Start timing
            start_time = time.time()
            
            # Detailed timing for each component
            component_times = {}
            
            def _test_performance():
                nonlocal component_times
                
                # Time embedding generation
                embedding_start = time.time()
                embedder = container.get('embedder')
                query_embedding = embedder.embed_text(query_text)
                component_times['embedding'] = time.time() - embedding_start
                
                # Time vector search
                search_start = time.time()
                faiss_store = container.get('faiss_store')
                search_results = faiss_store.search_with_metadata(query_embedding, k=max_results)
                component_times['search'] = time.time() - search_start
                
                # Time LLM generation (if sources found)
                if search_results:
                    llm_start = time.time()
                    try:
                        llm = container.get('llm')
                        context = "\n".join([result.get('content', '') for result in search_results[:3]])
                        prompt = f"Based on the following context, answer the question: {query_text}\n\nContext:\n{context}"
                        response = llm.generate(prompt)
                        component_times['llm'] = time.time() - llm_start
                    except Exception as e:
                        component_times['llm'] = 0
                        component_times['llm_error'] = str(e)
                else:
                    component_times['llm'] = 0
                
                return {
                    'query': query_text,
                    'sources_found': len(search_results),
                    'embedding_dimension': len(query_embedding) if isinstance(query_embedding, list) else 'unknown',
                    'search_results': search_results[:max_results] if search_results else []
                }
            
            # Execute test
            result = await asyncio.get_event_loop().run_in_executor(
                thread_pool, _test_performance
            )
            
            total_time = time.time() - start_time
            
            # Log performance data
            performance_data = {
                'query': query_text,
                'response_time': total_time,
                'embedding_time': component_times.get('embedding', 0),
                'search_time': component_times.get('search', 0),
                'llm_time': component_times.get('llm', 0),
                'sources_count': len(result.get('search_results', [])),
                'success': True
            }
            log_query_performance(performance_data)
            
            return {
                'success': True,
                'data': {
                    'query': query_text,
                    'total_time': total_time,
                    'component_times': component_times,
                    'results': result,
                    'performance_breakdown': {
                        'embedding_percentage': (component_times.get('embedding', 0) / total_time * 100) if total_time > 0 else 0,
                        'search_percentage': (component_times.get('search', 0) / total_time * 100) if total_time > 0 else 0,
                        'llm_percentage': (component_times.get('llm', 0) / total_time * 100) if total_time > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            logging.error(f"Error testing query performance: {e}")
            
            # Log failed performance data
            performance_data = {
                'query': request.get('query', 'test query'),
                'response_time': time.time() - start_time if 'start_time' in locals() else 0,
                'success': False,
                'error': str(e)
            }
            log_query_performance(performance_data)
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    @app.get("/performance/system")
    async def get_system_performance():
        """Get overall system performance metrics"""
        try:
            def _get_system_performance():
                import psutil
                import os
                
                # Memory usage
                memory = psutil.virtual_memory()
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                
                # Process info
                process = psutil.Process(os.getpid())
                process_memory = process.memory_info()
                
                # Vector store statistics
                faiss_store = container.get('faiss_store')
                vector_stats = faiss_store.get_stats() if hasattr(faiss_store, 'get_stats') else {}
                
                return {
                    'system_resources': {
                        'memory': {
                            'total': memory.total,
                            'available': memory.available,
                            'percent_used': memory.percent,
                            'used': memory.used
                        },
                        'cpu': {
                            'percent_used': cpu_percent,
                            'core_count': psutil.cpu_count()
                        },
                        'disk': {
                            'total': disk.total,
                            'used': disk.used,
                            'free': disk.free,
                            'percent_used': (disk.used / disk.total) * 100
                        }
                    },
                    'process_resources': {
                        'memory': {
                            'rss': process_memory.rss,
                            'vms': process_memory.vms
                        },
                        'cpu_percent': process.cpu_percent(),
                        'threads': process.num_threads(),
                        'open_files': len(process.open_files())
                    },
                    'vector_store': vector_stats,
                    'query_performance': {
                        'total_logged_queries': len(query_performance_log),
                        'recent_avg_response_time': sum([log.get('response_time', 0) for log in query_performance_log[-50:]]) / min(50, len(query_performance_log)) if query_performance_log else 0
                    }
                }
            
            # Execute with timeout
            result = await asyncio.get_event_loop().run_in_executor(
                thread_pool, _get_system_performance
            )
            
            return {
                'success': True,
                'data': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting system performance: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    @app.exception_handler(UnifiedError)
    async def unified_error_handler(request, exc: UnifiedError):
        """Handle unified system errors"""
        result = Result.fail(exc.error_info)
        response_data = format_api_response(result)
        status_code = get_http_status_code(exc.error_info.code)
        return JSONResponse(response_data, status_code=status_code)

    @app.exception_handler(RAGSystemError)
    async def rag_error_handler(request, exc: RAGSystemError):
        """Handle legacy RAG system specific errors"""
        # Convert to unified error
        error_info = ErrorInfo.from_exception(exc)
        result = Result.fail(error_info)
        response_data = format_api_response(result)
        status_code = get_http_status_code(error_info.code)
        return JSONResponse(response_data, status_code=status_code)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        # Convert to unified format
        error_code = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            408: ErrorCode.TIMEOUT,
            409: ErrorCode.ALREADY_EXISTS,
            429: ErrorCode.RATE_LIMITED,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.DEPENDENCY_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE
        }.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        
        error_info = ErrorInfo(
            code=error_code,
            message=exc.detail,
            details={'status_code': exc.status_code}
        )
        
        result = Result.fail(error_info)
        response_data = format_api_response(result)
        return JSONResponse(response_data, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def general_error_handler(request, exc: Exception):
        """Handle general exceptions with unified error handling"""
        logging.error(f"Unhandled exception: {exc}", exc_info=True)
        
        # Convert to unified error
        error_info = ErrorInfo.from_exception(exc)
        result = Result.fail(error_info)
        response_data = format_api_response(result)
        status_code = get_http_status_code(error_info.code)
        
        return JSONResponse(response_data, status_code=status_code)

    # Add management API router
    if create_management_router:
        try:
            management_router = create_management_router(container)
            app.include_router(management_router)
            logging.info("✅ Management API routes registered")
        except Exception as e:
            logging.warning(f"⚠️ Management API routes not available: {e}")
    else:
        logging.warning("⚠️ Management router not available - skipping")
    
    # Add ServiceNow API router
    try:
        try:
            from .routes.servicenow import router as servicenow_router
        except ImportError:
            from rag_system.src.api.routes.servicenow import router as servicenow_router
        app.include_router(servicenow_router, prefix="/api")
        logging.info("✅ ServiceNow API routes registered")
    except Exception as e:
        logging.warning(f"⚠️ ServiceNow API routes not available: {e}")
    
    # Add conversation router
    try:
        try:
            from .routes.conversation import router as conversation_router
        except ImportError:
            from rag_system.src.api.routes.conversation import router as conversation_router
        app.include_router(conversation_router, prefix="/api")
        logging.info("✅ Conversation API routes registered")
    except Exception as e:
        logging.warning(f"⚠️ Conversation API routes not available: {e}")
    
    # Add verification router
    if verification_router:
        try:
            app.include_router(verification_router)
            logging.info("✅ Verification API routes registered")
        except Exception as e:
            logging.warning(f"⚠️ Verification API routes not available: {e}")
    else:
        logging.warning("⚠️ Verification router not available - skipping")

    # Add enhanced folder monitoring router
    if enhanced_folder_router:
        try:
            app.include_router(enhanced_folder_router, prefix="/api")
            logging.info("✅ Enhanced folder monitoring API routes registered")
        except Exception as e:
            logging.warning(f"⚠️ Enhanced folder monitoring API routes not available: {e}")
    else:
        logging.warning("⚠️ Enhanced folder monitoring router not available - skipping")

    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize resources on startup with managed resources"""
        logging.info("🚀 RAG System API starting up with managed resources...")
        
        # Register feedback store with resource manager
        if app_lifecycle:
            app_lifecycle.resource_manager.register_resource(
                "feedback_store",
                feedback_store,
                lambda fs: fs.close() if hasattr(fs, 'close') else None
            )
        
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown with comprehensive cleanup"""
        logging.info("🛑 RAG System API shutting down - cleaning up managed resources...")
        
        # Cleanup will be handled automatically by the resource manager
        if app_lifecycle:
            # Get final stats before shutdown
            stats = app_lifecycle.get_system_stats()
            logging.info(f"Final system stats: {stats}")
            
            # The global app lifecycle will handle cleanup automatically
            # Individual components don't need manual shutdown
            logging.info("✅ Managed resource cleanup initiated")
        else:
            # Fallback cleanup if resource manager not available
            if thread_pool and hasattr(thread_pool, 'shutdown'):
                thread_pool.shutdown(wait=True)
                logging.info("✅ Thread pool shutdown complete")

    # Initialize progress tracker and monitor
    progress_tracker = None
    progress_monitor = None
    
    try:
        if ProgressTracker and ProgressMonitor:
            progress_tracker = ProgressTracker(persistence_path="data/progress/ingestion_progress.json")
            progress_monitor = ProgressMonitor(progress_tracker)
            
            # Pass progress_tracker to ingestion engine
            ingestion_engine = container.get('ingestion_engine')
            if ingestion_engine and hasattr(ingestion_engine, 'progress_tracker'):
                ingestion_engine.progress_tracker = progress_tracker
                if hasattr(ingestion_engine, 'progress_helper'):
                    from ..ingestion.progress_integration import ProgressTrackedIngestion
                    ingestion_engine.progress_helper = ProgressTrackedIngestion(progress_tracker)
            
            logging.info("✅ Progress tracker initialized successfully")
        else:
            logging.warning("⚠️ Progress tracking components not available")
    except Exception as e:
        logging.error(f"❌ Failed to initialize progress tracker: {e}")
        progress_tracker = None
        progress_monitor = None

    # WebSocket endpoint for real-time progress monitoring
    @app.websocket("/ws/progress")
    async def websocket_progress(websocket: WebSocket):
        if not progress_monitor:
            await websocket.accept()
            await websocket.send_json({"error": "Progress monitoring not available"})
            await websocket.close()
            return
        
        await progress_monitor.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            progress_monitor.disconnect(websocket)
    
    # Get progress for all files
    @app.get("/progress/all")
    async def get_all_progress():
        if not progress_tracker or not progress_monitor:
            raise HTTPException(status_code=503, detail="Progress tracking not available")
        
        return {
            'files': {
                path: progress_monitor._serialize_progress(progress)
                for path, progress in progress_tracker.get_all_progress().items()
            },
            'system_metrics': progress_tracker.get_system_metrics()
        }
    
    # Get progress for a specific file
    @app.get("/progress/file/{file_path:path}")
    async def get_file_progress(file_path: str):
        if not progress_tracker or not progress_monitor:
            raise HTTPException(status_code=503, detail="Progress tracking not available")
        
        progress = progress_tracker.get_progress(file_path)
        if progress:
            return progress_monitor._serialize_progress(progress)
        else:
            raise HTTPException(status_code=404, detail="File not found in progress tracker")
    
    # Get progress for a batch
    @app.get("/progress/batch/{batch_id}")
    async def get_batch_progress(batch_id: str):
        if not progress_tracker:
            raise HTTPException(status_code=503, detail="Progress tracking not available")
        
        return progress_tracker.get_batch_progress(batch_id)
    
    # Get system metrics
    @app.get("/progress/metrics")
    async def get_progress_metrics():
        if not progress_tracker:
            raise HTTPException(status_code=503, detail="Progress tracking not available")
        
        return progress_tracker.get_system_metrics()

    logging.info("FastAPI application created")
    return app