"""
Enhanced Folder Monitor with Pipeline Verification
Provides comprehensive monitoring with detailed pipeline verification for all files in monitored folders
"""
import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from .folder_monitor import FolderMonitor, FileState
    from ..core.pipeline_verifier import PipelineVerifier, PipelineStage, VerificationStatus
    from ..core.verified_ingestion_engine import VerifiedIngestionEngine
except ImportError:
    from rag_system.src.monitoring.folder_monitor import FolderMonitor, FileState
    from rag_system.src.core.pipeline_verifier import PipelineVerifier, PipelineStage, VerificationStatus
    from rag_system.src.core.verified_ingestion_engine import VerifiedIngestionEngine

@dataclass
class FileProcessingState:
    """Enhanced file state with pipeline verification details"""
    file_path: str
    file_name: str
    folder_path: str
    size_mb: float
    status: str  # pending, processing, completed, failed
    current_stage: Optional[str] = None
    verification_results: Dict[str, List[Dict]] = None
    pipeline_progress: Dict[str, str] = None  # stage -> status
    processing_start_time: Optional[str] = None
    processing_end_time: Optional[str] = None
    total_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.verification_results is None:
            self.verification_results = {}
        if self.pipeline_progress is None:
            self.pipeline_progress = {
                "file_validation": "pending",
                "processor_selection": "pending", 
                "content_extraction": "pending",
                "text_chunking": "pending",
                "embedding_generation": "pending",
                "vector_storage": "pending",
                "metadata_storage": "pending"
            }
        if self.metrics is None:
            self.metrics = {}

