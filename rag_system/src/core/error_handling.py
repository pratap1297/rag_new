"""
Error Handling Module - Complete error handling system
"""
import logging
from typing import Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
import traceback

# Simple unified error handling components
class ErrorCode(Enum):
    """Error codes for different types of errors"""
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    VECTOR_STORE_ERROR = "VECTOR_STORE_ERROR"
    EMBEDDING_ERROR = "EMBEDDING_ERROR"
    INGESTION_ERROR = "INGESTION_ERROR"
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"
    CHUNKING_ERROR = "CHUNKING_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    LLM_ERROR = "LLM_ERROR"
    API_KEY_ERROR = "API_KEY_ERROR"
    METADATA_ERROR = "METADATA_ERROR"
    RESOURCE_ERROR = "RESOURCE_ERROR"
    SERVICENOW_ERROR = "SERVICENOW_ERROR"
    AZURE_AI_ERROR = "AZURE_AI_ERROR"
    CONVERSATION_ERROR = "CONVERSATION_ERROR"
    FAISS_ERROR = "FAISS_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    NOT_FOUND = "NOT_FOUND"

class ErrorInfo:
    """Information about an error"""
    def __init__(self, code: ErrorCode, message: str, details: Dict[str, Any] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.context = None
    
    @classmethod
    def from_exception(cls, error: Exception, context=None):
        """Create ErrorInfo from an exception"""
        return cls(
            code=ErrorCode.INTERNAL_ERROR,
            message=str(error),
            details={'exception_type': type(error).__name__, 'traceback': traceback.format_exc()}
        )
    
    def to_user_message(self) -> str:
        """Convert to user-friendly message"""
        return self.message

class ErrorContext:
    """Context information for errors"""
    def __init__(self, operation: str = None, component: str = None):
        self.operation = operation
        self.component = component

class Result:
    """Result wrapper for operations that can fail"""
    def __init__(self, success: bool, value=None, error: ErrorInfo = None):
        self.success = success
        self.value = value
        self.error = error
    
    @classmethod
    def ok(cls, value=None):
        """Create successful result"""
        return cls(True, value=value)
    
    @classmethod
    def fail(cls, error: ErrorInfo):
        """Create failed result"""
        return cls(False, error=error)

class UnifiedError(Exception):
    """Unified error class"""
    def __init__(self, error_info: ErrorInfo):
        super().__init__(error_info.message)
        self.error_info = error_info

def with_error_handling(component: str, operation: str, default_error_code: ErrorCode):
    """Decorator for error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(operation=operation, component=component)
                error_info = ErrorInfo(
                    code=default_error_code,
                    message=str(e),
                    details={'function': func.__name__, 'args': str(args)[:100]}
                )
                error_info.context = context
                raise UnifiedError(error_info)
        return wrapper
    return decorator

def safe_execute(func, *args, **kwargs):
    """Safely execute a function and return Result"""
    try:
        result = func(*args, **kwargs)
        return Result.ok(result)
    except Exception as e:
        error_info = ErrorInfo.from_exception(e)
        return Result.fail(error_info)

def get_error_handler():
    """Get error handler instance"""
    return ErrorHandler()

class ErrorHandler:
    """Simple error handler"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error_info: ErrorInfo):
        """Handle an error"""
        self.logger.error(f"[{error_info.code.value}] {error_info.message}")
        if error_info.details:
            self.logger.debug(f"Error details: {error_info.details}")
        return Result.fail(error_info)

# Backward compatibility - keep existing exception classes
class RAGSystemError(Exception):
    """Base exception for RAG system"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}
        
        # Convert to unified error
        self.unified_error = ErrorInfo(
            code=ErrorCode(self.error_code) if hasattr(ErrorCode, self.error_code) else ErrorCode.INTERNAL_ERROR,
            message=message,
            details=details
        )

class ConfigurationError(RAGSystemError):
    """Configuration-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)

class VectorStoreError(RAGSystemError):
    """Vector store-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "VECTOR_STORE_ERROR", details)

class EmbeddingError(RAGSystemError):
    """Embedding-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "EMBEDDING_ERROR", details)

class IngestionError(RAGSystemError):
    """Ingestion-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "INGESTION_ERROR", details)

class RetrievalError(RAGSystemError):
    """Retrieval-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "RETRIEVAL_ERROR", details)

class QueryError(RAGSystemError):
    """Query-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "QUERY_ERROR", details)

class ChunkingError(RAGSystemError):
    """Chunking-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "CHUNKING_ERROR", details)

class ProcessingError(RAGSystemError):
    """Processing-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "PROCESSING_ERROR", details)

class FileProcessingError(RAGSystemError):
    """File processing-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "FILE_PROCESSING_ERROR", details)

