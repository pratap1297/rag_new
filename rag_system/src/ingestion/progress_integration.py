"""
Progress tracking integration for ingestion pipeline
"""
import time
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from ..core.progress_tracker import ProgressTracker, ProgressStage, ProgressStatus

class ProgressTrackedIngestion:
    """Helper class to integrate progress tracking with ingestion"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
    
    @contextmanager
    def track_stage(self, file_path: str, stage: ProgressStage):
        """Context manager for tracking a stage"""
        start_time = time.time()
        self.progress_tracker.update_stage(file_path, stage, 0.0, ProgressStatus.RUNNING)
        
        try:
            yield self
            # Auto-complete stage if not explicitly completed
            if self.progress_tracker.get_progress(file_path).stages[stage].status != ProgressStatus.COMPLETED:
                self.progress_tracker.complete_stage(file_path, stage)
        except Exception as e:
            self.progress_tracker.update_stage(file_path, stage, status=ProgressStatus.FAILED)
            raise
        finally:
            elapsed = time.time() - start_time
            self.progress_tracker.update_stage(file_path, stage, details={'duration': elapsed})
    
    def update_progress(self, file_path: str, stage: ProgressStage, progress: float, details: Optional[Dict] = None):
        """Update progress for current stage"""
        self.progress_tracker.update_stage(file_path, stage, progress, details=details) 