class EnhancedFolderMonitor(FolderMonitor):
    """Enhanced folder monitor with pipeline verification integration"""
    
    def __init__(self, container=None, config_manager=None):
        super().__init__(container, config_manager)
        
        # Enhanced monitoring state
        self.file_processing_states: Dict[str, FileProcessingState] = {}
        self.processing_queue: List[str] = []
        self.active_processors = 0
        self.max_concurrent_processors = 3
        
        # Event callbacks for real-time updates
        self.event_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Processing statistics
        self.enhanced_stats = {
            "total_files_processed": 0,
            "files_in_queue": 0,
            "active_processors": 0,
            "average_processing_time": 0,
            "success_rate": 0,
            "stage_performance": {}
        }
        
        self.logger.info("Enhanced folder monitor initialized with pipeline verification")
    
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
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced monitoring status with pipeline details"""
        base_status = super().get_status()
        
        # Calculate enhanced statistics
        processing_files = [f for f in self.file_processing_states.values() if f.status == "processing"]
        completed_files = [f for f in self.file_processing_states.values() if f.status == "completed"]
        failed_files = [f for f in self.file_processing_states.values() if f.status == "failed"]
        
        # Calculate average processing time
        completed_durations = [f.total_duration_seconds for f in completed_files if f.total_duration_seconds]
        avg_processing_time = sum(completed_durations) / len(completed_durations) if completed_durations else 0
        
        # Calculate success rate
        total_processed = len(completed_files) + len(failed_files)
        success_rate = (len(completed_files) / total_processed * 100) if total_processed > 0 else 0
        
        enhanced_status = {
            **base_status,
            "enhanced_monitoring": True,
            "files_in_processing": len(processing_files),
            "files_completed": len(completed_files),
            "files_failed_verification": len(failed_files),
            "processing_queue_size": len(self.processing_queue),
            "active_processors": self.active_processors,
            "max_concurrent_processors": self.max_concurrent_processors,
            "average_processing_time_seconds": round(avg_processing_time, 2),
            "success_rate_percentage": round(success_rate, 2),
            "pipeline_stages": [stage.value for stage in PipelineStage],
            "recent_files": self._get_recent_file_states(10)
        }
        
        return enhanced_status
    
    def _get_recent_file_states(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent file processing states"""
        sorted_files = sorted(
            self.file_processing_states.values(),
            key=lambda f: f.processing_start_time or "0",
            reverse=True
        )
        
        return [asdict(f) for f in sorted_files[:limit]]
    
    def get_file_processing_details(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed processing information for a specific file"""
        if file_path in self.file_processing_states:
            return asdict(self.file_processing_states[file_path])
        return None
    
    def get_all_file_processing_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all file processing states"""
        return {path: asdict(state) for path, state in self.file_processing_states.items()}
    
    def _process_changes(self, changes: List[Tuple[str, str]]):
        """Enhanced process changes with pipeline verification"""
        if not self.container:
            self.logger.warning("No container available for ingestion")
            return
        
        for change_type, file_path in changes:
            if change_type in ['new', 'modified']:
                self._queue_file_for_processing(file_path)
            elif change_type == 'deleted':
                self._handle_deleted_file_enhanced(file_path)
        
        # Process queued files
        self._process_queue()
    
    def _queue_file_for_processing(self, file_path: str):
        """Queue file for enhanced processing with verification"""
        file_name = os.path.basename(file_path)
        folder_path = os.path.dirname(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0
        
        # Create enhanced file processing state
        processing_state = FileProcessingState(
            file_path=file_path,
            file_name=file_name,
            folder_path=folder_path,
            size_mb=round(file_size_mb, 2),
            status="pending"
        )
        
        self.file_processing_states[file_path] = processing_state
        
        if file_path not in self.processing_queue:
            self.processing_queue.append(file_path)
            
            self._emit_event("file_queued", {
                "file_path": file_path,
                "file_name": file_name,
                "size_mb": processing_state.size_mb,
                "queue_position": len(self.processing_queue)
            })
            
            self.logger.info(f"Queued file for processing: {file_name} ({processing_state.size_mb}MB)")
    
    def _process_queue(self):
        """Process files in the queue with concurrent processing"""
        while (self.processing_queue and 
               self.active_processors < self.max_concurrent_processors):
            
            file_path = self.processing_queue.pop(0)
            if file_path in self.file_processing_states:
                # Start processing in a separate thread
                thread = threading.Thread(
                    target=self._process_file_with_verification,
                    args=(file_path,),
                    daemon=True
                )
                thread.start()
    
    def _process_file_with_verification(self, file_path: str):
        """Process a single file with comprehensive pipeline verification"""
        self.active_processors += 1
        processing_state = self.file_processing_states.get(file_path)
        
        if not processing_state:
            self.active_processors -= 1
            return
        
        try:
            # Update status to processing
            processing_state.status = "processing"
            processing_state.processing_start_time = datetime.now().isoformat()
            start_time = time.time()
            
            self._emit_event("file_processing_started", {
                "file_path": file_path,
                "file_name": processing_state.file_name,
                "size_mb": processing_state.size_mb
            })
            
            # Get verified ingestion engine
            verified_engine = self._get_verified_ingestion_engine()
            if not verified_engine:
                raise Exception("Verified ingestion engine not available")
            
            # Set up verification callback for real-time updates
            def verification_callback(event):
                self._handle_verification_event(file_path, event)
            
            verified_engine.verifier.add_event_callback(verification_callback)
            
            # Prepare metadata
            metadata = {
                "source": "enhanced_folder_monitor",
                "original_path": file_path,
                "monitored_folder": self._get_parent_folder(file_path),
                "file_size_mb": processing_state.size_mb,
                "processing_start_time": processing_state.processing_start_time
            }
            
            # Process file with verification
            result = verified_engine.ingest_file_with_verification(file_path, metadata)
            
            # Update processing state with results
            processing_state.processing_end_time = datetime.now().isoformat()
            processing_state.total_duration_seconds = round(time.time() - start_time, 2)
            
            if result.get('success', False):
                processing_state.status = "completed"
                processing_state.verification_results = result.get('verification_results', {})
                processing_state.metrics = {
                    "chunks_created": result.get('chunks_created', 0),
                    "vectors_stored": result.get('vectors_stored', 0),
                    "processing_time": processing_state.total_duration_seconds
                }
                
                self._emit_event("file_processing_completed", {
                    "file_path": file_path,
                    "file_name": processing_state.file_name,
                    "duration_seconds": processing_state.total_duration_seconds,
                    "chunks_created": processing_state.metrics.get("chunks_created", 0),
                    "success": True
                })
                
                self.logger.info(f"Successfully processed: {processing_state.file_name} "
                               f"({processing_state.total_duration_seconds}s)")
            else:
                processing_state.status = "failed"
                processing_state.error_message = result.get('error', 'Unknown error')
                processing_state.verification_results = result.get('verification_results', {})
                
                self._emit_event("file_processing_failed", {
                    "file_path": file_path,
                    "file_name": processing_state.file_name,
                    "error": processing_state.error_message,
                    "duration_seconds": processing_state.total_duration_seconds
                })
                
                self.logger.error(f"Failed to process {processing_state.file_name}: "
                                f"{processing_state.error_message}")
        
        except Exception as e:
            processing_state.status = "failed"
            processing_state.error_message = str(e)
            processing_state.processing_end_time = datetime.now().isoformat()
            processing_state.total_duration_seconds = round(time.time() - start_time, 2) if 'start_time' in locals() else 0
            
            self._emit_event("file_processing_error", {
                "file_path": file_path,
                "file_name": processing_state.file_name,
                "error": str(e)
            })
            
            self.logger.error(f"Exception processing {processing_state.file_name}: {e}")
        
        finally:
            self.active_processors -= 1
            # Process next file in queue if available
            if self.processing_queue:
                self._process_queue()
    
    def _handle_verification_event(self, file_path: str, event: Dict[str, Any]):
        """Handle verification events for real-time updates"""
        processing_state = self.file_processing_states.get(file_path)
        if not processing_state:
            return
        
        event_type = event.get("type")
        event_data = event.get("data", {})
        
        if event_type == "stage_started":
            stage = event_data.get("stage")
            if stage:
                processing_state.current_stage = stage
                processing_state.pipeline_progress[stage] = "running"
                
                self._emit_event("pipeline_stage_started", {
                    "file_path": file_path,
                    "file_name": processing_state.file_name,
                    "stage": stage
                })
        
        elif event_type == "stage_completed":
            stage = event_data.get("stage")
            if stage:
                processing_state.pipeline_progress[stage] = "completed"
                
                self._emit_event("pipeline_stage_completed", {
                    "file_path": file_path,
                    "file_name": processing_state.file_name,
                    "stage": stage,
                    "duration": event_data.get("duration", 0)
                })
    
    def _get_verified_ingestion_engine(self) -> Optional[VerifiedIngestionEngine]:
        """Get or create verified ingestion engine"""
        if not self.container:
            return None
        
        # Try to get existing verified engine
        verified_engine = self.container.get('verified_ingestion_engine')
        if verified_engine:
            return verified_engine
        
        # Create new verified engine if not available
        ingestion_engine = self.container.get('ingestion_engine')
        if ingestion_engine:
            verifier = PipelineVerifier(debug_mode=True, save_intermediate=True)
            verified_engine = VerifiedIngestionEngine(ingestion_engine, verifier)
            return verified_engine
        
        return None
    
    def _handle_deleted_file_enhanced(self, file_path: str):
        """Handle deleted file with enhanced tracking"""
        # Remove from processing states
        if file_path in self.file_processing_states:
            file_state = self.file_processing_states[file_path]
            del self.file_processing_states[file_path]
            
            self._emit_event("file_deleted", {
                "file_path": file_path,
                "file_name": file_state.file_name
            })
        
        # Remove from queue if present
        if file_path in self.processing_queue:
            self.processing_queue.remove(file_path)
        
        # Handle deletion in parent class
        if self.container and self.container.get('ingestion_engine'):
            super()._handle_deleted_file(file_path, self.container.get('ingestion_engine'))
    
    def force_process_file(self, file_path: str) -> Dict[str, Any]:
        """Force processing of a specific file"""
        if not os.path.exists(file_path):
            return {"success": False, "error": "File does not exist"}
        
        if file_path in self.file_processing_states:
            current_state = self.file_processing_states[file_path]
            if current_state.status == "processing":
                return {"success": False, "error": "File is already being processed"}
        
        # Queue file for processing
        self._queue_file_for_processing(file_path)
        self._process_queue()
        
        return {
            "success": True,
            "message": f"File queued for processing: {os.path.basename(file_path)}",
            "queue_position": len(self.processing_queue)
        }
    
    def get_pipeline_visualization_data(self) -> Dict[str, Any]:
        """Get data for pipeline visualization dashboard"""
        stages = [
            {"id": "file_validation", "name": "File Validation", "icon": "📁"},
            {"id": "processor_selection", "name": "Processor Selection", "icon": "⚙️"},
            {"id": "content_extraction", "name": "Content Extraction", "icon": "📄"},
            {"id": "text_chunking", "name": "Text Chunking", "icon": "✂️"},
            {"id": "embedding_generation", "name": "Embedding Generation", "icon": "🧮"},
            {"id": "vector_storage", "name": "Vector Storage", "icon": "💾"},
            {"id": "metadata_storage", "name": "Metadata Storage", "icon": "🏷️"}
        ]
        
        # Get current processing files
        processing_files = []
        for file_path, state in self.file_processing_states.items():
            if state.status in ["processing", "pending"]:
                processing_files.append({
                    "file_path": file_path,
                    "file_name": state.file_name,
                    "status": state.status,
                    "current_stage": state.current_stage,
                    "pipeline_progress": state.pipeline_progress,
                    "size_mb": state.size_mb,
                    "processing_start_time": state.processing_start_time
                })
        
        return {
            "stages": stages,
            "processing_files": processing_files,
            "queue_size": len(self.processing_queue),
            "active_processors": self.active_processors,
            "max_concurrent": self.max_concurrent_processors
        }

# Global enhanced instance
enhanced_folder_monitor = None

def initialize_enhanced_folder_monitor(container, config_manager):
    """Initialize the global enhanced folder monitor"""
    global enhanced_folder_monitor
    enhanced_folder_monitor = EnhancedFolderMonitor(container, config_manager)
    return enhanced_folder_monitor

def get_enhanced_folder_monitor():
    """Get the global enhanced folder monitor instance"""
    return enhanced_folder_monitor 