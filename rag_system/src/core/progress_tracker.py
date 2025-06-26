"""
Comprehensive Progress Tracking System for RAG Ingestion Pipeline
"""
import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
from collections import defaultdict
import psutil
import traceback

class ProgressStatus(Enum):
    """Status of a progress operation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ProgressStage(Enum):
    """Stages of document processing"""
    QUEUED = "queued"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    INDEXING = "indexing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"

@dataclass
class StageInfo:
    """Information about a processing stage"""
    name: str
    status: ProgressStatus
    progress: float  # 0.0 to 1.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.now() - self.started_at
        return None

@dataclass
class FileProgress:
    """Progress tracking for a single file"""
    file_path: str
    file_size: int
    status: ProgressStatus = ProgressStatus.PENDING
    current_stage: ProgressStage = ProgressStage.QUEUED
    stages: Dict[ProgressStage, StageInfo] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Metrics
    chunks_created: int = 0
    vectors_created: int = 0
    bytes_processed: int = 0
    
    # Performance metrics
    extraction_time: float = 0.0
    chunking_time: float = 0.0
    embedding_time: float = 0.0
    storage_time: float = 0.0
    
    def __post_init__(self):
        # Initialize all stages
        for stage in ProgressStage:
            self.stages[stage] = StageInfo(
                name=stage.value,
                status=ProgressStatus.PENDING,
                progress=0.0
            )
    
    @property
    def overall_progress(self) -> float:
        """Calculate overall progress across all stages"""
        if self.status == ProgressStatus.COMPLETED:
            return 1.0
        
        # Weight for each stage
        weights = {
            ProgressStage.QUEUED: 0.05,
            ProgressStage.VALIDATING: 0.1,
            ProgressStage.EXTRACTING: 0.2,
            ProgressStage.CHUNKING: 0.15,
            ProgressStage.EMBEDDING: 0.25,
            ProgressStage.STORING: 0.15,
            ProgressStage.INDEXING: 0.05,
            ProgressStage.FINALIZING: 0.05,
        }
        
        total_progress = 0.0
        for stage, weight in weights.items():
            stage_info = self.stages.get(stage)
            if stage_info:
                if stage_info.status == ProgressStatus.COMPLETED:
                    total_progress += weight
                elif stage_info.status == ProgressStatus.RUNNING:
                    total_progress += weight * stage_info.progress
        
        return min(total_progress, 1.0)
    
    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimate remaining time based on current progress"""
        if not self.started_at or self.overall_progress == 0:
            return None
        
        elapsed = (datetime.now() - self.started_at).total_seconds()
        if self.overall_progress > 0:
            total_estimated = elapsed / self.overall_progress
            remaining = total_estimated - elapsed
            return timedelta(seconds=max(0, remaining))
        return None

