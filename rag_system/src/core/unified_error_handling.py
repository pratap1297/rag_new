"""
Unified Error Handling System
Standardizes error handling patterns across the RAG system
"""
from typing import Optional, Dict, Any, Union, TypeVar, Callable, List
from enum import Enum
from dataclasses import dataclass, field
import logging
import traceback
from functools import wraps
import json
from datetime import datetime
import uuid

T = TypeVar('T')

class ErrorCode(Enum):
    """Standardized error codes for the RAG system"""
    # Success
    SUCCESS = "SUCCESS"
    
    # Client errors (4xx equivalent)
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    RATE_LIMITED = "RATE_LIMITED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    
    # Server errors (5xx equivalent)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    
    # RAG-specific errors
    VECTOR_STORE_ERROR = "VECTOR_STORE_ERROR"
    EMBEDDING_ERROR = "EMBEDDING_ERROR"
    LLM_ERROR = "LLM_ERROR"
    INGESTION_ERROR = "INGESTION_ERROR"
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    CHUNKING_ERROR = "CHUNKING_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    RESOURCE_ERROR = "RESOURCE_ERROR"
    METADATA_ERROR = "METADATA_ERROR"
    AZURE_AI_ERROR = "AZURE_AI_ERROR"
    SERVICENOW_ERROR = "SERVICENOW_ERROR"
    CONVERSATION_ERROR = "CONVERSATION_ERROR"

@dataclass
class ErrorContext:
    """Context information for errors"""
    operation: str
    component: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'operation': self.operation,
            'component': self.component,
            'user_id': self.user_id,
            'request_id': self.request_id,
            'session_id': self.session_id,
            'file_path': self.file_path,
            'metadata': self.metadata
        }

@dataclass
class ErrorInfo:
    """Unified error information"""
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    context: Optional[ErrorContext] = None
    cause: Optional[Exception] = None
    stack_trace: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    severity: str = "ERROR"  # ERROR, WARNING, INFO
    
    def __post_init__(self):
        if self.cause and not self.stack_trace:
            self.stack_trace = traceback.format_exc()
        
        # Set severity based on error code
        if self.code in [ErrorCode.INVALID_REQUEST, ErrorCode.NOT_FOUND, ErrorCode.MISSING_PARAMETER]:
            self.severity = "WARNING"
        elif self.code in [ErrorCode.ALREADY_EXISTS]:
            self.severity = "INFO"
    
    @staticmethod
    def from_exception(e: Exception, code: ErrorCode = None, 
                      context: ErrorContext = None) -> 'ErrorInfo':
        """Create ErrorInfo from exception"""
        if isinstance(e, UnifiedError):
            return e.error_info
        
        # Map exception types to error codes
        error_code = code or _map_exception_to_code(e)
        
        return ErrorInfo(
            code=error_code,
            message=str(e),
            cause=e,
            context=context,
            stack_trace=traceback.format_exc()
        )
    
    def to_dict(self, include_stack_trace: bool = None) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        if include_stack_trace is None:
            include_stack_trace = logging.getLogger().level <= logging.DEBUG
        
        return {
            'code': self.code.value,
            'message': self.message,
            'details': self.details,
            'context': self.context.to_dict() if self.context else None,
            'timestamp': self.timestamp,
            'severity': self.severity,
            'stack_trace': self.stack_trace if include_stack_trace else None
        }
    
    def to_user_message(self) -> str:
        """Get user-friendly error message"""
        user_messages = {
            ErrorCode.INVALID_REQUEST: "Your request could not be processed. Please check your input.",
            ErrorCode.MISSING_PARAMETER: "Required parameter is missing. Please check your request.",
            ErrorCode.INVALID_PARAMETER: "Invalid parameter provided. Please check your input.",
            ErrorCode.NOT_FOUND: "The requested resource was not found.",
            ErrorCode.ALREADY_EXISTS: "The resource already exists.",
            ErrorCode.RATE_LIMITED: "Too many requests. Please try again later.",
            ErrorCode.UNAUTHORIZED: "Authentication required.",
            ErrorCode.FORBIDDEN: "Access denied.",
            ErrorCode.SERVICE_UNAVAILABLE: "Service temporarily unavailable. Please try again.",
            ErrorCode.INTERNAL_ERROR: "An unexpected error occurred. Please try again.",
            ErrorCode.TIMEOUT: "The operation timed out. Please try again.",
            ErrorCode.RESOURCE_EXHAUSTED: "System resources are temporarily exhausted.",
            ErrorCode.VECTOR_STORE_ERROR: "Error accessing the knowledge base.",
            ErrorCode.EMBEDDING_ERROR: "Error processing your query.",
            ErrorCode.LLM_ERROR: "Error generating response.",
            ErrorCode.INGESTION_ERROR: "Error processing the document.",
            ErrorCode.RETRIEVAL_ERROR: "Error retrieving information.",
            ErrorCode.PROCESSING_ERROR: "Error processing your request.",
            ErrorCode.CHUNKING_ERROR: "Error processing document content.",
            ErrorCode.CONFIGURATION_ERROR: "System configuration error.",
            ErrorCode.AZURE_AI_ERROR: "Error with Azure AI service.",
            ErrorCode.SERVICENOW_ERROR: "Error with ServiceNow integration.",
            ErrorCode.CONVERSATION_ERROR: "Error in conversation processing."
        }
        
        return user_messages.get(self.code, self.message)

