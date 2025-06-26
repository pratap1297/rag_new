"""
Verified Ingestion Engine
Wraps the existing ingestion engine with comprehensive verification
"""
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .pipeline_verifier import PipelineVerifier, PipelineStage
from ..ingestion.ingestion_engine import IngestionEngine


class VerifiedIngestionEngine:
    """Ingestion engine with built-in verification at each step"""
    
    def __init__(self, ingestion_engine: IngestionEngine, verifier: PipelineVerifier = None):
        self.engine = ingestion_engine
        self.verifier = verifier or PipelineVerifier(debug_mode=True, save_intermediate=True)
        self.logger = logging.getLogger(__name__)
    
    def ingest_file_with_verification(self, file_path: str, 
                                     metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest file with verification at each step"""
        result = {
            "file_path": file_path,
            "verification_results": {},
            "ingestion_result": None,
            "success": False,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Step 1: Verify file input
            self.logger.info(f"Starting verified ingestion: {file_path}")
            file_valid, file_results = self.verifier.verify_file_input(file_path)
            result["verification_results"]["file_validation"] = [r.to_dict() for r in file_results]
            
            if not file_valid:
                result["error"] = "File validation failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 2: Get processor and verify selection
            file_path_obj = Path(file_path)
            processor = self.engine.processor_registry.get_processor(str(file_path))
            
            processor_valid, processor_results = self.verifier.verify_processor_selection(
                str(file_path), processor
            )
            result["verification_results"]["processor_selection"] = [r.to_dict() for r in processor_results]
            
            if not processor_valid:
                result["error"] = "Processor selection failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 3: Extract content and verify
            if processor:
                self.logger.info(f"Using processor: {processor.__class__.__name__}")
                processor_result = processor.process(str(file_path), metadata)
                
                # Verify extracted content
                content_valid, content_results = self.verifier.verify_extracted_content(
                    processor_result,
                    expected_format=file_path_obj.suffix.lower().replace('.', '')
                )
                result["verification_results"]["content_extraction"] = [r.to_dict() for r in content_results]
                
                if not content_valid:
                    result["error"] = "Content extraction failed"
                    result["end_time"] = datetime.now().isoformat()
                    return result
                
                # Use processor chunks
                chunks = processor_result.get('chunks', [])
            else:
                # Fallback to basic extraction
                self.logger.info("Using fallback text extraction")
                text_content = self.engine._extract_text(file_path_obj)
                chunks = self.engine.chunker.chunk_text(text_content, metadata)
                
                # Create a mock content result for verification
                mock_content = {
                    'status': 'success',
                    'chunks': chunks,
                    'metadata': metadata or {}
                }
                
                content_valid, content_results = self.verifier.verify_extracted_content(mock_content)
                result["verification_results"]["content_extraction"] = [r.to_dict() for r in content_results]
                
                if not content_valid:
                    result["error"] = "Content extraction failed"
                    result["end_time"] = datetime.now().isoformat()
                    return result
            
            # Step 4: Verify chunks
            self.logger.info(f"Verifying {len(chunks)} chunks")
            chunks_valid, chunk_results = self.verifier.verify_chunks(chunks)
            result["verification_results"]["text_chunking"] = [r.to_dict() for r in chunk_results]
            
            if not chunks_valid:
                result["error"] = "Chunk verification failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 5: Generate embeddings and verify
            self.logger.info("Generating embeddings")
            embeddings = []
            for chunk in chunks:
                embedding = self.engine.embedder.embed_text(chunk['text'])
                embeddings.append(embedding)
            
            # Verify embeddings
            embeddings_valid, embedding_results = self.verifier.verify_embeddings(embeddings)
            result["verification_results"]["embedding_generation"] = [r.to_dict() for r in embedding_results]
            
            if not embeddings_valid:
                result["error"] = "Embedding generation failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 6: Store vectors and verify
            self.logger.info("Storing vectors in FAISS")
            
            # Prepare vectors and metadata for batch addition
            vectors_to_add = []
            metadata_to_add = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vectors_to_add.append(embedding)
                chunk_metadata = {
                    'text': chunk['text'],
                    'content': chunk['text'],  # For compatibility
                    'chunk_index': i,
                    'doc_id': str(file_path),
                    'filename': os.path.basename(file_path),
                    'original_filename': str(file_path),  # Store full path
                    'file_path': str(file_path),  # Store full path
                    **(chunk.get('metadata', {}))
                }
                metadata_to_add.append(chunk_metadata)
            
            # Add vectors in batch
            vector_ids = self.engine.faiss_store.add_vectors(vectors_to_add, metadata_to_add)
            
            # Verify vector storage
            storage_valid, storage_results = self.verifier.verify_vector_storage(
                self.engine.faiss_store, vector_ids
            )
            result["verification_results"]["vector_storage"] = [r.to_dict() for r in storage_results]
            
            if not storage_valid:
                result["error"] = "Vector storage failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 7: Store metadata and verify
            self.logger.info("Storing file metadata")
            file_id = self.engine.metadata_store.add_file_metadata(str(file_path), {
                **(metadata or {}),
                'chunk_count': len(chunks),
                'vector_ids': vector_ids,
                'processor_used': processor.__class__.__name__ if processor else 'BasicExtractor'
            })
            
            # Verify metadata storage
            metadata_valid, metadata_results = self.verifier.verify_metadata_storage(
                self.engine.metadata_store,
                file_id
            )
            result["verification_results"]["metadata_storage"] = [r.to_dict() for r in metadata_results]
            
            # Generate final report
            verification_report = self.verifier.generate_verification_report()
            
            result["success"] = True
            result["ingestion_result"] = {
                "file_id": file_id,
                "chunks_created": len(chunks),
                "vectors_stored": len(vector_ids),
                "processor_used": processor.__class__.__name__ if processor else 'BasicExtractor'
            }
            # Ensure verification_report is JSON-serializable by converting to JSON and back
            import json
            from .pipeline_verifier import EnumJSONEncoder
            result["verification_report"] = json.loads(json.dumps(verification_report, cls=EnumJSONEncoder))
            result["end_time"] = datetime.now().isoformat()
            
            self.logger.info(f"Verified ingestion completed successfully: {file_id}")
            
        except Exception as e:
            self.verifier.add_error_trace("ingestion", e, {"file_path": file_path})
            result["error"] = str(e)
            # Ensure error_trace is JSON-serializable
            import json
            from .pipeline_verifier import EnumJSONEncoder
            result["error_trace"] = json.loads(json.dumps(self.verifier.error_trace, cls=EnumJSONEncoder))
            result["end_time"] = datetime.now().isoformat()
            self.logger.error(f"Verified ingestion failed: {e}")
        
        return result
    
    def ingest_text_with_verification(self, text: str, 
                                     metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest text directly with verification"""
        result = {
            "text_length": len(text),
            "verification_results": {},
            "ingestion_result": None,
            "success": False,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Create mock content for verification
            mock_content = {
                'status': 'success',
                'chunks': [],
                'metadata': metadata or {}
            }
            
            # Step 1: Generate chunks
            self.logger.info(f"Chunking text of length {len(text)}")
            chunks = self.engine.chunker.chunk_text(text, metadata)
            mock_content['chunks'] = chunks
            
            # Verify extracted content
            content_valid, content_results = self.verifier.verify_extracted_content(mock_content)
            result["verification_results"]["content_extraction"] = [r.to_dict() for r in content_results]
            
            if not content_valid:
                result["error"] = "Content processing failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 2: Verify chunks
            chunks_valid, chunk_results = self.verifier.verify_chunks(chunks)
            result["verification_results"]["text_chunking"] = [r.to_dict() for r in chunk_results]
            
            if not chunks_valid:
                result["error"] = "Chunk verification failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 3: Generate embeddings and verify
            embeddings = []
            for chunk in chunks:
                embedding = self.engine.embedder.embed_text(chunk['text'])
                embeddings.append(embedding)
            
            embeddings_valid, embedding_results = self.verifier.verify_embeddings(embeddings)
            result["verification_results"]["embedding_generation"] = [r.to_dict() for r in embedding_results]
            
            if not embeddings_valid:
                result["error"] = "Embedding generation failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 4: Store vectors and verify
            # Prepare vectors and metadata for batch addition
            vectors_to_add = []
            metadata_to_add = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vectors_to_add.append(embedding)
                chunk_metadata = {
                    'text': chunk['text'],
                    'content': chunk['text'],  # For compatibility
                    'chunk_index': i,
                    'source_type': 'direct_text',
                    **(chunk.get('metadata', {}))
                }
                metadata_to_add.append(chunk_metadata)
            
            # Add vectors in batch
            vector_ids = self.engine.faiss_store.add_vectors(vectors_to_add, metadata_to_add)
            
            storage_valid, storage_results = self.verifier.verify_vector_storage(
                self.engine.faiss_store, vector_ids
            )
            result["verification_results"]["vector_storage"] = [r.to_dict() for r in storage_results]
            
            if not storage_valid:
                result["error"] = "Vector storage failed"
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Step 5: Store metadata (create a pseudo file ID for text ingestion)
            import uuid
            file_id = f"text_{str(uuid.uuid4())[:8]}"
            self.engine.metadata_store.add_file_metadata(file_id, {
                **(metadata or {}),
                'chunk_count': len(chunks),
                'vector_ids': vector_ids,
                'source_type': 'direct_text',
                'text_length': len(text)
            })
            
            metadata_valid, metadata_results = self.verifier.verify_metadata_storage(
                self.engine.metadata_store, file_id
            )
            result["verification_results"]["metadata_storage"] = [r.to_dict() for r in metadata_results]
            
            # Generate final report
            verification_report = self.verifier.generate_verification_report()
            
            result["success"] = True
            result["ingestion_result"] = {
                "file_id": file_id,
                "chunks_created": len(chunks),
                "vectors_stored": len(vector_ids),
                "processor_used": "DirectText"
            }
            # Ensure verification_report is JSON-serializable by converting to JSON and back
            import json
            from .pipeline_verifier import EnumJSONEncoder
            result["verification_report"] = json.loads(json.dumps(verification_report, cls=EnumJSONEncoder))
            result["end_time"] = datetime.now().isoformat()
            
            self.logger.info(f"Verified text ingestion completed: {file_id}")
            
        except Exception as e:
            self.verifier.add_error_trace("text_ingestion", e, {"text_length": len(text)})
            result["error"] = str(e)
            # Ensure error_trace is JSON-serializable
            import json
            from .pipeline_verifier import EnumJSONEncoder
            result["error_trace"] = json.loads(json.dumps(self.verifier.error_trace, cls=EnumJSONEncoder))
            result["end_time"] = datetime.now().isoformat()
            self.logger.error(f"Verified text ingestion failed: {e}")
        
        return result
    
    def ingest_directory(self, directory_path: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Ingest directory with verification for each file"""
        results = {
            'directory_path': directory_path,
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'results': [],
            'verification_summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warning_checks': 0
            },
            'start_time': datetime.now().isoformat()
        }
        
        directory = Path(directory_path)
        if not directory.exists():
            results['error'] = f"Directory not found: {directory_path}"
            results['end_time'] = datetime.now().isoformat()
            return results
        
        # Default file patterns
        if file_patterns is None:
            file_patterns = self.engine.config.ingestion.supported_formats
        
        # Find files to ingest
        files_to_ingest = []
        for pattern in file_patterns:
            files_to_ingest.extend(directory.rglob(f"*{pattern}"))
        
        results['total_files'] = len(files_to_ingest)
        
        for file_path in files_to_ingest:
            try:
                # Create new verifier for each file to avoid state mixing
                file_verifier = PipelineVerifier(
                    debug_mode=self.verifier.debug_mode,
                    save_intermediate=self.verifier.save_intermediate
                )
                temp_engine = VerifiedIngestionEngine(self.engine, file_verifier)
                
                result = temp_engine.ingest_file_with_verification(str(file_path))
                results['results'].append(result)
                
                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                # Aggregate verification stats
                for stage_results in result.get('verification_results', {}).values():
                    for check_result in stage_results:
                        results['verification_summary']['total_checks'] += 1
                        status = check_result.get('status', 'unknown')
                        if status == 'passed':
                            results['verification_summary']['passed_checks'] += 1
                        elif status == 'failed':
                            results['verification_summary']['failed_checks'] += 1
                        elif status == 'warning':
                            results['verification_summary']['warning_checks'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['results'].append({
                    'status': 'failed',
                    'file_path': str(file_path),
                    'error': str(e),
                    'success': False
                })
                self.logger.error(f"Failed to ingest {file_path}: {e}")
        
        results['end_time'] = datetime.now().isoformat()
        self.logger.info(f"Directory verification completed: {results['successful']} successful, "
                        f"{results['failed']} failed from {results['total_files']} files")
        
        return results
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get summary of current verification state"""
        return {
            "total_checks": len(self.verifier.verification_results),
            "passed_checks": sum(1 for r in self.verifier.verification_results 
                               if r.status.value == 'passed'),
            "failed_checks": sum(1 for r in self.verifier.verification_results 
                               if r.status.value == 'failed'),
            "warning_checks": sum(1 for r in self.verifier.verification_results 
                                if r.status.value == 'warning'),
            "stage_timings": self.verifier.stage_timings,
            "error_count": len(self.verifier.error_trace)
        } 
