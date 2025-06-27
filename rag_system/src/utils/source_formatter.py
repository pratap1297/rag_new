"""
Utility functions for formatting source displays with original path information.
"""

from pathlib import Path
from typing import Dict, Any, Optional


def format_source_display(source: Dict[str, Any]) -> str:
    """
    Format a source for display, prioritizing original file information.
    
    Args:
        source: Source dictionary containing metadata
        
    Returns:
        Formatted string for display
    """
    # Get the best available original file information
    original_file = (
        source.get('original_filename') or 
        source.get('original_name') or
        source.get('display_name') or
        source.get('filename') or
        source.get('file_path', '')
    )
    
    if not original_file:
        # Fallback to extracting filename from path
        file_path = source.get('file_path', '')
        if file_path:
            original_file = Path(file_path).name
        else:
            original_file = "Unknown Source"
    
    # Check if this is a temp file
    is_temp = (
        'Temp' in original_file or 
        'tmp' in original_file.lower() or
        '/tmp/' in original_file or
        '\\temp\\' in original_file.lower()
    )
    
    # If it's a temp file, try to get the original name
    if is_temp:
        original_name = source.get('original_name') or source.get('display_name')
        if original_name:
            original_file = original_name
    
    # Format the display
    if '/' in original_file or '\\' in original_file:
        # For full paths, show a shortened version
        path_parts = original_file.replace('\\', '/').split('/')
        if len(path_parts) > 3:
            display_path = f".../{'/'.join(path_parts[-3:])}"
        else:
            display_path = original_file
        return f"📄 **{display_path}**"
    else:
        return f"📄 **{original_file}**"


def get_source_metadata_summary(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metadata for source summary.
    
    Args:
        source: Source dictionary containing metadata
        
    Returns:
        Dictionary with key metadata fields
    """
    return {
        'original_filename': source.get('original_filename'),
        'original_name': source.get('original_name'),
        'display_name': source.get('display_name'),
        'file_path': source.get('file_path'),
        'filename': source.get('filename'),
        'upload_source': source.get('upload_source'),
        'upload_timestamp': source.get('upload_timestamp'),
        'is_temp_file': source.get('is_temp_file', False),
        'source_type': source.get('source_type'),
        'doc_id': source.get('doc_id'),
        'chunk_id': source.get('chunk_id')
    }


def format_search_result_for_display(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a search result for frontend display with enhanced source information.
    
    Args:
        result: Raw search result from query engine
        
    Returns:
        Formatted result for display
    """
    # Extract source information
    source_info = get_source_metadata_summary(result)
    
    # Format the display
    formatted_result = {
        'content': result.get('text', ''),
        'score': result.get('similarity_score', 0),
        'source_display': format_source_display(result),
        'source_info': source_info,
        'metadata': result.get('metadata', {}),
        'doc_id': result.get('doc_id'),
        'chunk_id': result.get('chunk_id')
    }
    
    return formatted_result


def is_temp_file_path(file_path: str) -> bool:
    """
    Check if a file path is a temporary file path.
    
    Args:
        file_path: File path to check
        
    Returns:
        True if it's a temp file path, False otherwise
    """
    if not file_path:
        return False
    
    temp_indicators = [
        'Temp',
        'tmp',
        '/tmp/',
        '\\temp\\',
        'tempfile',
        'temp_file'
    ]
    
    file_path_lower = file_path.lower()
    return any(indicator.lower() in file_path_lower for indicator in temp_indicators)


def get_original_filename(source: Dict[str, Any]) -> Optional[str]:
    """
    Get the best available original filename from a source.
    
    Args:
        source: Source dictionary containing metadata
        
    Returns:
        Original filename if available, None otherwise
    """
    # Priority order for original filename
    filename_options = [
        source.get('original_filename'),
        source.get('original_name'),
        source.get('display_name'),
        source.get('filename')
    ]
    
    for option in filename_options:
        if option and not is_temp_file_path(option):
            return option
    
    # If all options are temp files or None, return the first non-None option
    for option in filename_options:
        if option:
            return option
    
    return None 