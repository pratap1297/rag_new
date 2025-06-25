"""
Simple Enhanced Folder Monitoring API Endpoints
Provides basic enhanced folder monitoring without complex dependencies
"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Router for simple enhanced folder monitoring
router = APIRouter(prefix="/api/enhanced-folder", tags=["enhanced-folder-monitoring"])

# WebSocket connection manager
class ConnectionManager:
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
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Request models
class AddFolderRequest(BaseModel):
    folder_path: str
    auto_start_monitoring: bool = True

class ProcessFileRequest(BaseModel):
    file_path: str

# Mock enhanced monitoring status
def get_mock_enhanced_status() -> Dict[str, Any]:
    """Get mock enhanced monitoring status for testing"""
    return {
        "is_running": True,
        "total_files_tracked": 5,
        "files_in_processing": 1,
        "files_completed": 3,
        "files_failed_verification": 1,
        "processing_queue_size": 2,
        "active_processors": 1,
        "max_concurrent_processors": 3,
        "average_processing_time_seconds": 12.5,
        "success_rate_percentage": 75.0,
        "pipeline_stages": [
            "file_validation",
            "processor_selection", 
            "content_extraction",
            "text_chunking",
            "embedding_generation",
            "vector_storage",
            "metadata_storage"
        ],
        "recent_files": [
            {
                "file_path": "/test/document1.txt",
                "file_name": "document1.txt",
                "status": "completed",
                "size_mb": 0.5,
                "processing_time": 10.2
            },
            {
                "file_path": "/test/document2.pdf",
                "file_name": "document2.pdf", 
                "status": "processing",
                "size_mb": 2.1,
                "current_stage": "embedding_generation"
            }
        ]
    }

# Mock file processing states
def get_mock_file_states() -> Dict[str, Dict[str, Any]]:
    """Get mock file processing states"""
    return {
        "/test/document1.txt": {
            "file_path": "/test/document1.txt",
            "file_name": "document1.txt",
            "folder_path": "/test",
            "size_mb": 0.5,
            "status": "completed",
            "current_stage": "metadata_storage",
            "pipeline_progress": {
                "file_validation": "completed",
                "processor_selection": "completed",
                "content_extraction": "completed", 
                "text_chunking": "completed",
                "embedding_generation": "completed",
                "vector_storage": "completed",
                "metadata_storage": "completed"
            },
            "processing_start_time": "2025-06-23T13:45:00",
            "processing_end_time": "2025-06-23T13:45:10",
            "total_duration_seconds": 10.2,
            "error_message": None,
            "metrics": {
                "chunks_created": 5,
                "vectors_stored": 5,
                "processing_time": 10.2
            }
        },
        "/test/document2.pdf": {
            "file_path": "/test/document2.pdf",
            "file_name": "document2.pdf",
            "folder_path": "/test",
            "size_mb": 2.1,
            "status": "processing",
            "current_stage": "embedding_generation",
            "pipeline_progress": {
                "file_validation": "completed",
                "processor_selection": "completed",
                "content_extraction": "completed",
                "text_chunking": "completed", 
                "embedding_generation": "running",
                "vector_storage": "pending",
                "metadata_storage": "pending"
            },
            "processing_start_time": "2025-06-23T13:48:00",
            "processing_end_time": None,
            "total_duration_seconds": None,
            "error_message": None,
            "metrics": {}
        }
    }

# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        # Send initial status
        initial_status = {
            "type": "status_update",
            "timestamp": datetime.now().isoformat(),
            "data": get_mock_enhanced_status()
        }
        await websocket.send_text(json.dumps(initial_status))
        
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            
            # Echo back for testing
            echo_message = {
                "type": "echo",
                "timestamp": datetime.now().isoformat(),
                "data": {"message": f"Echo: {data}"}
            }
            await websocket.send_text(json.dumps(echo_message))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Get enhanced monitoring status
@router.get("/status")
async def get_enhanced_status():
    """Get comprehensive monitoring status with pipeline details"""
    try:
        status = get_mock_enhanced_status()
        return {
            "status": "success",
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

# Get file processing states
@router.get("/files")
async def get_file_states():
    """Get all file processing states"""
    try:
        file_states = get_mock_file_states()
        return {
            "status": "success",
            "data": file_states,
            "count": len(file_states),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file states: {str(e)}")

# Add folder for monitoring
@router.post("/add-folder")
async def add_folder(request: AddFolderRequest):
    """Add folder for enhanced monitoring"""
    try:
        folder_path = request.folder_path
        
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail="Folder does not exist")
        
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        # Mock response for adding folder
        return {
            "status": "success",
            "message": f"Folder added for enhanced monitoring: {folder_path}",
            "folder_path": folder_path,
            "auto_start_monitoring": request.auto_start_monitoring,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add folder: {str(e)}")

# Process specific file
@router.post("/process-file")
async def process_file(request: ProcessFileRequest):
    """Process a specific file with enhanced verification"""
    try:
        file_path = request.file_path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="File does not exist")
        
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Mock processing response
        return {
            "status": "success",
            "message": f"File queued for processing: {os.path.basename(file_path)}",
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "queue_position": 1,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

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
                padding: 20px;
            }
            
            .dashboard-container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #fff, #e0e0e0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            
            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .status-card {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                padding: 20px;
                border-left: 4px solid #4CAF50;
                backdrop-filter: blur(10px);
            }
            
            .status-card h3 {
                font-size: 1.1em;
                margin-bottom: 10px;
                opacity: 0.8;
            }
            
            .status-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .pipeline-section {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 20px;
                backdrop-filter: blur(10px);
            }
            
            .pipeline-title {
                font-size: 1.4em;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .pipeline-stages {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .pipeline-stage {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                min-width: 120px;
                transition: all 0.3s ease;
            }
            
            .pipeline-stage.completed {
                background: rgba(76, 175, 80, 0.3);
                border: 2px solid #4CAF50;
            }
            
            .pipeline-stage.running {
                background: rgba(255, 152, 0, 0.3);
                border: 2px solid #FF9800;
                animation: pulse 2s infinite;
            }
            
            .pipeline-stage.failed {
                background: rgba(244, 67, 54, 0.3);
                border: 2px solid #f44336;
            }
            
            .pipeline-stage.pending {
                background: rgba(158, 158, 158, 0.3);
                border: 2px solid #9e9e9e;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .stage-icon {
                font-size: 2em;
                margin-bottom: 8px;
            }
            
            .stage-name {
                font-size: 0.9em;
                text-align: center;
                font-weight: 500;
            }
            
            .connection-status {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: bold;
            }
            
            .connection-status.connected {
                background: rgba(76, 175, 80, 0.9);
                color: white;
            }
            
            .connection-status.disconnected {
                background: rgba(244, 67, 54, 0.9);
                color: white;
            }
            
            .files-section {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                padding: 25px;
                backdrop-filter: blur(10px);
            }
            
            .files-title {
                font-size: 1.4em;
                margin-bottom: 20px;
            }
            
            .file-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-bottom: 10px;
            }
            
            .file-info {
                display: flex;
                flex-direction: column;
            }
            
            .file-name {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .file-status {
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            .refresh-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin: 10px;
                transition: background 0.3s ease;
            }
            
            .refresh-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="header">
                <h1>🚀 Enhanced Folder Monitoring</h1>
                <p>Real-time document processing pipeline with verification</p>
            </div>
            
            <div class="connection-status" id="connectionStatus">
                🔌 Connecting...
            </div>
            
            <div class="status-grid" id="statusGrid">
                <div class="status-card">
                    <h3>Files Tracked</h3>
                    <div class="status-value" id="filesTracked">0</div>
                </div>
                <div class="status-card">
                    <h3>Processing</h3>
                    <div class="status-value" id="filesProcessing">0</div>
                </div>
                <div class="status-card">
                    <h3>Completed</h3>
                    <div class="status-value" id="filesCompleted">0</div>
                </div>
                <div class="status-card">
                    <h3>Success Rate</h3>
                    <div class="status-value" id="successRate">0%</div>
                </div>
            </div>
            
            <div class="pipeline-section">
                <div class="pipeline-title">📋 Document Processing Pipeline</div>
                <div class="pipeline-stages" id="pipelineStages">
                    <div class="pipeline-stage pending" data-stage="file_validation">
                        <div class="stage-icon">📁</div>
                        <div class="stage-name">File Validation</div>
                    </div>
                    <div class="pipeline-stage pending" data-stage="processor_selection">
                        <div class="stage-icon">⚙️</div>
                        <div class="stage-name">Processor Selection</div>
                    </div>
                    <div class="pipeline-stage pending" data-stage="content_extraction">
                        <div class="stage-icon">📄</div>
                        <div class="stage-name">Content Extraction</div>
                    </div>
                    <div class="pipeline-stage pending" data-stage="text_chunking">
                        <div class="stage-icon">✂️</div>
                        <div class="stage-name">Text Chunking</div>
                    </div>
                    <div class="pipeline-stage pending" data-stage="embedding_generation">
                        <div class="stage-icon">🧮</div>
                        <div class="stage-name">Embedding Generation</div>
                    </div>
                    <div class="pipeline-stage pending" data-stage="vector_storage">
                        <div class="stage-icon">💾</div>
                        <div class="stage-name">Vector Storage</div>
                    </div>
                    <div class="pipeline-stage pending" data-stage="metadata_storage">
                        <div class="stage-icon">🏷️</div>
                        <div class="stage-name">Metadata Storage</div>
                    </div>
                </div>
            </div>
            
            <div class="files-section">
                <div class="files-title">📄 Recent Files</div>
                <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
                <div id="filesList">
                    <!-- Files will be populated by JavaScript -->
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let reconnectInterval = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/enhanced-folder/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('WebSocket connected');
                    updateConnectionStatus(true);
                    if (reconnectInterval) {
                        clearInterval(reconnectInterval);
                        reconnectInterval = null;
                    }
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = function() {
                    console.log('WebSocket disconnected');
                    updateConnectionStatus(false);
                    // Try to reconnect every 5 seconds
                    if (!reconnectInterval) {
                        reconnectInterval = setInterval(connectWebSocket, 5000);
                    }
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
                
                if (data.type === 'status_update') {
                    updateDashboard(data.data);
                } else if (data.type === 'file_processing_started') {
                    // Handle file processing events
                } else if (data.type === 'pipeline_stage_started') {
                    updatePipelineStage(data.data.stage, 'running');
                } else if (data.type === 'pipeline_stage_completed') {
                    updatePipelineStage(data.data.stage, 'completed');
                }
            }
            
            function updateDashboard(status) {
                document.getElementById('filesTracked').textContent = status.total_files_tracked || 0;
                document.getElementById('filesProcessing').textContent = status.files_in_processing || 0;
                document.getElementById('filesCompleted').textContent = status.files_completed || 0;
                document.getElementById('successRate').textContent = (status.success_rate_percentage || 0) + '%';
                
                // Update recent files
                if (status.recent_files) {
                    updateFilesList(status.recent_files);
                }
            }
            
            function updatePipelineStage(stage, status) {
                const stageElement = document.querySelector(`[data-stage="${stage}"]`);
                if (stageElement) {
                    stageElement.className = `pipeline-stage ${status}`;
                }
            }
            
            function updateFilesList(files) {
                const filesListElement = document.getElementById('filesList');
                filesListElement.innerHTML = '';
                
                files.forEach(file => {
                    const fileElement = document.createElement('div');
                    fileElement.className = 'file-item';
                    fileElement.innerHTML = `
                        <div class="file-info">
                            <div class="file-name">${file.file_name}</div>
                            <div class="file-status">Status: ${file.status} | Size: ${file.size_mb}MB</div>
                        </div>
                        <div class="file-status">${file.current_stage || 'Ready'}</div>
                    `;
                    filesListElement.appendChild(fileElement);
                });
            }
            
            function refreshData() {
                fetch('/api/enhanced-folder/status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            updateDashboard(data.data);
                        }
                    })
                    .catch(error => console.error('Error refreshing data:', error));
            }
            
            // Initialize
            connectWebSocket();
            refreshData();
            
            // Refresh data every 30 seconds
            setInterval(refreshData, 30000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=dashboard_html)

# Test endpoint
@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify the router is working"""
    return {
        "status": "success",
        "message": "Enhanced folder monitoring API is working!",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/enhanced-folder/status",
            "/api/enhanced-folder/dashboard", 
            "/api/enhanced-folder/files",
            "/api/enhanced-folder/add-folder",
            "/api/enhanced-folder/process-file",
            "/api/enhanced-folder/ws"
        ]
    } 