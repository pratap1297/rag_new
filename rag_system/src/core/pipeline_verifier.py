"""
Pipeline Verification System
Comprehensive verification and error checking for the RAG ingestion pipeline
"""
import logging
import json
import traceback
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import time

class PipelineStage(Enum):
    """Pipeline stages for verification"""
    FILE_VALIDATION = "file_validation"
    PROCESSOR_SELECTION = "processor_selection"
    CONTENT_EXTRACTION = "content_extraction"
    TEXT_CHUNKING = "text_chunking"
    EMBEDDING_GENERATION = "embedding_generation"
    VECTOR_STORAGE = "vector_storage"
    METADATA_STORAGE = "metadata_storage"

class VerificationStatus(Enum):
    """Verification status for each check"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    PENDING = "pending"
    RUNNING = "running"

@dataclass
class VerificationResult:
    """Result of a verification check"""
    stage: PipelineStage
    check_name: str
    status: VerificationStatus
    message: str
    details: Dict[str, Any] = None
    timestamp: str = None
    duration_ms: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            'stage': self.stage.value,
            'check_name': self.check_name,
            'status': self.status.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp,
            'duration_ms': self.duration_ms
        }

class EnumJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Enum objects"""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)

class PipelineVerifier:
    """Main verification system for the ingestion pipeline"""
    
    def __init__(self, debug_mode: bool = True, save_intermediate: bool = True):
        self.debug_mode = debug_mode
        self.save_intermediate = save_intermediate
        self.verification_results = []
        self.intermediate_outputs = {}
        self.error_trace = []
        self.stage_timings = {}
        self.event_callbacks = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if debug_mode:
            self.logger.setLevel(logging.DEBUG)
        
        # Create debug output directory
        self.debug_dir = Path("debug_output")
        self.debug_dir.mkdir(exist_ok=True)
    
    def add_event_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for real-time event updates"""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all registered callbacks"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Event callback error: {e}")
    
    def _start_stage_timing(self, stage: PipelineStage):
        """Start timing for a pipeline stage"""
        self.stage_timings[stage.value] = {"start": time.time()}
        self._emit_event("stage_started", {"stage": stage.value})
    
    def _end_stage_timing(self, stage: PipelineStage):
        """End timing for a pipeline stage"""
        if stage.value in self.stage_timings:
            duration = time.time() - self.stage_timings[stage.value]["start"]
            self.stage_timings[stage.value]["duration"] = duration
            self._emit_event("stage_completed", {
                "stage": stage.value,
                "duration": duration
            })
    
    def verify_file_input(self, file_path: str) -> Tuple[bool, List[VerificationResult]]:
        """Verify file input before processing"""
        self._start_stage_timing(PipelineStage.FILE_VALIDATION)
        results = []
        file_path = Path(file_path)
        
        # Check 1: File exists
        start_time = time.time()
        if not file_path.exists():
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_exists",
                status=VerificationStatus.FAILED,
                message=f"File not found: {file_path}",
                details={"file_path": str(file_path)},
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.FILE_VALIDATION)
            return False, results
        
        results.append(VerificationResult(
            stage=PipelineStage.FILE_VALIDATION,
            check_name="file_exists",
            status=VerificationStatus.PASSED,
            message="File exists",
            duration_ms=(time.time() - start_time) * 1000
        ))
        
        # Check 2: File size
        start_time = time.time()
        file_size = file_path.stat().st_size
        if file_size == 0:
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_size",
                status=VerificationStatus.FAILED,
                message="File is empty",
                details={"size": 0},
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.FILE_VALIDATION)
            return False, results
        elif file_size > 100 * 1024 * 1024:  # 100MB
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_size",
                status=VerificationStatus.WARNING,
                message=f"Large file: {file_size / 1024 / 1024:.2f}MB",
                details={"size_mb": file_size / 1024 / 1024},
                duration_ms=(time.time() - start_time) * 1000
            ))
        else:
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_size",
                status=VerificationStatus.PASSED,
                message=f"File size: {file_size / 1024:.2f}KB",
                details={"size_bytes": file_size},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        # Check 3: File permissions
        start_time = time.time()
        try:
            with open(file_path, 'rb') as f:
                # Try to read first few bytes
                f.read(1024)
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_readable",
                status=VerificationStatus.PASSED,
                message="File is readable",
                duration_ms=(time.time() - start_time) * 1000
            ))
        except Exception as e:
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_readable",
                status=VerificationStatus.FAILED,
                message=f"Cannot read file: {str(e)}",
                details={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.FILE_VALIDATION)
            return False, results
        
        # Check 4: File extension
        start_time = time.time()
        extension = file_path.suffix.lower()
        supported_extensions = ['.pdf', '.docx', '.xlsx', '.txt', '.md', '.csv']
        if extension not in supported_extensions:
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_extension",
                status=VerificationStatus.WARNING,
                message=f"Unusual extension: {extension}",
                details={"extension": extension, "supported": supported_extensions},
                duration_ms=(time.time() - start_time) * 1000
            ))
        else:
            results.append(VerificationResult(
                stage=PipelineStage.FILE_VALIDATION,
                check_name="file_extension",
                status=VerificationStatus.PASSED,
                message=f"Supported extension: {extension}",
                details={"extension": extension},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        self.verification_results.extend(results)
        self._end_stage_timing(PipelineStage.FILE_VALIDATION)
        return all(r.status != VerificationStatus.FAILED for r in results), results
    
    def verify_processor_selection(self, file_path: str, processor) -> Tuple[bool, List[VerificationResult]]:
        """Verify processor selection for the file"""
        self._start_stage_timing(PipelineStage.PROCESSOR_SELECTION)
        results = []
        start_time = time.time()
        
        if processor is None:
            results.append(VerificationResult(
                stage=PipelineStage.PROCESSOR_SELECTION,
                check_name="processor_available",
                status=VerificationStatus.WARNING,
                message="No specific processor found, using default",
                details={"file_path": file_path},
                duration_ms=(time.time() - start_time) * 1000
            ))
        else:
            results.append(VerificationResult(
                stage=PipelineStage.PROCESSOR_SELECTION,
                check_name="processor_available",
                status=VerificationStatus.PASSED,
                message=f"Using processor: {processor.__class__.__name__}",
                details={"processor": processor.__class__.__name__, "file_path": file_path},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        self.verification_results.extend(results)
        self._end_stage_timing(PipelineStage.PROCESSOR_SELECTION)
        return True, results
    
    def verify_extracted_content(self, content: Dict[str, Any], 
                               expected_format: str = None) -> Tuple[bool, List[VerificationResult]]:
        """Verify extracted content from processor"""
        self._start_stage_timing(PipelineStage.CONTENT_EXTRACTION)
        results = []
        
        # Check 1: Content structure
        start_time = time.time()
        required_fields = ['status', 'chunks']
        missing_fields = [f for f in required_fields if f not in content]
        
        if missing_fields:
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="content_structure",
                status=VerificationStatus.FAILED,
                message=f"Missing required fields: {missing_fields}",
                details={"missing_fields": missing_fields, "available_fields": list(content.keys())},
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.CONTENT_EXTRACTION)
            return False, results
        else:
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="content_structure",
                status=VerificationStatus.PASSED,
                message="Content structure is valid",
                details={"fields": list(content.keys())},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        # Check 2: Processing status
        start_time = time.time()
        status = content.get('status', 'unknown')
        if status != 'success':
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="processing_status",
                status=VerificationStatus.FAILED,
                message=f"Processing failed with status: {status}",
                details={"status": status, "error": content.get('error', 'Unknown error')},
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.CONTENT_EXTRACTION)
            return False, results
        else:
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="processing_status",
                status=VerificationStatus.PASSED,
                message="Processing completed successfully",
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        # Check 3: Chunks availability
        start_time = time.time()
        chunks = content.get('chunks', [])
        if not chunks:
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="chunks_available",
                status=VerificationStatus.FAILED,
                message="No chunks extracted from content",
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.CONTENT_EXTRACTION)
            return False, results
        else:
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="chunks_available",
                status=VerificationStatus.PASSED,
                message=f"Extracted {len(chunks)} chunks",
                details={"chunk_count": len(chunks)},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        # Check 4: Content quality
        start_time = time.time()
        total_text_length = sum(len(chunk.get('text', '')) for chunk in chunks)
        if total_text_length < 10:
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="content_quality",
                status=VerificationStatus.WARNING,
                message=f"Very little text extracted: {total_text_length} characters",
                details={"total_characters": total_text_length},
                duration_ms=(time.time() - start_time) * 1000
            ))
        else:
            results.append(VerificationResult(
                stage=PipelineStage.CONTENT_EXTRACTION,
                check_name="content_quality",
                status=VerificationStatus.PASSED,
                message=f"Extracted {total_text_length} characters of text",
                details={"total_characters": total_text_length},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        self.verification_results.extend(results)
        self._end_stage_timing(PipelineStage.CONTENT_EXTRACTION)
        return all(r.status != VerificationStatus.FAILED for r in results), results
    
    def verify_chunks(self, chunks: List[Dict[str, Any]]) -> Tuple[bool, List[VerificationResult]]:
        """Verify text chunks quality and structure"""
        self._start_stage_timing(PipelineStage.TEXT_CHUNKING)
        results = []
        
        # Check 1: Chunks exist
        start_time = time.time()
        if not chunks:
            results.append(VerificationResult(
                stage=PipelineStage.TEXT_CHUNKING,
                check_name="chunks_exist",
                status=VerificationStatus.FAILED,
                message="No chunks provided for verification",
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.TEXT_CHUNKING)
            return False, results
        
        results.append(VerificationResult(
            stage=PipelineStage.TEXT_CHUNKING,
            check_name="chunks_exist",
            status=VerificationStatus.PASSED,
            message=f"Found {len(chunks)} chunks",
            details={"chunk_count": len(chunks)},
            duration_ms=(time.time() - start_time) * 1000
        ))
        
        # Check 2: Chunk sizes
        start_time = time.time()
        chunk_sizes = [len(chunk.get('text', '')) for chunk in chunks]
        empty_chunks = sum(1 for size in chunk_sizes if size == 0)
        oversized_chunks = sum(1 for size in chunk_sizes if size > 2000)
        
        if empty_chunks > 0:
            results.append(VerificationResult(
                stage=PipelineStage.TEXT_CHUNKING,
                check_name="chunk_sizes",
                status=VerificationStatus.WARNING,
                message=f"Found {empty_chunks} empty chunks",
                details={"empty_chunks": empty_chunks, "total_chunks": len(chunks)},
                duration_ms=(time.time() - start_time) * 1000
            ))
        elif oversized_chunks > 0:
            results.append(VerificationResult(
                stage=PipelineStage.TEXT_CHUNKING,
                check_name="chunk_sizes",
                status=VerificationStatus.WARNING,
                message=f"Found {oversized_chunks} oversized chunks (>2000 chars)",
                details={"oversized_chunks": oversized_chunks, "total_chunks": len(chunks)},
                duration_ms=(time.time() - start_time) * 1000
            ))
        else:
            avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            results.append(VerificationResult(
                stage=PipelineStage.TEXT_CHUNKING,
                check_name="chunk_sizes",
                status=VerificationStatus.PASSED,
                message=f"Chunk sizes are appropriate (avg: {avg_size:.0f} chars)",
                details={"avg_size": avg_size, "min_size": min(chunk_sizes), "max_size": max(chunk_sizes)},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        # Check 3: Chunk metadata
        start_time = time.time()
        chunks_with_metadata = sum(1 for chunk in chunks if chunk.get('metadata'))
        if chunks_with_metadata < len(chunks) * 0.5:
            results.append(VerificationResult(
                stage=PipelineStage.TEXT_CHUNKING,
                check_name="chunk_metadata",
                status=VerificationStatus.WARNING,
                message=f"Only {chunks_with_metadata}/{len(chunks)} chunks have metadata",
                details={"chunks_with_metadata": chunks_with_metadata, "total_chunks": len(chunks)},
                duration_ms=(time.time() - start_time) * 1000
            ))
        else:
            results.append(VerificationResult(
                stage=PipelineStage.TEXT_CHUNKING,
                check_name="chunk_metadata",
                status=VerificationStatus.PASSED,
                message=f"Most chunks have metadata ({chunks_with_metadata}/{len(chunks)})",
                details={"chunks_with_metadata": chunks_with_metadata, "total_chunks": len(chunks)},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        self.verification_results.extend(results)
        self._end_stage_timing(PipelineStage.TEXT_CHUNKING)
        return all(r.status != VerificationStatus.FAILED for r in results), results
    
    def verify_embeddings(self, embeddings: List[List[float]], expected_dim: int = None) -> Tuple[bool, List[VerificationResult]]:
        """Verify embedding generation"""
        self._start_stage_timing(PipelineStage.EMBEDDING_GENERATION)
        results = []
        
        # Check 1: Embeddings exist
        start_time = time.time()
        if not embeddings:
            results.append(VerificationResult(
                stage=PipelineStage.EMBEDDING_GENERATION,
                check_name="embeddings_exist",
                status=VerificationStatus.FAILED,
                message="No embeddings provided for verification",
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.EMBEDDING_GENERATION)
            return False, results
        
        results.append(VerificationResult(
            stage=PipelineStage.EMBEDDING_GENERATION,
            check_name="embeddings_exist",
            status=VerificationStatus.PASSED,
            message=f"Generated {len(embeddings)} embeddings",
            details={"embedding_count": len(embeddings)},
            duration_ms=(time.time() - start_time) * 1000
        ))
        
        # Check 2: Embedding dimensions
        start_time = time.time()
        if embeddings:
            actual_dim = len(embeddings[0]) if embeddings[0] else 0
            dimension_mismatches = sum(1 for emb in embeddings if len(emb) != actual_dim)
            
            if dimension_mismatches > 0:
                results.append(VerificationResult(
                    stage=PipelineStage.EMBEDDING_GENERATION,
                    check_name="embedding_dimensions",
                    status=VerificationStatus.FAILED,
                    message=f"Dimension mismatches found: {dimension_mismatches}",
                    details={"mismatches": dimension_mismatches, "expected_dim": actual_dim},
                    duration_ms=(time.time() - start_time) * 1000
                ))
                self._end_stage_timing(PipelineStage.EMBEDDING_GENERATION)
                return False, results
            else:
                results.append(VerificationResult(
                    stage=PipelineStage.EMBEDDING_GENERATION,
                    check_name="embedding_dimensions",
                    status=VerificationStatus.PASSED,
                    message=f"All embeddings have consistent dimensions: {actual_dim}",
                    details={"dimension": actual_dim},
                    duration_ms=(time.time() - start_time) * 1000
                ))
        
        # Check 3: Embedding values
        start_time = time.time()
        invalid_embeddings = 0
        for i, emb in enumerate(embeddings):
            if not emb or any(not isinstance(val, (int, float)) or 
                            val != val or  # NaN check
                            abs(val) == float('inf') for val in emb):
                invalid_embeddings += 1
        
        if invalid_embeddings > 0:
            results.append(VerificationResult(
                stage=PipelineStage.EMBEDDING_GENERATION,
                check_name="embedding_values",
                status=VerificationStatus.FAILED,
                message=f"Found {invalid_embeddings} embeddings with invalid values",
                details={"invalid_count": invalid_embeddings},
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.EMBEDDING_GENERATION)
            return False, results
        else:
            results.append(VerificationResult(
                stage=PipelineStage.EMBEDDING_GENERATION,
                check_name="embedding_values",
                status=VerificationStatus.PASSED,
                message="All embeddings have valid numerical values",
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        self.verification_results.extend(results)
        self._end_stage_timing(PipelineStage.EMBEDDING_GENERATION)
        return all(r.status != VerificationStatus.FAILED for r in results), results
    
    def verify_vector_storage(self, faiss_store, vector_ids: List[int]) -> Tuple[bool, List[VerificationResult]]:
        """Verify vector storage in FAISS"""
        self._start_stage_timing(PipelineStage.VECTOR_STORAGE)
        results = []
        
        # Check 1: Vectors stored
        start_time = time.time()
        if not vector_ids:
            results.append(VerificationResult(
                stage=PipelineStage.VECTOR_STORAGE,
                check_name="vectors_stored",
                status=VerificationStatus.FAILED,
                message="No vector IDs provided for verification",
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.VECTOR_STORAGE)
            return False, results
        
        results.append(VerificationResult(
            stage=PipelineStage.VECTOR_STORAGE,
            check_name="vectors_stored",
            status=VerificationStatus.PASSED,
            message=f"Stored {len(vector_ids)} vectors",
            details={"vector_count": len(vector_ids)},
            duration_ms=(time.time() - start_time) * 1000
        ))
        
        # Check 2: Vector retrieval test
        start_time = time.time()
        try:
            # Test retrieving first vector
            if vector_ids and hasattr(faiss_store, 'get_vector_metadata'):
                test_metadata = faiss_store.get_vector_metadata(vector_ids[0])
                if test_metadata:
                    results.append(VerificationResult(
                        stage=PipelineStage.VECTOR_STORAGE,
                        check_name="vector_retrieval",
                        status=VerificationStatus.PASSED,
                        message="Vectors can be retrieved successfully",
                        duration_ms=(time.time() - start_time) * 1000
                    ))
                else:
                    results.append(VerificationResult(
                        stage=PipelineStage.VECTOR_STORAGE,
                        check_name="vector_retrieval",
                        status=VerificationStatus.WARNING,
                        message="Vector metadata not found, but storage may be successful",
                        duration_ms=(time.time() - start_time) * 1000
                    ))
            else:
                results.append(VerificationResult(
                    stage=PipelineStage.VECTOR_STORAGE,
                    check_name="vector_retrieval",
                    status=VerificationStatus.SKIPPED,
                    message="Vector retrieval test skipped (method not available)",
                    duration_ms=(time.time() - start_time) * 1000
                ))
        except Exception as e:
            results.append(VerificationResult(
                stage=PipelineStage.VECTOR_STORAGE,
                check_name="vector_retrieval",
                status=VerificationStatus.WARNING,
                message=f"Vector retrieval test failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000
            ))
        
        self.verification_results.extend(results)
        self._end_stage_timing(PipelineStage.VECTOR_STORAGE)
        return all(r.status != VerificationStatus.FAILED for r in results), results
    
    def verify_metadata_storage(self, metadata_store, file_id: str) -> Tuple[bool, List[VerificationResult]]:
        """Verify metadata storage"""
        self._start_stage_timing(PipelineStage.METADATA_STORAGE)
        results = []
        
        # Check 1: File metadata stored
        start_time = time.time()
        try:
            file_metadata = metadata_store.get_file_metadata(file_id)
            if file_metadata:
                results.append(VerificationResult(
                    stage=PipelineStage.METADATA_STORAGE,
                    check_name="file_metadata_stored",
                    status=VerificationStatus.PASSED,
                    message="File metadata stored successfully",
                    details={"file_id": file_id},
                    duration_ms=(time.time() - start_time) * 1000
                ))
            else:
                results.append(VerificationResult(
                    stage=PipelineStage.METADATA_STORAGE,
                    check_name="file_metadata_stored",
                    status=VerificationStatus.FAILED,
                    message="File metadata not found after storage",
                    details={"file_id": file_id},
                    duration_ms=(time.time() - start_time) * 1000
                ))
                self._end_stage_timing(PipelineStage.METADATA_STORAGE)
                return False, results
        except Exception as e:
            results.append(VerificationResult(
                stage=PipelineStage.METADATA_STORAGE,
                check_name="file_metadata_stored",
                status=VerificationStatus.FAILED,
                message=f"Error retrieving file metadata: {str(e)}",
                details={"file_id": file_id, "error": str(e)},
                duration_ms=(time.time() - start_time) * 1000
            ))
            self._end_stage_timing(PipelineStage.METADATA_STORAGE)
            return False, results
        
        self.verification_results.extend(results)
        self._end_stage_timing(PipelineStage.METADATA_STORAGE)
        return all(r.status != VerificationStatus.FAILED for r in results), results
    
    def generate_verification_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(self.verification_results),
            "passed_checks": sum(1 for r in self.verification_results if r.status == VerificationStatus.PASSED),
            "failed_checks": sum(1 for r in self.verification_results if r.status == VerificationStatus.FAILED),
            "warning_checks": sum(1 for r in self.verification_results if r.status == VerificationStatus.WARNING),
            "skipped_checks": sum(1 for r in self.verification_results if r.status == VerificationStatus.SKIPPED),
            "stage_timings": self.stage_timings,
            "verification_results": [r.to_dict() for r in self.verification_results],
            "error_trace": self.error_trace
        }
        
        # Save report if requested
        if self.save_intermediate:
            report_path = self.debug_dir / f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, cls=EnumJSONEncoder)
            report["report_path"] = str(report_path)
        
        return report
    
    def add_error_trace(self, stage: str, error: Exception, context: Dict[str, Any] = None):
        """Add error to trace for debugging"""
        self.error_trace.append({
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }) 