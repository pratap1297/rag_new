"""
Ingestion Engine
Main engine for processing and ingesting documents
"""
import logging
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.error_handling import IngestionError, FileProcessingError
from ..core.unified_error_handling import (
    ErrorCode, ErrorInfo, ErrorContext, Result, 
    with_error_handling, IngestionErrorHandler
)
from ..core.metadata_manager import get_metadata_manager, MetadataSchema
from .processors.base_processor import ProcessorRegistry
from .processors.excel_processor import ExcelProcessor
from .processors import create_processor_registry

class IngestionEngine:
    """Main document ingestion engine"""
    
    def __init__(self, chunker, embedder, faiss_store, metadata_store, config_manager):
        self.chunker = chunker
        self.embedder = embedder
        self.faiss_store = faiss_store
        self.metadata_store = metadata_store
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Initialize metadata manager
        self.metadata_manager = get_metadata_manager()
        
        # Initialize processor registry with all available processors
        try:
            # Create processor config from ingestion config
            processor_config = self.config.ingestion.__dict__.copy()
            logging.info(f"DEBUG: Created processor config with keys: {list(processor_config.keys())}")
            
            # Add Azure AI config if available
            try:
                azure_config = self.config_manager.get_config('azure_ai')
                if azure_config:
                    processor_config['azure_ai'] = azure_config.__dict__
                    logging.info("DEBUG: Added Azure AI config to processor config")
            except Exception as e:
                logging.debug(f"Azure AI config not available: {e}")
            
            # Create registry with all processors
            logging.info("DEBUG: About to call create_processor_registry")
            self.processor_registry = create_processor_registry(processor_config)
            logging.info(f"Processor registry initialized with {len(self.processor_registry.list_processors())} processors: {self.processor_registry.list_processors()}")
            
        except Exception as e:
            logging.error(f"Failed to create processor registry: {e}")
            logging.error(f"DEBUG: Exception type: {type(e)}")
            import traceback
            logging.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
            # Fallback to empty registry
            self.processor_registry = ProcessorRegistry()
            # Still register Excel processor manually as fallback
            self._register_excel_processor()
        
        logging.info("Ingestion engine initialized with managed metadata")
    
    def _register_excel_processor(self):
        """Register Excel processor with robust Azure AI support if configured"""
        try:
            # Try to get Azure AI configuration
            azure_config = None
            try:
                azure_config = self.config_manager.get_config('azure_ai')
            except Exception as e:
                logging.debug(f"Azure AI config not available: {e}")
            
            # Use robust Excel processor with comprehensive error handling
            from .processors.robust_excel_processor import RobustExcelProcessor
            from ..integrations.azure_ai.config_validator import AzureAIConfigValidator
            from ..integrations.azure_ai.robust_azure_client import RobustAzureAIClient
            
            # Prepare processor config
            processor_config = self.config.ingestion.__dict__.copy()
            
            # Add Azure AI config if available
            if azure_config:
                try:
                    # Validate and fix Azure configuration
                    fixed_azure_config, issues = AzureAIConfigValidator.validate_and_fix(azure_config.__dict__)
                    
                    if issues:
                        logging.info(f"Azure AI configuration fixes applied: {len(issues)} issues")
                        for issue in issues[:5]:  # Log first 5 issues
                            logging.debug(f"Config fix: {issue}")
                    
                    # Check configuration status
                    config_status = AzureAIConfigValidator.get_configuration_status(fixed_azure_config)
                    
                    if config_status['overall']['configuration_complete']:
                        # Initialize robust Azure client
                        try:
                            azure_client = RobustAzureAIClient(fixed_azure_config)
                            
                            # Check client health
                            if azure_client.is_healthy():
                                processor_config['azure_ai'] = fixed_azure_config
                                excel_processor = RobustExcelProcessor(
                                    config=processor_config,
                                    azure_client=azure_client
                                )
                                available_services = azure_client.get_available_services()
                                logging.info(f"Excel processor registered with Azure AI support: {available_services}")
                            else:
                                # Client not healthy, use without Azure AI
                                excel_processor = RobustExcelProcessor(config=processor_config)
                                service_status = azure_client.get_service_status()
                                logging.warning(f"Azure AI services not healthy, using fallback processing. Status: {service_status['overall_health']}")
                        
                        except Exception as e:
                            # Azure client initialization failed
                            excel_processor = RobustExcelProcessor(config=processor_config)
                            logging.error(f"Failed to initialize Azure AI client: {e}")
                    else:
                        # Configuration incomplete
                        excel_processor = RobustExcelProcessor(config=processor_config)
                        missing_services = [s for s, status in config_status['services'].items() if not status['configured']]
                        logging.info(f"Azure AI configuration incomplete (missing: {missing_services}), using fallback processing")
                
                except Exception as e:
                    # Configuration validation failed
                    excel_processor = RobustExcelProcessor(config=processor_config)
                    logging.error(f"Azure AI configuration validation failed: {e}")
            else:
                # No Azure AI configuration
                excel_processor = RobustExcelProcessor(config=processor_config)
                logging.info("No Azure AI configuration found, using local processing only")
            
            # Register the processor
            self.processor_registry.register(excel_processor)
            
            # Log processor capabilities
            processor_info = excel_processor.get_processor_info()
            logging.info(f"Excel processor registered: {processor_info['capabilities']}")
            
        except ImportError as e:
            # Fallback to basic Excel processor if robust version not available
            logging.warning(f"Robust Excel processor not available: {e}")
            try:
                excel_processor = ExcelProcessor(config=self.config.ingestion.__dict__)
                self.processor_registry.register(excel_processor)
                logging.info("Basic Excel processor registered as fallback")
            except Exception as fallback_e:
                logging.error(f"Failed to register any Excel processor: {fallback_e}")
        
        except Exception as e:
            logging.error(f"Failed to register Excel processor: {e}")
            # Try basic fallback
            try:
                excel_processor = ExcelProcessor(config=self.config.ingestion.__dict__)
                self.processor_registry.register(excel_processor)
                logging.info("Basic Excel processor registered after error")
            except Exception as fallback_e:
                logging.error(f"All Excel processor registration attempts failed: {fallback_e}")
    
    def _generate_doc_id(self, metadata: Dict[str, Any]) -> str:
        """Generate a proper document ID based on available metadata"""
        # Priority 1: Use doc_path if available (most reliable)
        if metadata.get('doc_path'):
            doc_path = metadata['doc_path']
            # Remove leading slash and convert to proper ID format
            if doc_path.startswith('/'):
                doc_path = doc_path[1:]
            return doc_path.replace('/', '_').replace(' ', '_')
        
        # Priority 2: Use filename if available
        if metadata.get('filename'):
            filename = metadata['filename']
            # Remove extension and clean up
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]
            return f"docs_{filename.replace(' ', '_').replace('-', '_')}"
        
        # Priority 3: Use file_name from file_path
        if metadata.get('file_name'):
            file_name = metadata['file_name']
            if '.' in file_name:
                file_name = file_name.rsplit('.', 1)[0]
            return f"docs_{file_name.replace(' ', '_').replace('-', '_')}"
        
        # Priority 4: Generate from file_path
        if metadata.get('file_path'):
            file_path = Path(metadata['file_path'])
            stem = file_path.stem
            return f"docs_{stem.replace(' ', '_').replace('-', '_')}"
        
        # Fallback: Generate a unique ID
        import uuid
        return f"docs_{uuid.uuid4().hex[:8]}"
    
    def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest a single file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileProcessingError(f"File not found: {file_path}")
        
        try:
            # Store current metadata for matching purposes
            self._current_metadata = metadata or {}
            
            # Check if this file path already exists and delete old vectors
            old_vectors_deleted = self._handle_existing_file(str(file_path))
            
            # Extract text from file
            text_content = self._extract_text(file_path)
            
            if not text_content.strip():
                return {
                    'status': 'skipped',
                    'reason': 'no_content',
                    'file_path': str(file_path)
                }
            
            # Prepare base file metadata
            file_metadata = {
                'file_path': str(file_path),
                'filename': file_path.name,  # Use 'filename' instead of 'file_name'
                'file_size': file_path.stat().st_size,
                'file_type': file_path.suffix,
                'source_type': 'file',
                'ingested_at': datetime.now().isoformat(),
                'processor': 'ingestion_engine',
                'is_update': old_vectors_deleted > 0,
                'replaced_vectors': old_vectors_deleted
            }
            
            # Chunk the text with base metadata
            chunks = self.chunker.chunk_text(text_content, file_metadata)
            
            if not chunks:
                return {
                    'status': 'skipped',
                    'reason': 'no_chunks',
                    'file_path': str(file_path)
                }
            
            # Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.embed_texts(chunk_texts)
            
            # Prepare chunk metadata using metadata manager
            chunk_metadata_list = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Merge metadata using the metadata manager to prevent double flattening
                try:
                    merged_metadata = self.metadata_manager.merge_metadata(
                        file_metadata,           # Base file metadata
                        metadata or {},          # Custom metadata from user
                        chunk.get('metadata', {}),  # Chunk-specific metadata
                        {                        # Final chunk data
                            'text': chunk['text'],
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'chunk_size': len(chunk['text']),
                            'chunking_method': getattr(self.chunker, '__class__', {}).get('__name__', 'unknown'),
                            'embedding_model': getattr(self.embedder, 'model_name', 'unknown')
                        }
                    )
                    
                    # Prepare for storage
                    storage_metadata = self.metadata_manager.prepare_for_storage(merged_metadata)
                    chunk_metadata_list.append(storage_metadata)
                    
                except Exception as e:
                    logging.error(f"Failed to merge metadata for chunk {i}: {e}")
                    # Fallback to simple metadata
                    fallback_meta = {
                        'text': chunk['text'],
                        'chunk_index': i,
                        'doc_id': file_metadata.get('filename', 'unknown'),
                        'filename': file_metadata.get('filename'),
                        'file_path': str(file_path),
                        'source_type': 'file'
                    }
                    chunk_metadata_list.append(fallback_meta)
            
            # Add to FAISS store
            vector_ids = self.faiss_store.add_vectors(embeddings, chunk_metadata_list)
            
            # Store file metadata
            final_file_metadata = {
                **file_metadata,
                'chunk_count': len(chunks),
                'vector_ids': vector_ids,
                'doc_id': chunk_metadata_list[0].get('doc_id', 'unknown') if chunk_metadata_list else 'unknown'
            }
            
            file_id = self.metadata_store.add_file_metadata(str(file_path), final_file_metadata)
            
            logging.info(f"Successfully ingested file: {file_path} ({len(chunks)} chunks)")
            if old_vectors_deleted > 0:
                logging.info(f"Replaced {old_vectors_deleted} old vectors for updated file")
            
            # Get doc_id for response
            doc_id = chunk_metadata_list[0].get('doc_id', 'unknown') if chunk_metadata_list else 'unknown'
            
            return {
                'status': 'success',
                'file_id': file_id,
                'doc_id': doc_id,
                'file_path': str(file_path),
                'chunks_created': len(chunks),
                'vectors_stored': len(vector_ids),
                'is_update': old_vectors_deleted > 0,
                'old_vectors_deleted': old_vectors_deleted
            }
            
        except Exception as e:
            logging.error(f"Failed to ingest file {file_path}: {e}")
            raise IngestionError(f"Failed to ingest file: {e}", file_path=str(file_path))
    
    def ingest_text(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest raw text content with managed metadata"""
        try:
            if not text.strip():
                return {
                    'status': 'skipped',
                    'reason': 'no_content'
                }
            
            # Prepare base metadata
            base_metadata = {
                'source_type': 'text',
                'ingested_at': datetime.now().isoformat(),
                'processor': 'ingestion_engine_text',
                'text_length': len(text)
            }
            
            # Chunk the text
            chunks = self.chunker.chunk_text(text, base_metadata)
            
            if not chunks:
                return {
                    'status': 'skipped',
                    'reason': 'no_chunks'
                }
            
            # Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.embed_texts(chunk_texts)
            
            # Prepare chunk metadata using metadata manager
            chunk_metadata_list = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    # Merge metadata using the metadata manager
                    merged_metadata = self.metadata_manager.merge_metadata(
                        base_metadata,           # Base metadata
                        metadata or {},          # Custom metadata from user
                        chunk.get('metadata', {}),  # Chunk-specific metadata
                        {                        # Final chunk data
                            'text': chunk['text'],
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'chunk_size': len(chunk['text']),
                            'chunking_method': getattr(self.chunker, '__class__', {}).get('__name__', 'unknown'),
                            'embedding_model': getattr(self.embedder, 'model_name', 'unknown')
                        }
                    )
                    
                    # Prepare for storage
                    storage_metadata = self.metadata_manager.prepare_for_storage(merged_metadata)
                    chunk_metadata_list.append(storage_metadata)
                    
                except Exception as e:
                    logging.error(f"Failed to merge metadata for text chunk {i}: {e}")
                    # Fallback to simple metadata
                    fallback_meta = {
                        'text': chunk['text'],
                        'chunk_index': i,
                        'doc_id': metadata.get('title', 'text_document') if metadata else 'text_document',
                        'source_type': 'text'
                    }
                    chunk_metadata_list.append(fallback_meta)
            
            # Add to FAISS store
            vector_ids = self.faiss_store.add_vectors(embeddings, chunk_metadata_list)
            
            # Get doc_id for response
            doc_id = chunk_metadata_list[0].get('doc_id', 'text_document') if chunk_metadata_list else 'text_document'
            
            logging.info(f"Successfully ingested text content ({len(chunks)} chunks)")
            
            return {
                'status': 'success',
                'doc_id': doc_id,
                'chunks_created': len(chunks),
                'vectors_stored': len(vector_ids),
                'text_length': len(text)
            }
            
        except Exception as e:
            logging.error(f"Failed to ingest text: {e}")
            raise IngestionError(f"Failed to ingest text: {e}")
    
    def _handle_existing_file(self, file_path: str) -> int:
        """Handle existing file by deleting old vectors"""
        try:
            # Search for existing vectors with this file path
            existing_vectors = []
            
            # Extract doc_path from current metadata if available
            current_doc_path = None
            current_filename = None
            if hasattr(self, '_current_metadata') and self._current_metadata:
                current_doc_path = self._current_metadata.get('doc_path')
                current_filename = self._current_metadata.get('filename')
            
            logging.info(f"Looking for existing vectors for file_path: {file_path}, doc_path: {current_doc_path}, filename: {current_filename}")
            
            # Get all vector metadata and find matches
            for vector_id, metadata in self.faiss_store.id_to_metadata.items():
                if metadata.get('deleted', False):
                    continue
                
                # Check multiple possible matching criteria
                is_match = False
                match_reason = ""
                
                # Priority 1: doc_path match (most reliable for updates)
                if current_doc_path and metadata.get('doc_path') == current_doc_path:
                    is_match = True
                    match_reason = f"doc_path match: {metadata.get('doc_path')}"
                
                # Priority 2: Check nested metadata for doc_path
                elif current_doc_path and isinstance(metadata.get('metadata'), dict):
                    nested_doc_path = metadata['metadata'].get('doc_path')
                    if nested_doc_path == current_doc_path:
                        is_match = True
                        match_reason = f"nested doc_path match: {nested_doc_path}"
                
                # Priority 3: filename match (for same filename uploads)
                elif current_filename and metadata.get('filename') == current_filename:
                    is_match = True
                    match_reason = f"filename match: {metadata.get('filename')}"
                
                # Priority 4: Check nested metadata for filename
                elif current_filename and isinstance(metadata.get('metadata'), dict):
                    nested_filename = metadata['metadata'].get('filename')
                    if nested_filename == current_filename:
                        is_match = True
                        match_reason = f"nested filename match: {nested_filename}"
                
                # Priority 5: Direct file_path match (least reliable for updates)
                elif metadata.get('file_path') == file_path:
                    is_match = True
                    match_reason = f"file_path match: {metadata.get('file_path')}"
                
                if is_match:
                    existing_vectors.append(vector_id)
                    logging.info(f"Found matching vector {vector_id}: {match_reason}")
            
            if existing_vectors:
                logging.info(f"Found {len(existing_vectors)} existing vectors")
                # Delete old vectors
                self.faiss_store.delete_vectors(existing_vectors)
                logging.info(f"Deleted {len(existing_vectors)} old vectors for file update")
                return len(existing_vectors)
            else:
                logging.info(f"No existing vectors found for file: {file_path}")
                # Debug: Print some metadata samples
                sample_count = 0
                for vector_id, metadata in self.faiss_store.id_to_metadata.items():
                    if not metadata.get('deleted', False) and sample_count < 3:
                        logging.debug(f"Sample vector {vector_id} metadata keys: {list(metadata.keys())}")
                        if 'doc_path' in metadata:
                            logging.debug(f"  doc_path: {metadata['doc_path']}")
                        if 'file_path' in metadata:
                            logging.debug(f"  file_path: {metadata['file_path']}")
                        if isinstance(metadata.get('metadata'), dict):
                            nested_meta = metadata['metadata']
                            if 'doc_path' in nested_meta:
                                logging.debug(f"  nested doc_path: {nested_meta['doc_path']}")
                            if 'filename' in nested_meta:
                                logging.debug(f"  nested filename: {nested_meta['filename']}")
                        sample_count += 1
            
            return 0
            
        except Exception as e:
            logging.warning(f"Error handling existing file {file_path}: {e}")
            return 0
    
    def ingest_directory(self, directory_path: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Ingest all files in a directory"""
        directory = Path(directory_path)
        
        if not directory.exists():
            raise IngestionError(f"Directory not found: {directory_path}")
        
        # Default file patterns
        if file_patterns is None:
            file_patterns = self.config.ingestion.supported_formats
        
        # Find files to ingest
        files_to_ingest = []
        for pattern in file_patterns:
            files_to_ingest.extend(directory.rglob(f"*{pattern}"))
        
        results = {
            'total_files': len(files_to_ingest),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
        
        for file_path in files_to_ingest:
            try:
                result = self.ingest_file(str(file_path))
                results['results'].append(result)
                
                if result['status'] == 'success':
                    results['successful'] += 1
                elif result['status'] == 'skipped':
                    results['skipped'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['results'].append({
                    'status': 'failed',
                    'file_path': str(file_path),
                    'error': str(e)
                })
                logging.error(f"Failed to ingest {file_path}: {e}")
        
        logging.info(f"Directory ingestion completed: {results['successful']} successful, "
                    f"{results['failed']} failed, {results['skipped']} skipped")
        
        return results
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text content from various file types"""
        file_extension = file_path.suffix.lower()
        # Check if we have a specialized processor
        processor = self.processor_registry.get_processor(str(file_path))
        if processor:
            try:
                result = processor.process(str(file_path), getattr(self, '_current_metadata', {}))
                if result['status'] == 'success':
                    chunk_texts = [chunk['text'] for chunk in result.get('chunks', [])]
                    combined_text = '\n\n'.join(chunk_texts)
                    if hasattr(self, '_current_metadata') and self._current_metadata:
                        self._current_metadata.update({
                            'processor_used': processor.__class__.__name__,
                            'embedded_objects': len(result.get('embedded_objects', [])),
                            'images_processed': len(result.get('images', [])),
                            'charts_found': len(result.get('charts', []))
                        })
                    return combined_text
            except Exception as e:
                logging.error(f"Processor failed for {file_path}: {e}")
                # Fall back to default extraction
        try:
            if file_extension == '.txt':
                return self._extract_text_file(file_path)
            elif file_extension == '.pdf':
                return self._extract_pdf_file(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_docx_file(file_path)
            elif file_extension == '.md':
                return self._extract_markdown_file(file_path)
            elif file_extension in ['.xlsx', '.xls', '.xlsm']:
                return self._extract_excel_basic(file_path)
            else:
                return self._extract_text_file(file_path)
        except Exception as e:
            raise FileProcessingError(f"Failed to extract text from {file_path}: {e}")
    
    def _extract_text_file(self, file_path: Path) -> str:
        """Extract text from plain text file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _extract_pdf_file(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise FileProcessingError("PyPDF2 not installed. Cannot process PDF files.")
    
    def _extract_docx_file(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise FileProcessingError("python-docx not installed. Cannot process DOCX files.")
    
    def _extract_markdown_file(self, file_path: Path) -> str:
        """Extract text from Markdown file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Simple markdown processing - remove formatting
        import re
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)  # Remove headers
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # Remove italic
        content = re.sub(r'`(.*?)`', r'\1', content)  # Remove code
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Remove links
        
        return content
    
    def _extract_excel_basic(self, file_path: Path) -> str:
        """Basic Excel text extraction without Azure AI"""
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(file_path)
            all_text = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                all_text.append(f"Sheet: {sheet_name}")
                all_text.append(df.to_string())
                all_text.append("\n")
            return "\n".join(all_text)
        except ImportError:
            raise FileProcessingError("pandas not installed. Cannot process Excel files without processor.")
        except Exception as e:
            raise FileProcessingError(f"Failed to extract Excel content: {e}")
    
    def delete_file(self, file_path: str, doc_path: str = None) -> Dict[str, Any]:
        """Delete all vectors associated with a file"""
        try:
            logging.info(f"Deleting vectors for file: {file_path}")
            
            # Find all vectors associated with this file
            vectors_to_delete = []
            
            # Get all vector metadata and find matches
            for vector_id, metadata in self.faiss_store.id_to_metadata.items():
                if metadata.get('deleted', False):
                    continue
                
                # Check multiple possible matching criteria
                is_match = False
                match_reason = ""
                
                # Priority 1: doc_path match (most reliable)
                if doc_path and metadata.get('doc_path') == doc_path:
                    is_match = True
                    match_reason = f"doc_path match: {metadata.get('doc_path')}"
                
                # Priority 2: Check nested metadata for doc_path
                elif doc_path and isinstance(metadata.get('metadata'), dict):
                    nested_doc_path = metadata['metadata'].get('doc_path')
                    if nested_doc_path == doc_path:
                        is_match = True
                        match_reason = f"nested doc_path match: {nested_doc_path}"
                
                # Priority 3: Direct file_path match
                elif metadata.get('file_path') == file_path:
                    is_match = True
                    match_reason = f"file_path match: {metadata.get('file_path')}"
                
                # Priority 4: Check nested metadata for original_path
                elif isinstance(metadata.get('metadata'), dict):
                    nested_original_path = metadata['metadata'].get('original_path')
                    if nested_original_path == file_path:
                        is_match = True
                        match_reason = f"nested original_path match: {nested_original_path}"
                
                if is_match:
                    vectors_to_delete.append(vector_id)
                    logging.info(f"Found vector to delete {vector_id}: {match_reason}")
            
            if vectors_to_delete:
                # Delete the vectors
                self.faiss_store.delete_vectors(vectors_to_delete)
                logging.info(f"Successfully deleted {len(vectors_to_delete)} vectors for file: {file_path}")
                
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'vectors_deleted': len(vectors_to_delete),
                    'message': f"Deleted {len(vectors_to_delete)} vectors"
                }
            else:
                logging.info(f"No vectors found for file: {file_path}")
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'vectors_deleted': 0,
                    'message': "No vectors found to delete"
                }
                
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return {
                'status': 'failed',
                'file_path': file_path,
                'error': str(e)
            }
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        # Get stats from metadata store
        collections = self.metadata_store.list_collections()
        
        stats = {
            'total_files': 0,
            'total_chunks': 0,
            'total_vectors': 0,
            'collections': len(collections)
        }
        
        # Get file count
        if 'files_metadata' in collections:
            file_stats = self.metadata_store.collection_stats('files_metadata')
            stats['total_files'] = file_stats.get('count', 0)
        
        # Get FAISS stats
        faiss_info = self.faiss_store.get_index_info()
        stats['total_vectors'] = faiss_info.get('ntotal', 0)
        stats['active_vectors'] = faiss_info.get('active_vectors', 0)
        
        return stats