"""
System Constants
Defines embedding dimensions and other system-wide constants

IMPORTANT: This file should NOT import from other modules in the project
to prevent circular import issues. Keep it as a pure constants file.
"""

# Embedding dimensions by provider and model
EMBEDDING_DIMENSIONS = {
    'sentence-transformers': {
        'all-MiniLM-L6-v2': 384,
        'all-mpnet-base-v2': 768,
        'all-distilroberta-v1': 768,
    },
    'cohere': {
        'embed-english-v3.0': 1024,
        'embed-multilingual-v3.0': 1024,
        'embed-english-light-v3.0': 384,
    },
    'azure': {
        'Cohere-embed-v3-english': 1024,
        'Cohere-embed-v3-multilingual': 1024,
        'text-embedding-ada-002': 1536,
        'text-embedding-3-small': 1536,
        'text-embedding-3-large': 3072,
    },
    'openai': {
        'text-embedding-ada-002': 1536,
        'text-embedding-3-small': 1536,
        'text-embedding-3-large': 3072,
    }
}

# Default embedding configurations
DEFAULT_EMBEDDING_CONFIG = {
    'sentence-transformers': {
        'model': 'sentence-transformers/all-MiniLM-L6-v2',
        'dimension': 384
    },
    'cohere': {
        'model': 'embed-english-v3.0',
        'dimension': 1024
    },
    'azure': {
        'model': 'Cohere-embed-v3-english',
        'dimension': 1024
    },
    'openai': {
        'model': 'text-embedding-ada-002',
        'dimension': 1536
    }
}

# System limits
MAX_FILE_SIZE_MB = 100
MAX_CHUNK_SIZE = 2000
MIN_CHUNK_SIZE = 100
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# API limits
MAX_QUERY_LENGTH = 1000
MAX_RESULTS_PER_QUERY = 50
DEFAULT_TOP_K = 5

# Thread pool settings
DEFAULT_THREAD_POOL_SIZE = 4
MAX_THREAD_POOL_SIZE = 16

def get_embedding_dimension(provider: str, model_name: str) -> int:
    """Get embedding dimension for a specific provider and model
    
    Args:
        provider: The embedding provider (e.g., 'azure', 'cohere', 'sentence-transformers')
        model_name: The model name (can include path separators)
        
    Returns:
        int: The embedding dimension for the specified provider and model
        
    Note:
        This function is kept import-free to prevent circular dependencies.
        If you need to import modules, consider using lazy imports or 
        restructuring the code to avoid circular dependencies.
    """
    if not provider or not model_name:
        # Fallback to default if invalid input
        return 384
        
    if provider in EMBEDDING_DIMENSIONS:
        # Extract model name from full path if needed
        model_key = model_name.split('/')[-1] if '/' in model_name else model_name
        
        if model_key in EMBEDDING_DIMENSIONS[provider]:
            return EMBEDDING_DIMENSIONS[provider][model_key]
        
        # Return default for provider if specific model not found
        if provider in DEFAULT_EMBEDDING_CONFIG:
            return DEFAULT_EMBEDDING_CONFIG[provider]['dimension']
    
    # Fallback to sentence-transformers default
    return 384

def get_default_model_for_provider(provider: str) -> tuple:
    """Get default model name and dimension for a provider"""
    if provider in DEFAULT_EMBEDDING_CONFIG:
        config = DEFAULT_EMBEDDING_CONFIG[provider]
        return config['model'], config['dimension']
    
    # Fallback
    return 'sentence-transformers/all-MiniLM-L6-v2', 384

def safe_import_and_call(module_path: str, function_name: str, *args, **kwargs):
    """Safely import a module and call a function to avoid circular imports
    
    This utility function can be used when you need to import from other modules
    within constants.py functions, though it's generally better to avoid this.
    
    Args:
        module_path: The module path to import from
        function_name: The function name to call
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function call, or None if import fails
    """
    try:
        import importlib
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        return func(*args, **kwargs)
    except (ImportError, AttributeError) as e:
        print(f"Warning: Could not import {module_path}.{function_name}: {e}")
        return None 