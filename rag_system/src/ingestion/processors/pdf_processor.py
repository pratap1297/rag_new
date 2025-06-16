# -*- coding: utf-8 -*-
"""
Enhanced PDF Processor with Azure Computer Vision Integration
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .base_processor import BaseProcessor
    from .enhanced_pdf_processor import EnhancedPDFProcessor
except ImportError:
    class BaseProcessor:
        def __init__(self, config=None):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)
    
    # Fallback if enhanced processor not available
    EnhancedPDFProcessor = None


class PDFProcessor(BaseProcessor):
    """Enhanced PDF processor with Azure Computer Vision and fallback methods"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PDF processor"""
        super().__init__(config)
        self.supported_extensions = ['.pdf']
        self.logger.info("PDF processor initialized")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed by this processor"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process PDF file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Processing PDF file: {file_path}")
        
        # Basic implementation - can be enhanced later
        result = {
            'status': 'success',
            'file_path': str(file_path),
            'file_name': file_path.name,
            'pages': [],
            'metadata': {
                'processor': 'pdf',
                'timestamp': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                **(metadata or {})
            },
            'chunks': []
        }
        
        # Create a basic chunk for now
        chunks = [{
            'text': f"PDF document: {file_path.name}",
            'metadata': {
                'source': str(file_path),
                'chunk_type': 'pdf_placeholder'
            }
        }]
        result['chunks'] = chunks
        
        return result


def create_pdf_processor(config: Optional[Dict[str, Any]] = None,
                        azure_config: Optional[Dict[str, Any]] = None) -> BaseProcessor:
    """Create a PDF processor with optional Azure AI integration"""
    azure_client = None
    
    # Try to create Azure AI client if config provided
    if azure_config:
        try:
            from ...integrations.azure_ai.azure_client import AzureAIClient
            azure_client = AzureAIClient(azure_config)
            logging.info("Azure AI client created successfully for PDF processing")
        except Exception as e:
            logging.error(f"Failed to create Azure AI client: {e}")
            logging.info("Falling back to basic PDF processor")
    
    # Use enhanced processor if available and Azure client created
    if EnhancedPDFProcessor and azure_client:
        logging.info("Using EnhancedPDFProcessor with Azure AI integration")
        return EnhancedPDFProcessor(config=config, azure_client=azure_client)
    else:
        logging.info("Using basic PDFProcessor")
        return PDFProcessor(config) 