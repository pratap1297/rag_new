"""
Error Handling Framework
Custom exceptions and error tracking for the RAG system
"""
import traceback
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    CONFIGURATION = "configuration"
    INGESTION = "ingestion"
    RETRIEVAL = "retrieval"
    STORAGE = "storage"
    API = "api"
    LLM = "llm"
    EMBEDDING = "embedding"
    SYSTEM = "system"

# Base exceptions
class RAGSystemError(Exception):
    """Base exception for RAG system"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.traceback = traceback.format_exc()

# Configuration errors
class ConfigurationError(RAGSystemError):
    """Configuration related errors"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, ErrorCategory.CONFIGURATION, **kwargs)
        if config_key:
            self.details['config_key'] = config_key

class MissingConfigError(ConfigurationError):
    """Missing configuration error"""
    
    def __init__(self, config_key: str, **kwargs):
        message = f"Missing required configuration: {config_key}"
        super().__init__(message, config_key, severity=ErrorSeverity.HIGH, **kwargs)

# Storage errors
class StorageError(RAGSystemError):
    """Storage related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.STORAGE, **kwargs)

class FAISSError(StorageError):
    """FAISS index errors"""
    pass

class MetadataError(StorageError):
    """Metadata storage errors"""
    pass

# Ingestion errors
class IngestionError(RAGSystemError):
    """Data ingestion errors"""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        super().__init__(message, ErrorCategory.INGESTION, **kwargs)
        if file_path:
            self.details['file_path'] = file_path

class FileProcessingError(IngestionError):
    """File processing errors"""
    pass

class ChunkingError(IngestionError):
    """Text chunking errors"""
    pass

class EmbeddingError(IngestionError):
    """Embedding generation errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.EMBEDDING, **kwargs)

# Retrieval errors
class RetrievalError(RAGSystemError):
    """Query retrieval errors"""
    
    def __init__(self, message: str, query: str = None, **kwargs):
        super().__init__(message, ErrorCategory.RETRIEVAL, **kwargs)
        if query:
            self.details['query'] = query

class QueryError(RetrievalError):
    """Query processing and enhancement errors"""
    pass

class LLMError(RAGSystemError):
    """LLM related errors"""
    
    def __init__(self, message: str, provider: str = None, model: str = None, **kwargs):
        super().__init__(message, ErrorCategory.LLM, **kwargs)
        if provider:
            self.details['provider'] = provider
        if model:
            self.details['model'] = model

class APIKeyError(LLMError):
    """API key related errors"""
    
    def __init__(self, provider: str, **kwargs):
        message = f"Invalid or missing API key for {provider}"
        super().__init__(message, provider=provider, severity=ErrorSeverity.HIGH, **kwargs)

# API errors
class APIError(RAGSystemError):
    """API related errors"""
    
    def __init__(self, message: str, endpoint: str = None, status_code: int = None, **kwargs):
        super().__init__(message, ErrorCategory.API, **kwargs)
        if endpoint:
            self.details['endpoint'] = endpoint
        if status_code:
            self.details['status_code'] = status_code

class ValidationError(APIError):
    """Request validation errors"""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if field:
            self.details['field'] = field

# Integration errors
class IntegrationError(RAGSystemError):
    """Integration related errors"""
    
    def __init__(self, message: str, integration: str = None, **kwargs):
        super().__init__(message, ErrorCategory.API, **kwargs)
        if integration:
            self.details['integration'] = integration

class AuthenticationError(IntegrationError):
    """Authentication related errors"""
    
    def __init__(self, message: str, provider: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if provider:
            self.details['provider'] = provider
        self.severity = ErrorSeverity.HIGH

# Error tracking and reporting
class ErrorTracker:
    """Track and report system errors"""
    
    def __init__(self, log_store=None):
        self.log_store = log_store
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 100
    
    def track_error(self, error: RAGSystemError, context: Dict[str, Any] = None):
        """Track an error occurrence"""
        error_data = {
            'message': error.message,
            'category': error.category.value,
            'severity': error.severity.value,
            'details': error.details,
            'timestamp': error.timestamp,
            'traceback': error.traceback,
            'context': context or {}
        }
        
        # Update error counts
        error_key = f"{error.category.value}:{error.__class__.__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Add to recent errors
        self.recent_errors.append(error_data)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # Log to store if available
        if self.log_store:
            self.log_store.log_event('error', error_data)
        
        # Log to system logger
        logger = logging.getLogger(__name__)
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"[{error.category.value}] {error.message}", extra=error_data)
        else:
            logger.warning(f"[{error.category.value}] {error.message}", extra=error_data)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        total_errors = sum(self.error_counts.values())
        
        # Group by category
        category_counts = {}
        for error_key, count in self.error_counts.items():
            category = error_key.split(':')[0]
            category_counts[category] = category_counts.get(category, 0) + count
        
        # Get severity distribution from recent errors
        severity_counts = {}
        for error in self.recent_errors:
            severity = error['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_errors': total_errors,
            'category_counts': category_counts,
            'severity_counts': severity_counts,
            'error_types': self.error_counts,
            'recent_error_count': len(self.recent_errors)
        }
    
    def get_recent_errors(self, limit: int = 10, category: str = None, 
                         severity: str = None) -> List[Dict[str, Any]]:
        """Get recent errors with optional filtering"""
        errors = self.recent_errors.copy()
        
        # Filter by category
        if category:
            errors = [e for e in errors if e['category'] == category]
        
        # Filter by severity
        if severity:
            errors = [e for e in errors if e['severity'] == severity]
        
        # Sort by timestamp (most recent first)
        errors.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return errors[:limit]
    
    def clear_error_history(self):
        """Clear error tracking history"""
        self.error_counts.clear()
        self.recent_errors.clear()

# Error handling decorators
def handle_errors(error_tracker = None, 
                 default_category: ErrorCategory = ErrorCategory.SYSTEM,
                 reraise: bool = True):
    """Decorator to handle and track errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RAGSystemError as e:
                if error_tracker:
                    error_tracker.track_error(e, {'function': func.__name__})
                if reraise:
                    raise
                return None
            except Exception as e:
                # Convert to RAGSystemError
                rag_error = RAGSystemError(
                    str(e), 
                    category=default_category,
                    severity=ErrorSeverity.MEDIUM,
                    details={'original_exception': type(e).__name__}
                )
                if error_tracker:
                    error_tracker.track_error(rag_error, {'function': func.__name__})
                if reraise:
                    raise rag_error
                return None
        return wrapper
    return decorator

def validate_config(config_manager, required_keys: List[str]):
    """Validate required configuration keys"""
    missing_keys = []
    
    for key in required_keys:
        try:
            # Support nested keys like 'llm.api_key'
            keys = key.split('.')
            value = config_manager.get_config()
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    missing_keys.append(key)
                    break
            
            if value is None:
                missing_keys.append(key)
                
        except Exception:
            missing_keys.append(key)
    
    if missing_keys:
        raise MissingConfigError(
            f"Missing required configuration keys: {', '.join(missing_keys)}"
        )

# Global error tracker instance
_global_error_tracker = None

def get_error_tracker():
    """Get global error tracker instance"""
    global _global_error_tracker
    if _global_error_tracker is None:
        _global_error_tracker = ErrorTracker()
    return _global_error_tracker

def set_error_tracker(tracker):
    """Set global error tracker instance"""
    global _global_error_tracker
    _global_error_tracker = tracker 