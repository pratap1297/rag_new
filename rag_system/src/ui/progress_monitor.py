"""
Real-time progress monitoring UI
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from fastapi import WebSocket
from ..core.progress_tracker import ProgressTracker, FileProgress

class ProgressMonitor:
    """WebSocket-based real-time progress monitor"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.active_connections: List[WebSocket] = []
        
        # Register callbacks
        progress_tracker.register_progress_callback(self._on_progress_update)
        progress_tracker.register_completion_callback(self._on_file_complete)
        progress_tracker.register_error_callback(self._on_error)
    
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send initial state
        await self._send_full_state(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def _send_full_state(self, websocket: WebSocket):
        """Send complete progress state to a client"""
        state = {
            'type': 'full_state',
            'timestamp': datetime.now().isoformat(),
            'files': {
                path: self._serialize_progress(progress)
                for path, progress in self.progress_tracker.get_all_progress().items()
            },
            'system_metrics': self.progress_tracker.get_system_metrics()
        }
        
        await websocket.send_json(state)
    
    def _serialize_progress(self, progress: FileProgress) -> Dict[str, Any]:
        """Serialize FileProgress for JSON transmission"""
        return {
            'file_path': progress.file_path,
            'file_size': progress.file_size,
            'status': progress.status.value,
            'current_stage': progress.current_stage.value,
            'overall_progress': progress.overall_progress,
            'started_at': progress.started_at.isoformat() if progress.started_at else None,
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'error': progress.error,
            'chunks_created': progress.chunks_created,
            'vectors_created': progress.vectors_created,
            'estimated_time_remaining': str(progress.estimated_time_remaining) if progress.estimated_time_remaining else None,
            'stages': {
                stage.value: {
                    'status': info.status.value,
                    'progress': info.progress,
                    'duration': str(info.duration) if info.duration else None
                }
                for stage, info in progress.stages.items()
            }
        }
    
    def _on_progress_update(self, file_path: str, progress: FileProgress):
        """Handle progress update - synchronous version for non-async contexts"""
        try:
            message = {
                'type': 'progress_update',
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path,
                'progress': self._serialize_progress(progress)
            }
            
            # Log progress update instead of broadcasting in sync context
            logging.info(f"Progress update for {file_path}: {progress.current_stage.value} - {progress.overall_progress * 100:.1f}%")
            
        except Exception as e:
            logging.error(f"Error in progress update callback: {e}")
    
    def _on_file_complete(self, file_path: str, progress: FileProgress):
        """Handle file completion - synchronous version for non-async contexts"""
        try:
            message = {
                'type': 'file_complete',
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path,
                'progress': self._serialize_progress(progress)
            }
            
            # Log completion instead of broadcasting in sync context
            logging.info(f"File completed: {file_path} - {progress.chunks_created} chunks, {progress.vectors_created} vectors")
            
        except Exception as e:
            logging.error(f"Error in file completion callback: {e}")
    
    def _on_error(self, file_path: str, progress: FileProgress, error: Exception):
        """Handle error - synchronous version for non-async contexts"""
        try:
            message = {
                'type': 'error',
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path,
                'error': str(error),
                'progress': self._serialize_progress(progress)
            }
            
            # Log error instead of broadcasting in sync context
            logging.error(f"File processing error: {file_path} - {str(error)}")
            
        except Exception as e:
            logging.error(f"Error in error callback: {e}") 