class ProgressTracker:
    """Main progress tracking system"""
    
    def __init__(self, 
                 persistence_path: Optional[str] = "data/progress/ingestion_progress.json",
                 auto_save_interval: int = 5):
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.auto_save_interval = auto_save_interval
        
        # Progress storage
        self.file_progress: Dict[str, FileProgress] = {}
        self.batch_progress: Dict[str, List[str]] = {}  # batch_id -> file_paths
        
        # Callbacks
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # System metrics
        self.system_metrics = {
            'total_files_processed': 0,
            'total_bytes_processed': 0,
            'total_chunks_created': 0,
            'total_vectors_created': 0,
            'total_errors': 0,
            'start_time': None,
            'last_update': None
        }
        
        # Performance monitoring
        self._start_time = time.time()
        self._lock = threading.RLock()
        self._auto_save_thread = None
        self._stop_auto_save = threading.Event()
        
        # Load existing progress if available
        if self.persistence_path:
            self._load_progress()
            self._start_auto_save()
        
        logging.info("Progress tracker initialized")
    
    def register_progress_callback(self, callback: Callable[[str, FileProgress], None]):
        """Register a callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def register_completion_callback(self, callback: Callable[[str, FileProgress], None]):
        """Register a callback for file completion"""
        self.completion_callbacks.append(callback)
    
    def register_error_callback(self, callback: Callable[[str, FileProgress, Exception], None]):
        """Register a callback for errors"""
        self.error_callbacks.append(callback)
    
    def start_file(self, file_path: str, file_size: Optional[int] = None) -> FileProgress:
        """Start tracking a new file"""
        with self._lock:
            if file_size is None:
                try:
                    file_size = Path(file_path).stat().st_size
                except:
                    file_size = 0
            
            progress = FileProgress(
                file_path=file_path,
                file_size=file_size,
                status=ProgressStatus.RUNNING,
                started_at=datetime.now()
            )
            
            self.file_progress[file_path] = progress
            self.system_metrics['last_update'] = datetime.now()
            
            if self.system_metrics['start_time'] is None:
                self.system_metrics['start_time'] = datetime.now()
            
            self._trigger_progress_callbacks(file_path, progress)
            
            return progress
    
    def update_stage(self, 
                    file_path: str, 
                    stage: ProgressStage, 
                    progress: float = 0.0,
                    status: Optional[ProgressStatus] = None,
                    details: Optional[Dict[str, Any]] = None):
        """Update progress for a specific stage"""
        with self._lock:
            if file_path not in self.file_progress:
                return
            
            file_progress = self.file_progress[file_path]
            stage_info = file_progress.stages[stage]
            
            # Update stage info
            if status:
                stage_info.status = status
                if status == ProgressStatus.RUNNING and not stage_info.started_at:
                    stage_info.started_at = datetime.now()
                elif status == ProgressStatus.COMPLETED:
                    stage_info.completed_at = datetime.now()
                    stage_info.progress = 1.0
            
            if progress is not None:
                stage_info.progress = max(0.0, min(1.0, progress))
            
            if details:
                stage_info.details.update(details)
            
            # Update current stage
            file_progress.current_stage = stage
            
            # Trigger callbacks
            self._trigger_progress_callbacks(file_path, file_progress)
    
    def complete_stage(self, file_path: str, stage: ProgressStage, details: Optional[Dict[str, Any]] = None):
        """Mark a stage as completed"""
        self.update_stage(file_path, stage, 1.0, ProgressStatus.COMPLETED, details)
    
    def fail_file(self, file_path: str, error: Exception, stage: Optional[ProgressStage] = None):
        """Mark a file as failed"""
        with self._lock:
            if file_path not in self.file_progress:
                return
            
            file_progress = self.file_progress[file_path]
            file_progress.status = ProgressStatus.FAILED
            file_progress.error = str(error)
            file_progress.error_traceback = traceback.format_exc()
            file_progress.completed_at = datetime.now()
            
            if stage:
                stage_info = file_progress.stages[stage]
                stage_info.status = ProgressStatus.FAILED
                stage_info.error = str(error)
            
            self.system_metrics['total_errors'] += 1
            
            # Trigger error callbacks
            for callback in self.error_callbacks:
                try:
                    callback(file_path, file_progress, error)
                except Exception as e:
                    logging.error(f"Error in error callback: {e}")
    
    def complete_file(self, file_path: str, metrics: Optional[Dict[str, Any]] = None):
        """Mark a file as completed"""
        with self._lock:
            if file_path not in self.file_progress:
                return
            
            file_progress = self.file_progress[file_path]
            file_progress.status = ProgressStatus.COMPLETED
            file_progress.completed_at = datetime.now()
            
            # Update metrics
            if metrics:
                file_progress.chunks_created = metrics.get('chunks_created', 0)
                file_progress.vectors_created = metrics.get('vectors_created', 0)
                file_progress.extraction_time = metrics.get('extraction_time', 0.0)
                file_progress.chunking_time = metrics.get('chunking_time', 0.0)
                file_progress.embedding_time = metrics.get('embedding_time', 0.0)
                file_progress.storage_time = metrics.get('storage_time', 0.0)
            
            # Update system metrics
            self.system_metrics['total_files_processed'] += 1
            self.system_metrics['total_bytes_processed'] += file_progress.file_size
            self.system_metrics['total_chunks_created'] += file_progress.chunks_created
            self.system_metrics['total_vectors_created'] += file_progress.vectors_created
            
            # Trigger progress callbacks with final status
            self._trigger_progress_callbacks(file_path, file_progress)
            
            # Trigger completion callbacks
            for callback in self.completion_callbacks:
                try:
                    callback(file_path, file_progress)
                except Exception as e:
                    logging.error(f"Error in completion callback: {e}")
    
    def get_progress(self, file_path: str) -> Optional[FileProgress]:
        """Get progress for a specific file"""
        with self._lock:
            return self.file_progress.get(file_path)
    
    def get_all_progress(self) -> Dict[str, FileProgress]:
        """Get progress for all files"""
        with self._lock:
            return self.file_progress.copy()
    
    def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        """Get aggregated progress for a batch"""
        with self._lock:
            if batch_id not in self.batch_progress:
                return {}
            
            file_paths = self.batch_progress[batch_id]
            total_files = len(file_paths)
            completed_files = 0
            failed_files = 0
            total_progress = 0.0
            
            for file_path in file_paths:
                if file_path in self.file_progress:
                    progress = self.file_progress[file_path]
                    if progress.status == ProgressStatus.COMPLETED:
                        completed_files += 1
                    elif progress.status == ProgressStatus.FAILED:
                        failed_files += 1
                    total_progress += progress.overall_progress
            
            return {
                'batch_id': batch_id,
                'total_files': total_files,
                'completed_files': completed_files,
                'failed_files': failed_files,
                'running_files': total_files - completed_files - failed_files,
                'overall_progress': total_progress / total_files if total_files > 0 else 0.0,
                'file_progress': {fp: self.file_progress.get(fp) for fp in file_paths}
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics"""
        with self._lock:
            metrics = self.system_metrics.copy()
            
            # Calculate rates
            if metrics['start_time']:
                elapsed = (datetime.now() - metrics['start_time']).total_seconds()
                if elapsed > 0:
                    metrics['files_per_minute'] = (metrics['total_files_processed'] / elapsed) * 60
                    metrics['mb_per_minute'] = (metrics['total_bytes_processed'] / (1024 * 1024) / elapsed) * 60
            
            # Add system resource usage
            metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            metrics['memory_percent'] = psutil.virtual_memory().percent
            metrics['disk_usage_percent'] = psutil.disk_usage('/').percent
            
            return metrics
    
    def create_batch(self, batch_id: str, file_paths: List[str]):
        """Create a batch for tracking multiple files"""
        with self._lock:
            self.batch_progress[batch_id] = file_paths
    
    def _trigger_progress_callbacks(self, file_path: str, progress: FileProgress):
        """Trigger progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(file_path, progress)
            except Exception as e:
                logging.error(f"Error in progress callback: {e}")
    
    def _save_progress(self):
        """Save progress to disk"""
        if not self.persistence_path:
            return
        
        with self._lock:
            try:
                self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Convert to serializable format
                data = {
                    'file_progress': {
                        path: {
                            'file_path': p.file_path,
                            'file_size': p.file_size,
                            'status': p.status.value,
                            'current_stage': p.current_stage.value,
                            'started_at': p.started_at.isoformat() if p.started_at else None,
                            'completed_at': p.completed_at.isoformat() if p.completed_at else None,
                            'error': p.error,
                            'chunks_created': p.chunks_created,
                            'vectors_created': p.vectors_created,
                            'overall_progress': p.overall_progress
                        }
                        for path, p in self.file_progress.items()
                    },
                    'system_metrics': {
                        k: v.isoformat() if isinstance(v, datetime) else v
                        for k, v in self.system_metrics.items()
                    },
                    'saved_at': datetime.now().isoformat()
                }
                
                with open(self.persistence_path, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            except Exception as e:
                logging.error(f"Failed to save progress: {e}")
    
    def _load_progress(self):
        """Load progress from disk"""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
            
            # Restore file progress for incomplete files only
            for path, progress_data in data.get('file_progress', {}).items():
                if progress_data.get('status') not in ['completed', 'failed']:
                    # Restore as pending
                    progress = FileProgress(
                        file_path=progress_data['file_path'],
                        file_size=progress_data['file_size'],
                        status=ProgressStatus.PENDING,
                        chunks_created=progress_data.get('chunks_created', 0),
                        vectors_created=progress_data.get('vectors_created', 0)
                    )
                    self.file_progress[path] = progress
            
            # Restore system metrics
            saved_metrics = data.get('system_metrics', {})
            for key in ['total_files_processed', 'total_bytes_processed', 
                       'total_chunks_created', 'total_vectors_created', 'total_errors']:
                if key in saved_metrics:
                    self.system_metrics[key] = saved_metrics[key]
                    
        except Exception as e:
            logging.error(f"Failed to load progress: {e}")
    
    def _start_auto_save(self):
        """Start auto-save thread"""
        def auto_save_loop():
            while not self._stop_auto_save.wait(self.auto_save_interval):
                self._save_progress()
        
        self._auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
        self._auto_save_thread.start()
    
    def shutdown(self):
        """Shutdown progress tracker"""
        if self._auto_save_thread:
            self._stop_auto_save.set()
            self._auto_save_thread.join(timeout=5)
        
        self._save_progress() 