class LLMError(RAGSystemError):
    """LLM-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "LLM_ERROR", details)

class APIKeyError(RAGSystemError):
    """API key related errors"""
    def __init__(self, provider: str, details: Dict[str, Any] = None):
        message = f"API key not found or invalid for {provider}"
        super().__init__(message, "API_KEY_ERROR", details or {"provider": provider})

class MetadataError(RAGSystemError):
    """Metadata-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "METADATA_ERROR", details)

class ResourceError(RAGSystemError):
    """Resource-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "RESOURCE_ERROR", details)

class ServiceNowError(RAGSystemError):
    """ServiceNow integration errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "SERVICENOW_ERROR", details)

class AzureAIError(RAGSystemError):
    """Azure AI integration errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "AZURE_AI_ERROR", details)

class ConversationError(RAGSystemError):
    """Conversation-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "CONVERSATION_ERROR", details)

class FAISSError(RAGSystemError):
    """FAISS-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "FAISS_ERROR", details)

class StorageError(RAGSystemError):
    """Storage-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "STORAGE_ERROR", details)

# Error tracking for system monitoring
class ErrorTracker:
    """Track and monitor system errors"""
    
    def __init__(self, log_store=None):
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 100
        self.log_store = log_store
        
    def track_error(self, error: Exception, component: str = "unknown", operation: str = "unknown"):
        """Track an error occurrence"""
        error_key = f"{component}.{operation}.{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        error_info = {
            'timestamp': ErrorInfo.from_exception(error).timestamp,
            'component': component,
            'operation': operation,
            'error_type': type(error).__name__,
            'message': str(error),
            'count': self.error_counts[error_key]
        }
        
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': len(self.error_counts),
            'error_counts': self.error_counts.copy(),
            'recent_errors': self.recent_errors[-10:]  # Last 10 errors
        }
    
    def clear_stats(self):
        """Clear error tracking statistics"""
        self.error_counts.clear()
        self.recent_errors.clear()

# Global error tracker instance
_error_tracker = None

def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker

def set_error_tracker(tracker: ErrorTracker):
    """Set the global error tracker instance"""
    global _error_tracker
    _error_tracker = tracker

