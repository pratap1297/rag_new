"""
Enhanced Folder Monitoring API Endpoints
Provides comprehensive folder monitoring with pipeline verification
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from ..monitoring.enhanced_folder_monitor import EnhancedFolderMonitor, get_enhanced_folder_monitor
    from ..core.dependency_container import get_dependency_container
except ImportError:
    from rag_system.src.monitoring.enhanced_folder_monitor import EnhancedFolderMonitor, get_enhanced_folder_monitor
    from rag_system.src.core.dependency_container import get_dependency_container

# Router for enhanced folder monitoring
router = APIRouter(prefix="/api/enhanced-folder", tags=["enhanced-folder-monitoring"])

# WebSocket connection manager for folder monitoring
class FolderMonitorConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logging.error(f"Error broadcasting message to websocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

folder_manager = FolderMonitorConnectionManager()

# Request/Response models
class AddFolderRequest(BaseModel):
    folder_path: str
    auto_start_monitoring: bool = True

class ProcessFileRequest(BaseModel):
    file_path: str

class MonitoringConfigRequest(BaseModel):
    check_interval: Optional[int] = None
    max_concurrent_processors: Optional[int] = None
    auto_ingest: Optional[bool] = None

# WebSocket endpoint for real-time folder monitoring updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await folder_manager.connect(websocket)
    
    # Set up event callback for the enhanced folder monitor
    # Note: WebSocket doesn't have access to app state, so we'll use the global function
    enhanced_monitor = get_enhanced_folder_monitor()
    if enhanced_monitor:
        def event_callback(event):
            # Send event to WebSocket clients
            asyncio.create_task(folder_manager.broadcast(event))
        
        enhanced_monitor.add_event_callback(event_callback)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for connection testing
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        folder_manager.disconnect(websocket)

# Get enhanced monitoring status
@router.get("/status")
async def get_enhanced_status(request: Request):
    """Get comprehensive monitoring status with pipeline details"""
    try:
        # Get enhanced monitor from app state
        enhanced_monitor = getattr(request.app.state, 'enhanced_folder_monitor', None)
        if not enhanced_monitor:
            raise HTTPException(status_code=500, detail="Enhanced folder monitor not available")
        
        status = enhanced_monitor.get_enhanced_status()
        return {
            "status": "success",
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

# Enhanced folder monitoring dashboard
@router.get("/dashboard", response_class=HTMLResponse)
async def get_enhanced_dashboard():
    """Get the enhanced folder monitoring dashboard"""
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enhanced Folder Monitoring Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #ffffff;
                min-height: 100vh;
            }
            
            .dashboard-container {
                display: grid;
                grid-template-columns: 300px 1fr;
                min-height: 100vh;
            }
            
            .sidebar {
                background: rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                padding: 20px;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                overflow-y: auto;
            }
            
            .main-content {
                padding: 20px;
                overflow-y: auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                font-size: 2.2em;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #fff, #e0e0e0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .status-card {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                border-left: 4px solid #4CAF50;
            }
            
            .pipeline-stage {
                display: flex;
                align-items: center;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-bottom: 10px;
                transition: all 0.3s ease;
            }
            
            .pipeline-stage.completed {
                background: rgba(76, 175, 80, 0.2);
                border-left: 4px solid #4CAF50;
            }
            
            .pipeline-stage.running {
                background: rgba(255, 152, 0, 0.2);
                border-left: 4px solid #FF9800;
                animation: pulse 2s infinite;
            }
            
            .pipeline-stage.failed {
                background: rgba(244, 67, 54, 0.2);
                border-left: 4px solid #f44336;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .stage-icon {
                font-size: 1.5em;
                margin-right: 15px;
            }
            
            .stage-info {
                flex: 1;
            }
            
            .stage-status {
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.85em;
                font-weight: 500;
            }
            
            .status-completed {
                background: #4CAF50;
                color: white;
            }
            
            .status-running {
                background: #FF9800;
                color: white;
            }
            
            .status-pending {
                background: #666;
                color: white;
            }
            
            .status-failed {
                background: #f44336;
                color: white;
            }
            
            .connection-status {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 500;
            }
            
            .connected {
                background: #4CAF50;
                color: white;
            }
            
            .disconnected {
                background: #f44336;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="connection-status" id="connectionStatus">
            🔴 Disconnected
        </div>
        
        <div class="dashboard-container">
            <div class="sidebar">
                <div class="header">
                    <h1>📁 Enhanced Folder Monitor</h1>
                    <p>Pipeline Verification Monitoring</p>
                </div>
                
                <div class="status-card">
                    <h3>📊 Status</h3>
                    <div id="monitoringStatus">Loading...</div>
                </div>
            </div>
            
            <div class="main-content">
                <div class="header">
                    <h1>🔍 Pipeline Visualization</h1>
                    <p>Real-time processing pipeline monitoring</p>
                </div>
                
                <div class="pipeline-visualization">
                    <h3>📋 Pipeline Stages</h3>
                    <div id="pipelineStages">
                        <div class="pipeline-stage pending">
                            <div class="stage-icon">📁</div>
                            <div class="stage-info">
                                <div class="stage-name">File Validation</div>
                                <div class="stage-description">Checking file existence, size, and permissions</div>
                            </div>
                            <div class="stage-status status-pending">Pending</div>
                        </div>
                        
                        <div class="pipeline-stage pending">
                            <div class="stage-icon">⚙️</div>
                            <div class="stage-info">
                                <div class="stage-name">Processor Selection</div>
                                <div class="stage-description">Selecting appropriate processor for file type</div>
                            </div>
                            <div class="stage-status status-pending">Pending</div>
                        </div>
                        
                        <div class="pipeline-stage pending">
                            <div class="stage-icon">📄</div>
                            <div class="stage-info">
                                <div class="stage-name">Content Extraction</div>
                                <div class="stage-description">Extracting text and content from file</div>
                            </div>
                            <div class="stage-status status-pending">Pending</div>
                        </div>
                        
                        <div class="pipeline-stage pending">
                            <div class="stage-icon">✂️</div>
                            <div class="stage-info">
                                <div class="stage-name">Text Chunking</div>
                                <div class="stage-description">Breaking text into manageable chunks</div>
                            </div>
                            <div class="stage-status status-pending">Pending</div>
                        </div>
                        
                        <div class="pipeline-stage pending">
                            <div class="stage-icon">🧮</div>
                            <div class="stage-info">
                                <div class="stage-name">Embedding Generation</div>
                                <div class="stage-description">Creating vector embeddings for chunks</div>
                            </div>
                            <div class="stage-status status-pending">Pending</div>
                        </div>
                        
                        <div class="pipeline-stage pending">
                            <div class="stage-icon">💾</div>
                            <div class="stage-info">
                                <div class="stage-name">Vector Storage</div>
                                <div class="stage-description">Storing vectors in FAISS index</div>
                            </div>
                            <div class="stage-status status-pending">Pending</div>
                        </div>
                        
                        <div class="pipeline-stage pending">
                            <div class="stage-icon">🏷️</div>
                            <div class="stage-info">
                                <div class="stage-name">Metadata Storage</div>
                                <div class="stage-description">Storing file and chunk metadata</div>
                            </div>
                            <div class="stage-status status-pending">Pending</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/enhanced-folder/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('WebSocket connected');
                    updateConnectionStatus(true);
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = function() {
                    console.log('WebSocket disconnected');
                    updateConnectionStatus(false);
                    setTimeout(connectWebSocket, 5000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    updateConnectionStatus(false);
                };
            }
            
            function updateConnectionStatus(connected) {
                const statusElement = document.getElementById('connectionStatus');
                if (connected) {
                    statusElement.textContent = '🟢 Connected';
                    statusElement.className = 'connection-status connected';
                } else {
                    statusElement.textContent = '🔴 Disconnected';
                    statusElement.className = 'connection-status disconnected';
                }
            }
            
            function handleWebSocketMessage(data) {
                console.log('Received:', data);
                
                switch(data.type) {
                    case 'pipeline_stage_started':
                        updatePipelineStage(data.data.stage, 'running');
                        break;
                    case 'pipeline_stage_completed':
                        updatePipelineStage(data.data.stage, 'completed');
                        break;
                    case 'file_processing_failed':
                        // Reset all stages to pending when processing fails
                        resetPipelineStages();
                        break;
                }
            }
            
            function updatePipelineStage(stageName, status) {
                const stages = document.querySelectorAll('.pipeline-stage');
                stages.forEach(stage => {
                    const stageInfo = stage.querySelector('.stage-info .stage-name');
                    if (stageInfo && stageInfo.textContent.toLowerCase().includes(stageName.replace('_', ' '))) {
                        stage.className = `pipeline-stage ${status}`;
                        const statusElement = stage.querySelector('.stage-status');
                        statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                        statusElement.className = `stage-status status-${status}`;
                    }
                });
            }
            
            function resetPipelineStages() {
                const stages = document.querySelectorAll('.pipeline-stage');
                stages.forEach(stage => {
                    stage.className = 'pipeline-stage pending';
                    const statusElement = stage.querySelector('.stage-status');
                    statusElement.textContent = 'Pending';
                    statusElement.className = 'stage-status status-pending';
                });
            }
            
            async function updateStatus() {
                try {
                    const response = await fetch('/api/enhanced-folder/status');
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        const status = result.data;
                        document.getElementById('monitoringStatus').innerHTML = `
                            <div>Status: ${status.is_running ? '🟢 Running' : '🔴 Stopped'}</div>
                            <div>Files Tracked: ${status.total_files_tracked}</div>
                            <div>Processing: ${status.files_in_processing || 0}</div>
                            <div>Completed: ${status.files_completed || 0}</div>
                            <div>Queue: ${status.processing_queue_size || 0}</div>
                        `;
                    }
                } catch (error) {
                    console.error('Failed to update status:', error);
                }
            }
            
            // Initialize
            connectWebSocket();
            updateStatus();
            
            // Update every 30 seconds
            setInterval(updateStatus, 30000);
        </script>
    </body>
    </html>
    """
    return dashboard_html 