# -*- coding: utf-8 -*-
"""
Text Processor for plain text and code files
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

try:
    from .base_processor import BaseProcessor
except ImportError:
    class BaseProcessor:
        def __init__(self, config=None):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)


class TextProcessor(BaseProcessor):
    """Text processor for plain text and code files"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Text processor"""
        super().__init__(config)
        self.supported_extensions = [
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', 
            '.csv', '.log', '.sql', '.sh', '.bat', '.yaml', '.yml'
        ]
        self.logger.info("Text processor initialized")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed by this processor"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def detect_language(self, text: str) -> str:
        """Simple language detection based on content"""
        if re.search(r'\bdef\s+\w+\s*\(', text):
            return 'python'
        elif re.search(r'\bfunction\s+\w+\s*\(', text):
            return 'javascript'
        elif re.search(r'<html|<div|<span', text, re.IGNORECASE):
            return 'html'
        elif re.search(r'SELECT|FROM|WHERE', text, re.IGNORECASE):
            return 'sql'
        else:
            return 'text'
    
    def detect_content_type(self, text: str) -> str:
        """Detect content type"""
        if re.search(r'^\s*{.*}\s*$', text, re.DOTALL):
            return 'json'
        elif re.search(r'^\s*<\?xml', text):
            return 'xml'
        elif ',' in text and '\n' in text:
            return 'csv'
        else:
            return 'plain_text'
    
    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process text file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Processing text file: {file_path}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Analyze content
        word_count = len(content.split())
        char_count = len(content)
        line_count = len(content.splitlines())
        language = self.detect_language(content)
        content_type = self.detect_content_type(content)
        
        result = {
            'status': 'success',
            'file_path': str(file_path),
            'file_name': file_path.name,
            'metadata': {
                'processor': 'text',
                'timestamp': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                'word_count': word_count,
                'char_count': char_count,
                'line_count': line_count,
                'language': language,
                'content_type': content_type,
                **(metadata or {})
            },
            'chunks': []
        }
        
        # Create chunks (simple implementation)
        chunk_size = self.config.get('chunk_size', 1000)
        chunks = []
        
        if len(content) <= chunk_size:
            chunks.append({
                'text': content,
                'metadata': {
                    'source_type': 'text',
                    'content_type': 'full_document',
                    'chunk_index': 0,
                    'file_path': str(file_path),
                    'language': language,
                    'content_type_detected': content_type,
                    'word_count': word_count,
                    'line_count': line_count
                }
            })
        else:
            # Split into chunks
            for i in range(0, len(content), chunk_size):
                chunk_text = content[i:i + chunk_size]
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'source_type': 'text',
                        'content_type': 'text_chunk',
                        'chunk_index': len(chunks),
                        'start_char': i,
                        'end_char': min(i + chunk_size, len(content)),
                        'file_path': str(file_path),
                        'language': language,
                        'content_type_detected': content_type
                    }
                })
        
        result['chunks'] = chunks
        return result


def create_text_processor(config: Optional[Dict[str, Any]] = None) -> TextProcessor:
    """Factory function to create Text processor"""
    return TextProcessor(config) 