# Backward compatibility functions
def handle_error(error: Exception, component: str = "unknown", 
                operation: str = "unknown", logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Legacy error handling function - converts to unified system
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    context = ErrorContext(
        operation=operation,
        component=component
    )
    
    if isinstance(error, RAGSystemError):
        error_info = error.unified_error
        error_info.context = context
    else:
        error_info = ErrorInfo.from_exception(error, context=context)
    
    # Log using unified handler
    error_handler = get_error_handler()
    result = error_handler.handle_error(error_info)
    
    # Return legacy format
    return {
        'error': True,
        'error_type': error_info.code.value,
        'message': error_info.message,
        'details': error_info.details or {},
        'component': component,
        'operation': operation
    }

def create_error_response(error_code: str, message: str, 
                         details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create standardized error response - legacy format
    """
    try:
        code = ErrorCode(error_code)
    except ValueError:
        code = ErrorCode.INTERNAL_ERROR
    
    error_info = ErrorInfo(
        code=code,
        message=message,
        details=details
    )
    
    return {
        'error': True,
        'error_code': error_info.code.value,
        'message': error_info.to_user_message(),
        'details': error_info.details or {},
        'timestamp': error_info.timestamp
    }

def log_error(error: Exception, logger: logging.Logger, 
              component: str = "unknown", operation: str = "unknown"):
    """
    Legacy error logging function
    """
    context = ErrorContext(
        operation=operation,
        component=component
    )
    
    error_info = ErrorInfo.from_exception(error, context=context)
    error_handler = get_error_handler()
    error_handler.handle_error(error_info)

# Enhanced error handling decorators for specific components
def handle_vector_store_errors(func):
    """Decorator for vector store error handling"""
    return with_error_handling("vector_store", func.__name__, ErrorCode.VECTOR_STORE_ERROR)(func)

def handle_embedding_errors(func):
    """Decorator for embedding error handling"""
    return with_error_handling("embedding", func.__name__, ErrorCode.EMBEDDING_ERROR)(func)

def handle_ingestion_errors(func):
    """Decorator for ingestion error handling"""
    return with_error_handling("ingestion", func.__name__, ErrorCode.INGESTION_ERROR)(func)

def handle_retrieval_errors(func):
    """Decorator for retrieval error handling"""
    return with_error_handling("retrieval", func.__name__, ErrorCode.RETRIEVAL_ERROR)(func)

def handle_chunking_errors(func):
    """Decorator for chunking error handling"""
    return with_error_handling("chunking", func.__name__, ErrorCode.CHUNKING_ERROR)(func)

def handle_llm_errors(func):
    """Decorator for LLM error handling"""
    return with_error_handling("llm", func.__name__, ErrorCode.LLM_ERROR)(func)

def handle_configuration_errors(func):
    """Decorator for configuration error handling"""
    return with_error_handling("configuration", func.__name__, ErrorCode.CONFIGURATION_ERROR)(func)

def handle_servicenow_errors(func):
    """Decorator for ServiceNow error handling"""
    return with_error_handling("servicenow", func.__name__, ErrorCode.SERVICENOW_ERROR)(func)

def handle_azure_ai_errors(func):
    """Decorator for Azure AI error handling"""
    return with_error_handling("azure_ai", func.__name__, ErrorCode.AZURE_AI_ERROR)(func)

# Utility functions for common error patterns
def validate_required_params(**params) -> Result:
    """Validate required parameters"""
    missing = [name for name, value in params.items() if value is None or value == ""]
    
    if missing:
        return Result.fail(ErrorInfo(
            code=ErrorCode.MISSING_PARAMETER,
            message=f"Missing required parameters: {', '.join(missing)}",
            details={'missing_parameters': missing}
        ))
    
    return Result.ok()

def validate_file_path(file_path: str) -> Result:
    """Validate file path"""
    if not file_path:
        return Result.fail(ErrorInfo(
            code=ErrorCode.MISSING_PARAMETER,
            message="File path is required"
        ))
    
    from pathlib import Path
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
    
    return Result.ok(path_obj)

def validate_query(query: str) -> Result:
    """Validate query string"""
    if not query:
        return Result.fail(ErrorInfo(
            code=ErrorCode.MISSING_PARAMETER,
            message="Query is required"
        ))
    
    if not query.strip():
        return Result.fail(ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER,
            message="Query cannot be empty"
        ))
    
    if len(query) > 10000:
        return Result.fail(ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER,
            message="Query is too long (max 10000 characters)",
            details={'query_length': len(query)}
        ))
    
    return Result.ok(query.strip())

def validate_config(config_manager, required_configs: list = None) -> Result:
    """Validate system configuration"""
    if not config_manager:
        return Result.fail(ErrorInfo(
            code=ErrorCode.CONFIGURATION_ERROR,
            message="Configuration manager is required"
        ))
    
    try:
        config = config_manager.get_config()
        
        # If specific configs are required, check them
        if required_configs:
            missing_configs = []
            for config_path in required_configs:
                # Split config path like 'llm.provider' into parts
                parts = config_path.split('.')
                current = config
                
                try:
                    for part in parts:
                        if hasattr(current, part):
                            current = getattr(current, part)
                        elif isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            missing_configs.append(config_path)
                            break
                    
                    # Check if final value is empty/None
                    if current is None or current == "":
                        missing_configs.append(config_path)
                        
                except (AttributeError, KeyError):
                    missing_configs.append(config_path)
            
            if missing_configs:
                return Result.fail(ErrorInfo(
                    code=ErrorCode.CONFIGURATION_ERROR,
                    message=f"Missing required configurations: {', '.join(missing_configs)}",
                    details={'missing_configs': missing_configs}
                ))
        
        return Result.ok(config)
        
    except Exception as e:
        return Result.fail(ErrorInfo(
            code=ErrorCode.CONFIGURATION_ERROR,
            message=f"Configuration validation failed: {str(e)}",
            details={'error': str(e)}
        ))

# Export unified error handling components for new code
__all__ = [
    # Legacy exceptions for backward compatibility
    'RAGSystemError', 'ConfigurationError', 'VectorStoreError', 'EmbeddingError',
    'IngestionError', 'RetrievalError', 'ChunkingError', 'ProcessingError',
    'LLMError', 'MetadataError', 'ResourceError', 'ServiceNowError',
    'AzureAIError', 'ConversationError', 'FAISSError', 'StorageError',
    'FileProcessingError', 'QueryError',
    
    # Legacy functions
    'handle_error', 'create_error_response', 'log_error',
    
    # Enhanced decorators
    'handle_vector_store_errors', 'handle_embedding_errors', 'handle_ingestion_errors',
    'handle_retrieval_errors', 'handle_chunking_errors', 'handle_llm_errors',
    'handle_configuration_errors', 'handle_servicenow_errors', 'handle_azure_ai_errors',
    
    # Utility functions
    'validate_required_params', 'validate_file_path', 'validate_query', 'validate_config',
    
    # Error tracking
    'ErrorTracker', 'get_error_tracker', 'set_error_tracker',
    
    # Unified system components (for new code)
    'ErrorCode', 'ErrorInfo', 'ErrorContext', 'Result', 'UnifiedError',
    'with_error_handling', 'safe_execute', 'get_error_handler'
] 