@dataclass
class Result:
    """Standardized result wrapper"""
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorInfo] = None
    warnings: List[ErrorInfo] = field(default_factory=list)
    
    @staticmethod
    def ok(data: Any = None, warnings: List[ErrorInfo] = None) -> 'Result':
        """Create success result"""
        return Result(success=True, data=data, warnings=warnings or [])
    
    @staticmethod
    def fail(error: ErrorInfo) -> 'Result':
        """Create failure result"""
        return Result(success=False, error=error)
    
    @staticmethod
    def from_exception(e: Exception, context: ErrorContext = None) -> 'Result':
        """Create failure result from exception"""
        error_info = ErrorInfo.from_exception(e, context=context)
        return Result.fail(error_info)
    
    def unwrap(self) -> Any:
        """Get data or raise exception"""
        if self.success:
            return self.data
        else:
            raise UnifiedError(self.error)
    
    def unwrap_or(self, default: Any) -> Any:
        """Get data or return default"""
        return self.data if self.success else default
    
    def map(self, func: Callable[[Any], Any]) -> 'Result':
        """Map function over successful result"""
        if self.success:
            try:
                new_data = func(self.data)
                return Result.ok(new_data, self.warnings)
            except Exception as e:
                error_info = ErrorInfo.from_exception(e)
                return Result.fail(error_info)
        return self
    
    def and_then(self, func: Callable[[Any], 'Result']) -> 'Result':
        """Chain operations that return Results"""
        if self.success:
            try:
                new_result = func(self.data)
                if isinstance(new_result, Result):
                    if new_result.success:
                        # Combine warnings
                        all_warnings = self.warnings + new_result.warnings
                        return Result.ok(new_result.data, all_warnings)
                    else:
                        return new_result
                else:
                    return Result.ok(new_result, self.warnings)
            except Exception as e:
                error_info = ErrorInfo.from_exception(e)
                return Result.fail(error_info)
        return self
    
    def add_warning(self, warning: ErrorInfo) -> 'Result':
        """Add warning to result"""
        self.warnings.append(warning)
        return self

