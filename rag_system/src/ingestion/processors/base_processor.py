# src/ingestion/processors/base_processor.py
"""
Base Processor Interface
Abstract base class for all document processors
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path


class BaseProcessor(ABC):
    """Abstract base class for document processors"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize base processor"""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """
        Check if this processor can handle the given file
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if processor can handle this file type
        """
        pass
    
    @abstractmethod
    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process the file and extract content
        
        Args:
            file_path: Path to the file to process
            metadata: Optional metadata to include
            
        Returns:
            Dictionary containing:
                - status: 'success' or 'error'
                - chunks: List of text chunks ready for embedding
                - metadata: Extracted metadata
                - Other processor-specific fields
        """
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """Validate file exists and is readable"""
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"File does not exist: {file_path}")
            return False
        
        if not path.is_file():
            self.logger.error(f"Path is not a file: {file_path}")
            return False
        
        if not path.stat().st_size > 0:
            self.logger.error(f"File is empty: {file_path}")
            return False
        
        return True
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic file information"""
        path = Path(file_path)
        return {
            'name': path.name,
            'extension': path.suffix.lower(),
            'size': path.stat().st_size,
            'modified': path.stat().st_mtime,
            'absolute_path': str(path.absolute())
        }


class ProcessorRegistry:
    """Registry for document processors"""
    
    def __init__(self):
        self._processors: List[BaseProcessor] = []
        self.logger = logging.getLogger(__name__)
    
    def register(self, processor: BaseProcessor):
        """Register a processor"""
        self._processors.append(processor)
        self.logger.info(f"Registered processor: {processor.__class__.__name__}")
    
    def get_processor(self, file_path: str) -> Optional[BaseProcessor]:
        """Get appropriate processor for a file"""
        for processor in self._processors:
            if processor.can_process(file_path):
                return processor
        return None
    
    def list_processors(self) -> List[str]:
        """List registered processor names"""
        return [p.__class__.__name__ for p in self._processors]