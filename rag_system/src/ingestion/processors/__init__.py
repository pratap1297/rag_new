# src/ingestion/processors/__init__.py
"""
Document Processors Package
Unified interface for all document processing capabilities
"""

from .base_processor import BaseProcessor, ProcessorRegistry
from .excel_processor import ExcelProcessor, create_excel_processor
from .pdf_processor import PDFProcessor, create_pdf_processor
from .word_processor import WordProcessor, create_word_processor
from .image_processor import ImageProcessor, create_image_processor
from .servicenow_processor import ServiceNowProcessor, create_servicenow_processor
from .text_processor import TextProcessor, create_text_processor

# Version info
__version__ = "2.0.0"

# Available processors
AVAILABLE_PROCESSORS = {
    'excel': ExcelProcessor,
    'pdf': PDFProcessor,
    'word': WordProcessor,
    'image': ImageProcessor,
    'servicenow': ServiceNowProcessor,
    'text': TextProcessor
}

# Factory functions
PROCESSOR_FACTORIES = {
    'excel': create_excel_processor,
    'pdf': create_pdf_processor,
    'word': create_word_processor,
    'image': create_image_processor,
    'servicenow': create_servicenow_processor,
    'text': create_text_processor
}


def create_processor_registry(config=None) -> ProcessorRegistry:
    """Create and populate a processor registry with all available processors"""
    registry = ProcessorRegistry()
    
    # Register all processors
    for processor_name, processor_factory in PROCESSOR_FACTORIES.items():
        try:
            processor = processor_factory(config)
            registry.register(processor)
        except Exception as e:
            print(f"Warning: Could not register {processor_name} processor: {e}")
    
    return registry


def get_processor_for_file(file_path: str, config=None) -> BaseProcessor:
    """Get the appropriate processor for a file"""
    registry = create_processor_registry(config)
    return registry.get_processor(file_path)


def list_supported_extensions() -> dict:
    """List all supported file extensions by processor"""
    extensions = {}
    
    for processor_name, processor_class in AVAILABLE_PROCESSORS.items():
        try:
            # Create temporary instance to get supported extensions
            temp_processor = processor_class()
            if hasattr(temp_processor, 'supported_extensions'):
                extensions[processor_name] = temp_processor.supported_extensions
        except:
            pass
    
    return extensions


def get_processor_capabilities() -> dict:
    """Get capabilities of each processor"""
    capabilities = {}
    
    for processor_name, processor_class in AVAILABLE_PROCESSORS.items():
        capabilities[processor_name] = {
            'class': processor_class.__name__,
            'description': processor_class.__doc__ or "No description available",
            'supported_extensions': getattr(processor_class(), 'supported_extensions', [])
        }
    
    return capabilities


# Export main classes and functions
__all__ = [
    'BaseProcessor',
    'ProcessorRegistry',
    'ExcelProcessor',
    'PDFProcessor', 
    'WordProcessor',
    'ImageProcessor',
    'ServiceNowProcessor',
    'TextProcessor',
    'create_processor_registry',
    'get_processor_for_file',
    'list_supported_extensions',
    'get_processor_capabilities',
    'AVAILABLE_PROCESSORS',
    'PROCESSOR_FACTORIES'
] 