class UnifiedError(Exception):
    """Unified exception class"""
    
    def __init__(self, error_info: ErrorInfo):
        self.error_info = error_info
        super().__init__(error_info.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.error_info.to_dict()

def _map_exception_to_code(e: Exception) -> ErrorCode:
    """Map exception type to error code"""
    exception_mapping = {
        ValueError: ErrorCode.INVALID_PARAMETER,
        KeyError: ErrorCode.MISSING_PARAMETER,
        FileNotFoundError: ErrorCode.NOT_FOUND,
        TimeoutError: ErrorCode.TIMEOUT,
        ConnectionError: ErrorCode.SERVICE_UNAVAILABLE,
        PermissionError: ErrorCode.UNAUTHORIZED,
        MemoryError: ErrorCode.RESOURCE_EXHAUSTED,
        OSError: ErrorCode.RESOURCE_ERROR,
    }
    
    # Check for specific error types in the RAG system
    error_str = str(e).lower()
    if any(term in error_str for term in ['vector', 'faiss', 'index']):
        return ErrorCode.VECTOR_STORE_ERROR
    elif any(term in error_str for term in ['embedding', 'encode']):
        return ErrorCode.EMBEDDING_ERROR
    elif any(term in error_str for term in ['llm', 'openai', 'azure']):
        return ErrorCode.LLM_ERROR
    elif any(term in error_str for term in ['chunk', 'split']):
        return ErrorCode.CHUNKING_ERROR
    elif any(term in error_str for term in ['ingest', 'process']):
        return ErrorCode.INGESTION_ERROR
    elif any(term in error_str for term in ['retriev', 'search']):
        return ErrorCode.RETRIEVAL_ERROR
    elif any(term in error_str for term in ['config', 'setting']):
        return ErrorCode.CONFIGURATION_ERROR
    elif any(term in error_str for term in ['servicenow']):
        return ErrorCode.SERVICENOW_ERROR
    elif any(term in error_str for term in ['azure']):
        return ErrorCode.AZURE_AI_ERROR
    
    # Check exception type mapping
    for exc_type, code in exception_mapping.items():
        if isinstance(e, exc_type):
            return code
    
    return ErrorCode.INTERNAL_ERROR

class ErrorHandler:
    """Centralized error handler"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_callbacks: Dict[ErrorCode, List[Callable]] = {}
        self.global_callbacks: List[Callable] = []
        self.error_stats: Dict[ErrorCode, int] = {}
    
    def register_callback(self, callback: Callable[[ErrorInfo], None], 
                         error_code: Optional[ErrorCode] = None):
        """Register error callback"""
        if error_code:
            if error_code not in self.error_callbacks:
                self.error_callbacks[error_code] = []
            self.error_callbacks[error_code].append(callback)
        else:
            self.global_callbacks.append(callback)
    
    def handle_error(self, error_info: ErrorInfo) -> Result:
        """Handle error with callbacks and logging"""
        # Update statistics
        self.error_stats[error_info.code] = self.error_stats.get(error_info.code, 0) + 1
        
        # Log error
        self._log_error(error_info)
        
        # Execute specific callbacks
        if error_info.code in self.error_callbacks:
            for callback in self.error_callbacks[error_info.code]:
                try:
                    callback(error_info)
                except Exception as e:
                    self.logger.error(f"Error in callback: {e}")
        
        # Execute global callbacks
        for callback in self.global_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"Error in global callback: {e}")
        
        return Result.fail(error_info)
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        log_data = error_info.to_dict(include_stack_trace=False)
        
        if error_info.severity == "ERROR":
            if error_info.code in [ErrorCode.INTERNAL_ERROR, ErrorCode.SERVICE_UNAVAILABLE]:
                self.logger.error(f"Error [{error_info.code.value}]: {error_info.message}", 
                                extra=log_data)
            else:
                self.logger.error(f"Error [{error_info.code.value}]: {error_info.message}", 
                                extra=log_data)
        elif error_info.severity == "WARNING":
            self.logger.warning(f"Warning [{error_info.code.value}]: {error_info.message}", 
                              extra=log_data)
        else:
            self.logger.info(f"Info [{error_info.code.value}]: {error_info.message}", 
                           extra=log_data)
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return {code.value: count for code, count in self.error_stats.items()}

# Global error handler
_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """Get global error handler"""
    return _error_handler

def with_error_handling(component: str, operation: str, 
                       error_code: ErrorCode = None):
    """Decorator for unified error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(
                operation=operation,
                component=component,
                request_id=kwargs.get('request_id'),
                user_id=kwargs.get('user_id'),
                session_id=kwargs.get('session_id'),
                file_path=kwargs.get('file_path')
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Wrap non-Result returns
                if not isinstance(result, Result):
                    return Result.ok(result)
                
                return result
                
            except Exception as e:
                error_info = ErrorInfo.from_exception(
                    e, 
                    code=error_code, 
                    context=context
                )
                return _error_handler.handle_error(error_info)
        
        return wrapper
    return decorator

def safe_execute(func: Callable[[], T], 
                context: ErrorContext = None,
                default: T = None,
                error_code: ErrorCode = None) -> Result:
    """Safely execute a function and return Result"""
    try:
        result = func()
        return Result.ok(result)
    except Exception as e:
        error_info = ErrorInfo.from_exception(e, code=error_code, context=context)
        return _error_handler.handle_error(error_info)

# Component-specific error handlers
class VectorStoreErrorHandler:
    """Error handling for vector store operations"""
    
    @staticmethod
    @with_error_handling("vector_store", "add_vectors", ErrorCode.VECTOR_STORE_ERROR)
    def add_vectors(store, vectors, metadata) -> Result:
        """Add vectors with error handling"""
        if not vectors:
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message="Vectors list cannot be empty"
            ))
        
        if metadata and len(metadata) != len(vectors):
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message="Metadata list length must match vectors list length"
            ))
        
        try:
            vector_ids = store.add_vectors(vectors, metadata)
            return Result.ok(vector_ids)
        except Exception as e:
            if "dimension" in str(e):
                return Result.fail(ErrorInfo(
                    code=ErrorCode.INVALID_PARAMETER,
                    message=f"Vector dimension mismatch: {e}",
                    details={'expected_dimension': getattr(store, 'dimension', None)}
                ))
            raise

    @staticmethod
    @with_error_handling("vector_store", "search", ErrorCode.VECTOR_STORE_ERROR)
    def search(store, query_vector, k=5) -> Result:
        """Search with error handling"""
        if not query_vector:
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message="Query vector cannot be empty"
            ))
        
        if k <= 0:
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message="k must be greater than 0"
            ))
        
        try:
            results = store.search(query_vector, k)
            return Result.ok(results)
        except Exception as e:
            if "empty index" in str(e).lower():
                return Result.ok([])  # Return empty results for empty index
            raise

