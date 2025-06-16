# -*- coding: utf-8 -*-
"""
Word Document Processor
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .base_processor import BaseProcessor
except ImportError:
    class BaseProcessor:
        def __init__(self, config=None):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)


class WordProcessor(BaseProcessor):
    """Word document processor for .docx files"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Word processor"""
        super().__init__(config)
        self.supported_extensions = ['.docx', '.doc']
        self.logger.info("Word processor initialized")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed by this processor"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process Word document file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Processing Word file: {file_path}")
        
        # Basic implementation - can be enhanced later
        result = {
            'status': 'success',
            'file_path': str(file_path),
            'file_name': file_path.name,
            'metadata': {
                'processor': 'word',
                'timestamp': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                **(metadata or {})
            },
            'chunks': []
        }
        
        # Create a basic chunk for now
        chunks = [{
            'text': f"Word document: {file_path.name}",
            'metadata': {
                'source': str(file_path),
                'chunk_type': 'word_placeholder'
            }
        }]
        result['chunks'] = chunks
        
        return result


def create_word_processor(config: Optional[Dict[str, Any]] = None) -> WordProcessor:
    """Factory function to create Word processor"""
    return WordProcessor(config) 