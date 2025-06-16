# -*- coding: utf-8 -*-
"""
Image Processor with Azure Computer Vision
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


class ImageProcessor(BaseProcessor):
    """Image processor with OCR capabilities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Image processor"""
        super().__init__(config)
        self.supported_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        self.logger.info("Image processor initialized")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed by this processor"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process image file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Processing image file: {file_path}")
        
        # Basic implementation - can be enhanced later
        result = {
            'status': 'success',
            'file_path': str(file_path),
            'file_name': file_path.name,
            'metadata': {
                'processor': 'image',
                'timestamp': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                **(metadata or {})
            },
            'chunks': []
        }
        
        # Create a basic chunk for now
        chunks = [{
            'text': f"Image file: {file_path.name}",
            'metadata': {
                'source': str(file_path),
                'chunk_type': 'image_placeholder'
            }
        }]
        result['chunks'] = chunks
        
        return result


def create_image_processor(config: Optional[Dict[str, Any]] = None) -> ImageProcessor:
    """Factory function to create Image processor"""
    return ImageProcessor(config) 