class IngestionErrorHandler:
    """Error handling for ingestion operations"""
    
    @staticmethod
    @with_error_handling("ingestion", "ingest_file", ErrorCode.INGESTION_ERROR)
    def ingest_file(engine, file_path, metadata=None) -> Result:
        """Ingest file with error handling"""
        from pathlib import Path
        
        # Validate input
        if not file_path:
            return Result.fail(ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER,
                message="File path is required"
            ))
        
        path_obj = Path(file_path)
        if not path_obj.exists():
            return Result.fail(ErrorInfo(
                code=ErrorCode.NOT_FOUND,
                message=f"File not found: {file_path}",
                details={'file_path': str(file_path)}
            ))
        
        if not path_obj.is_file():
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message=f"Path is not a file: {file_path}",
                details={'file_path': str(file_path)}
            ))
        
        try:
            result = engine.ingest_file(file_path, metadata)
            return Result.ok(result)
        except Exception as e:
            error_str = str(e).lower()
            if "unsupported format" in error_str or "format not supported" in error_str:
                return Result.fail(ErrorInfo(
                    code=ErrorCode.INVALID_REQUEST,
                    message=f"Unsupported file format: {path_obj.suffix}",
                    details={'file_path': str(file_path), 'file_extension': path_obj.suffix}
                ))
            elif "permission" in error_str:
                return Result.fail(ErrorInfo(
                    code=ErrorCode.FORBIDDEN,
                    message=f"Permission denied accessing file: {file_path}",
                    details={'file_path': str(file_path)}
                ))
            raise

class QueryErrorHandler:
    """Error handling for query operations"""
    
    @staticmethod
    @with_error_handling("query", "process_query", ErrorCode.RETRIEVAL_ERROR)
    def process_query(engine, query, **kwargs) -> Result:
        """Process query with error handling"""
        # Validate input
        if not query:
            return Result.fail(ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER,
                message="Query is required"
            ))
        
        if not query.strip():
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message="Query cannot be empty or whitespace only"
            ))
        
        if len(query.strip()) > 10000:  # Reasonable limit
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message="Query is too long (max 10000 characters)",
                details={'query_length': len(query)}
            ))
        
        try:
            results = engine.process_query(query, **kwargs)
            return Result.ok(results)
        except Exception as e:
            error_str = str(e).lower()
            if "no results" in error_str or "not found" in error_str:
                return Result.ok({
                    'query': query,
                    'response': "No relevant information found for your query.",
                    'sources': [],
                    'confidence_score': 0.0
                })
            elif "timeout" in error_str:
                return Result.fail(ErrorInfo(
                    code=ErrorCode.TIMEOUT,
                    message="Query processing timed out",
                    details={'query': query[:100]}  # First 100 chars for debugging
                ))
            raise

class ChunkingErrorHandler:
    """Error handling for chunking operations"""
    
    @staticmethod
    @with_error_handling("chunking", "chunk_text", ErrorCode.CHUNKING_ERROR)
    def chunk_text(chunker, text, metadata=None) -> Result:
        """Chunk text with error handling"""
        if not text:
            return Result.ok([])  # Empty text returns empty chunks
        
        if len(text) > 1000000:  # 1MB limit
            return Result.fail(ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER,
                message="Text is too large for chunking (max 1MB)",
                details={'text_length': len(text)}
            ))
        
        try:
            chunks = chunker.chunk_text(text, metadata)
            return Result.ok(chunks)
        except Exception as e:
            error_str = str(e).lower()
            if "model" in error_str and "load" in error_str:
                return Result.fail(ErrorInfo(
                    code=ErrorCode.RESOURCE_ERROR,
                    message="Failed to load chunking model",
                    details={'chunker_type': type(chunker).__name__}
                ))
            raise

# API response formatting
def format_api_response(result: Result, include_warnings: bool = True) -> Dict[str, Any]:
    """Format Result for API response"""
    if result.success:
        response = {
            'success': True,
            'data': result.data
        }
        
        if include_warnings and result.warnings:
            response['warnings'] = [
                {
                    'code': warning.code.value,
                    'message': warning.to_user_message()
                }
                for warning in result.warnings
            ]
        
        return response
    else:
        return {
            'success': False,
            'error': result.error.to_user_message(),
            'error_code': result.error.code.value,
            'error_details': result.error.details,
            'request_id': result.error.context.request_id if result.error.context else None
        }

def get_http_status_code(error_code: ErrorCode) -> int:
    """Map error code to HTTP status code"""
    status_mapping = {
        ErrorCode.SUCCESS: 200,
        ErrorCode.INVALID_REQUEST: 400,
        ErrorCode.MISSING_PARAMETER: 400,
        ErrorCode.INVALID_PARAMETER: 400,
        ErrorCode.NOT_FOUND: 404,
        ErrorCode.ALREADY_EXISTS: 409,
        ErrorCode.UNAUTHORIZED: 401,
        ErrorCode.FORBIDDEN: 403,
        ErrorCode.RATE_LIMITED: 429,
        ErrorCode.TIMEOUT: 408,
        ErrorCode.RESOURCE_EXHAUSTED: 429,
        ErrorCode.SERVICE_UNAVAILABLE: 503,
        ErrorCode.INTERNAL_ERROR: 500,
        ErrorCode.DEPENDENCY_ERROR: 502,
        ErrorCode.VECTOR_STORE_ERROR: 500,
        ErrorCode.EMBEDDING_ERROR: 500,
        ErrorCode.LLM_ERROR: 500,
        ErrorCode.INGESTION_ERROR: 500,
        ErrorCode.RETRIEVAL_ERROR: 500,
        ErrorCode.PROCESSING_ERROR: 500,
        ErrorCode.CHUNKING_ERROR: 500,
        ErrorCode.CONFIGURATION_ERROR: 500,
        ErrorCode.RESOURCE_ERROR: 500,
        ErrorCode.METADATA_ERROR: 500,
        ErrorCode.AZURE_AI_ERROR: 502,
        ErrorCode.SERVICENOW_ERROR: 502,
        ErrorCode.CONVERSATION_ERROR: 500,
    }
    
    return status_mapping.get(error_code, 500) 