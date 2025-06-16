# Comprehensive Heartbeat Monitoring System

## File: heartbeat_monitor.py
```python
import asyncio
import logging
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import threading
from contextlib import contextmanager

# Import system components
from config import config
from storage import json_store, vector_store
from embedder import embedder
from llm_client import llm_client
from servicenow_client import servicenow_client
from scheduler_service import scheduler_service

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class ComponentHealth:
    """Individual component health status"""
    name: str
    status: HealthStatus
    response_time_ms: float
    last_check: str
    details: Dict[str, Any]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        return result

@dataclass
class SystemHealth:
    """Overall system health"""
    overall_status: HealthStatus
    timestamp: str
    uptime_seconds: int
    components: List[ComponentHealth]
    performance_metrics: Dict[str, Any]
    alerts: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['overall_status'] = self.overall_status.value
        result['components'] = [comp.to_dict() for comp in self.components]
        return result

class HeartbeatMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        self.check_interval = 30  # seconds
        self.is_running = False
        self.last_health_check = None
        self.health_history = []
        self.max_history = 100
        
        # Performance thresholds
        self.thresholds = {
            'api_response_time_ms': 5000,  # 5 seconds
            'memory_usage_percent': 85,
            'cpu_usage_percent': 80,
            'disk_usage_percent': 90,
            'vector_search_time_ms': 1000,
            'embedding_time_ms': 3000,
            'llm_response_time_ms': 10000
        }
        
        self.logger.info("Heartbeat monitor initialized")
    
    async def comprehensive_health_check(self) -> SystemHealth:
        """Perform comprehensive system health check"""
        start_time = time.time()
        components = []
        alerts = []
        
        self.logger.info("🔍 Starting comprehensive health check...")
        
        # Check all components
        components.append(await self._check_api_server())
        components.append(await self._check_storage_layer())
        components.append(await self._check_vector_store())
        components.append(await self._check_embeddings())
        components.append(await self._check_llm_service())
        components.append(await self._check_servicenow())
        components.append(await self._check_scheduler())
        components.append(await self._check_system_resources())
        components.append(await self._check_external_dependencies())
        
        # Calculate overall status
        critical_components = [c for c in components if c.status == HealthStatus.CRITICAL]
        warning_components = [c for c in components if c.status == HealthStatus.WARNING]
        
        if critical_components:
            overall_status = HealthStatus.CRITICAL
            alerts.append(f"Critical issues detected in: {', '.join([c.name for c in critical_components])}")
        elif warning_components:
            overall_status = HealthStatus.WARNING
            alerts.append(f"Warnings detected in: {', '.join([c.name for c in warning_components])}")
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Get performance metrics
        performance_metrics = await self._get_performance_metrics()
        
        # Check performance thresholds
        for metric, threshold in self.thresholds.items():
            if metric in performance_metrics and performance_metrics[metric] > threshold:
                alerts.append(f"Performance threshold exceeded: {metric} = {performance_metrics[metric]} > {threshold}")
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
        
        # Create system health object
        system_health = SystemHealth(
            overall_status=overall_status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=int(time.time() - self.start_time),
            components=components,
            performance_metrics=performance_metrics,
            alerts=alerts
        )
        
        # Store health check result
        self.last_health_check = system_health
        self._store_health_history(system_health)
        
        check_duration = (time.time() - start_time) * 1000
        self.logger.info(f"✅ Health check completed in {check_duration:.0f}ms - Status: {overall_status.value}")
        
        return system_health
    
    async def _check_api_server(self) -> ComponentHealth:
        """Check FastAPI server health"""
        start_time = time.time()
        
        try:
            # Test basic endpoint
            response = requests.get(f"http://{config.api_host}:{config.api_port}/health", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                details = {
                    "status_code": response.status_code,
                    "response_data": response.json(),
                    "server_host": config.api_host,
                    "server_port": config.api_port
                }
                error_msg = None
            else:
                status = HealthStatus.WARNING
                details = {"status_code": response.status_code}
                error_msg = f"Unexpected status code: {response.status_code}"
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.CRITICAL
            details = {"error_type": type(e).__name__}
            error_msg = str(e)
        
        return ComponentHealth(
            name="API Server",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_storage_layer(self) -> ComponentHealth:
        """Check JSON storage and file system"""
        start_time = time.time()
        
        try:
            # Test read/write operations
            test_data = {"health_check": datetime.now().isoformat()}
            json_store.save("health_check_test.json", test_data)
            loaded_data = json_store.load("health_check_test.json")
            
            # Check data directories exist and are writable
            data_path = Path(config.data_dir)
            required_dirs = ["metadata", "vectors", "uploads", "logs"]
            missing_dirs = [d for d in required_dirs if not (data_path / d).exists()]
            
            if loaded_data.get("health_check") == test_data["health_check"] and not missing_dirs:
                status = HealthStatus.HEALTHY
                error_msg = None
            else:
                status = HealthStatus.WARNING
                error_msg = f"Missing directories: {missing_dirs}" if missing_dirs else "Data verification failed"
            
            # Get storage statistics
            disk_usage = psutil.disk_usage(str(data_path))
            details = {
                "data_directory": str(data_path),
                "directories_status": {d: (data_path / d).exists() for d in required_dirs},
                "disk_total_gb": round(disk_usage.total / (1024**3), 2),
                "disk_used_gb": round(disk_usage.used / (1024**3), 2),
                "disk_free_gb": round(disk_usage.free / (1024**3), 2),
                "disk_usage_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
            }
            
            # Clean up test file
            try:
                (data_path / "health_check_test.json").unlink(missing_ok=True)
            except:
                pass
                
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {"error_type": type(e).__name__}
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="Storage Layer",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_vector_store(self) -> ComponentHealth:
        """Check FAISS vector store"""
        start_time = time.time()
        
        try:
            # Get vector store statistics
            stats = vector_store.get_stats()
            
            # Test vector search if vectors exist
            if stats['vector_count'] > 0:
                # Create dummy query vector
                dummy_vector = [0.1] * config.faiss.dimension
                search_start = time.time()
                vector_ids, scores = vector_store.search(dummy_vector, k=min(5, stats['vector_count']))
                search_time = (time.time() - search_start) * 1000
                
                search_successful = len(vector_ids) > 0
            else:
                search_time = 0
                search_successful = True  # No vectors to search
            
            if search_successful and stats.get('ntotal', 0) == stats.get('vector_count', 0):
                status = HealthStatus.HEALTHY
                error_msg = None
            else:
                status = HealthStatus.WARNING
                error_msg = "Vector search failed or index inconsistency"
            
            details = {
                **stats,
                "search_test_time_ms": search_time,
                "search_successful": search_successful,
                "index_file_exists": vector_store.index_file.exists(),
                "metadata_file_exists": vector_store.metadata_file.exists()
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {"error_type": type(e).__name__}
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="Vector Store (FAISS)",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_embeddings(self) -> ComponentHealth:
        """Check Cohere embedding service"""
        start_time = time.time()
        
        try:
            # Test embedding generation
            test_text = "Health check test for embedding service"
            embedding = embedder.embed(test_text)
            
            # Verify embedding properties
            expected_dim = config.embedding.dimension
            actual_dim = len(embedding)
            
            if actual_dim == expected_dim and all(isinstance(x, (int, float)) for x in embedding):
                status = HealthStatus.HEALTHY
                error_msg = None
            else:
                status = HealthStatus.CRITICAL
                error_msg = f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}"
            
            details = {
                "provider": config.embedding.provider,
                "model": config.embedding.model,
                "expected_dimension": expected_dim,
                "actual_dimension": actual_dim,
                "test_embedding_sample": embedding[:5] if len(embedding) >= 5 else embedding,
                "embedding_successful": len(embedding) > 0
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {
                "provider": config.embedding.provider,
                "model": config.embedding.model,
                "error_type": type(e).__name__
            }
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="Embedding Service (Cohere)",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_llm_service(self) -> ComponentHealth:
        """Check Llama-4 Maverick LLM service"""
        start_time = time.time()
        
        try:
            # Test LLM generation
            test_prompt = "Respond with exactly: 'Health check successful'"
            response = llm_client.generate(test_prompt, max_tokens=10, temperature=0.0)
            
            # Verify response
            response_valid = len(response) > 0 and "health check" in response.lower()
            
            if response_valid:
                status = HealthStatus.HEALTHY
                error_msg = None
            else:
                status = HealthStatus.WARNING
                error_msg = f"Unexpected LLM response: {response[:100]}"
            
            details = {
                "provider": config.llm.provider,
                "model": config.llm.model,
                "max_tokens": config.llm.max_tokens,
                "temperature": config.llm.temperature,
                "test_response": response[:100],
                "response_length": len(response),
                "response_valid": response_valid
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {
                "provider": config.llm.provider,
                "model": config.llm.model,
                "error_type": type(e).__name__
            }
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="LLM Service (Llama-4 Maverick)",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_servicenow(self) -> ComponentHealth:
        """Check ServiceNow integration"""
        start_time = time.time()
        
        try:
            if not servicenow_client.enabled:
                status = HealthStatus.WARNING
                error_msg = "ServiceNow integration not configured"
                details = {
                    "enabled": False,
                    "base_url": "Not configured",
                    "last_sync": "Never"
                }
            else:
                # Test connection
                connection_test = servicenow_client.test_connection()
                
                # Get sync status
                sync_log = json_store.load('logs/servicenow_sync.json', {})
                last_sync = sync_log.get('last_sync')
                last_status = sync_log.get('last_status', 'unknown')
                
                # Check if sync is recent (within last 24 hours)
                sync_recent = False
                if last_sync:
                    try:
                        last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                        sync_recent = (datetime.now() - last_sync_dt) < timedelta(hours=24)
                    except:
                        pass
                
                if connection_test and (sync_recent or last_status == 'success'):
                    status = HealthStatus.HEALTHY
                    error_msg = None
                elif connection_test:
                    status = HealthStatus.WARNING
                    error_msg = "Connection OK but sync issues detected"
                else:
                    status = HealthStatus.CRITICAL
                    error_msg = "ServiceNow connection failed"
                
                # Get ticket count
                tickets_data = json_store.load('metadata/servicenow_tickets.json', {})
                ticket_count = len(tickets_data.get('tickets', {}))
                
                details = {
                    "enabled": True,
                    "base_url": servicenow_client.base_url,
                    "connection_test": connection_test,
                    "last_sync": last_sync or "Never",
                    "last_sync_status": last_status,
                    "sync_recent": sync_recent,
                    "total_tickets": ticket_count,
                    "table": servicenow_client.table
                }
                
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {"error_type": type(e).__name__}
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="ServiceNow Integration",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_scheduler(self) -> ComponentHealth:
        """Check background scheduler service"""
        start_time = time.time()
        
        try:
            scheduler_status = scheduler_service.get_status()
            
            is_running = scheduler_status.get('scheduler_running', False)
            active_jobs = scheduler_status.get('active_jobs', [])
            
            if is_running and len(active_jobs) > 0:
                status = HealthStatus.HEALTHY
                error_msg = None
            elif is_running:
                status = HealthStatus.WARNING
                error_msg = "Scheduler running but no active jobs"
            else:
                status = HealthStatus.CRITICAL
                error_msg = "Scheduler not running"
            
            details = {
                "running": is_running,
                "active_jobs_count": len(active_jobs),
                "active_jobs": active_jobs,
                "last_file_sync": scheduler_status.get('last_file_sync'),
                "last_servicenow_sync": scheduler_status.get('last_servicenow_sync')
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {"error_type": type(e).__name__}
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="Background Scheduler",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_system_resources(self) -> ComponentHealth:
        """Check system resources (CPU, Memory, Disk)"""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            warnings = []
            if cpu_percent > self.thresholds['cpu_usage_percent']:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > self.thresholds['memory_usage_percent']:
                warnings.append(f"High memory usage: {memory.percent}%")
            if disk.percent > self.thresholds['disk_usage_percent']:
                warnings.append(f"High disk usage: {disk.percent}%")
            
            if warnings:
                status = HealthStatus.WARNING
                error_msg = "; ".join(warnings)
            else:
                status = HealthStatus.HEALTHY
                error_msg = None
            
            details = {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": round(disk.percent, 1),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "cpu_count": psutil.cpu_count(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {"error_type": type(e).__name__}
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="System Resources",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _check_external_dependencies(self) -> ComponentHealth:
        """Check external API dependencies"""
        start_time = time.time()
        
        try:
            dependencies = []
            
            # Check Groq API
            try:
                groq_test = llm_client.test_connection()
                dependencies.append({"name": "Groq API", "status": "healthy" if groq_test else "failed"})
            except Exception as e:
                dependencies.append({"name": "Groq API", "status": "error", "error": str(e)})
            
            # Check Cohere API
            try:
                cohere_test = embedder.embed("test")
                cohere_ok = len(cohere_test) == config.embedding.dimension
                dependencies.append({"name": "Cohere API", "status": "healthy" if cohere_ok else "failed"})
            except Exception as e:
                dependencies.append({"name": "Cohere API", "status": "error", "error": str(e)})
            
            # Overall status
            failed_deps = [d for d in dependencies if d["status"] != "healthy"]
            
            if not failed_deps:
                status = HealthStatus.HEALTHY
                error_msg = None
            else:
                status = HealthStatus.CRITICAL
                error_msg = f"Failed dependencies: {', '.join([d['name'] for d in failed_deps])}"
            
            details = {
                "dependencies": dependencies,
                "total_dependencies": len(dependencies),
                "healthy_dependencies": len([d for d in dependencies if d["status"] == "healthy"]),
                "failed_dependencies": len(failed_deps)
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            details = {"error_type": type(e).__name__}
            error_msg = str(e)
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            name="External Dependencies",
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now().isoformat(),
            details=details,
            error_message=error_msg
        )
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # RAG system metrics
            files_data = json_store.load('metadata/files.json', {})
            chunks_data = json_store.load('metadata/chunks.json', {})
            tickets_data = json_store.load('metadata/servicenow_tickets.json', {})
            
            # Performance metrics
            metrics = {
                "system_cpu_percent": round(cpu_percent, 1),
                "system_memory_percent": round(memory.percent, 1),
                "system_disk_percent": round(disk.percent, 1),
                "total_files": len(files_data.get('files', {})),
                "total_chunks": len(chunks_data.get('chunks', {})),
                "total_tickets": len(tickets_data.get('tickets', {})),
                "total_vectors": vector_store.vector_count,
                "uptime_seconds": int(time.time() - self.start_time),
                "uptime_hours": round((time.time() - self.start_time) / 3600, 1)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}
    
    def _store_health_history(self, health: SystemHealth):
        """Store health check in history"""
        self.health_history.append(health.to_dict())
        
        # Keep only recent history
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
        
        # Save to file
        try:
            json_store.save('logs/health_history.json', {
                'history': self.health_history,
                'last_updated': datetime.now().isoformat()
            })
        except Exception as e:
            self.logger.error(f"Failed to save health history: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary"""
        if not self.last_health_check:
            return {"status": "unknown", "message": "No health check performed yet"}
        
        return {
            "overall_status": self.last_health_check.overall_status.value,
            "timestamp": self.last_health_check.timestamp,
            "uptime_hours": round((time.time() - self.start_time) / 3600, 1),
            "component_count": len(self.last_health_check.components),
            "healthy_components": len([c for c in self.last_health_check.components if c.status == HealthStatus.HEALTHY]),
            "warning_components": len([c for c in self.last_health_check.components if c.status == HealthStatus.WARNING]),
            "critical_components": len([c for c in self.last_health_check.components if c.status == HealthStatus.CRITICAL]),
            "alerts": self.last_health_check.alerts
        }
    
    def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("🚀 Starting continuous health monitoring...")
        
        def monitor_loop():
            while self.is_running:
                try:
                    # Run health check
                    health = asyncio.run(self.comprehensive_health_check())
                    
                    # Log status
                    if health.overall_status == HealthStatus.CRITICAL:
                        self.logger.error(f"🚨 CRITICAL system health issues detected")
                    elif health.overall_status == HealthStatus.WARNING:
                        self.logger.warning(f"⚠️ System health warnings detected")
                    else:
                        self.logger.info(f"✅ System health check passed")
                    
                    # Wait for next check
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Health monitoring error: {e}")
                    time.sleep(self.check_interval)
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.is_running = False
        self.logger.info("🛑 Stopping health monitoring...")

# Global instance
heartbeat_monitor = HeartbeatMonitor()
```

## Enhanced API Endpoints for Health Monitoring

### File: health_api.py (Add to enhanced_api.py)
```python
# Add these endpoints to your FastAPI app

@app.get("/heartbeat", dependencies=[Depends(verify_api_key)])
async def get_heartbeat():
    """Get comprehensive system heartbeat"""
    try:
        health = await heartbeat_monitor.comprehensive_health_check()
        return health.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/summary")
async def get_health_summary():
    """Get health summary (no auth required for monitoring tools)"""
    try:
        summary = heartbeat_monitor.get_health_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/components", dependencies=[Depends(verify_api_key)])
async def get_component_health():
    """Get detailed component health status"""
    try:
        if not heartbeat_monitor.last_health_check:
            health = await heartbeat_monitor.comprehensive_health_check()
        else:
            health = heartbeat_monitor.last_health_check
        
        return {
            "components": [comp.to_dict() for comp in health.components],
            "timestamp": health.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/history", dependencies=[Depends(verify_api_key)])
async def get_health_history(limit: int = 24):
    """Get health check history"""
    try:
        history_data = json_store.load('logs/health_history.json', {})
        history = history_data.get('history', [])
        
        # Return recent history
        recent_history = history[-limit:] if len(history) > limit else history
        
        return {
            "history": recent_history,
            "total_checks": len(history),
            "returned_checks": len(recent_history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/health/check", dependencies=[Depends(verify_api_key)])
async def trigger_health_check():
    """Manually trigger health check"""
    try:
        health = await heartbeat_monitor.comprehensive_health_check()
        return {
            "message": "Health check completed",
            "overall_status": health.overall_status.value,
            "timestamp": health.timestamp,
            "component_count": len(health.components)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/servicenow", dependencies=[Depends(verify_api_key)])
async def get_servicenow_health():
    """Get detailed ServiceNow health and sync status"""
    try:
        # Get ServiceNow component health
        servicenow_health = await heartbeat_monitor._check_servicenow()
        
        # Get additional ServiceNow metrics
        sync_log = json_store.load('logs/servicenow_sync.json', {})
        tickets_data = json_store.load('metadata/servicenow_tickets.json', {})
        
        # Calculate sync statistics
        tickets = tickets_data.get('tickets', {})
        ticket_stats = {}
        
        if tickets:
            # Group by status
            from collections import defaultdict
            status_counts = defaultdict(int)
            priority_counts = defaultdict(int)
            category_counts = defaultdict(int)
            
            for ticket in tickets.values():
                status_counts[ticket.get('state', 'unknown')] += 1
                priority_counts[ticket.get('priority', 'unknown')] += 1
                category_counts[ticket.get('category', 'unknown')] += 1
            
            ticket_stats = {
                'total_tickets': len(tickets),
                'by_status': dict(status_counts),
                'by_priority': dict(priority_counts),
                'by_category': dict(category_counts)
            }
        
        return {
            "component_health": servicenow_health.to_dict(),
            "sync_history": sync_log,
            "ticket_statistics": ticket_stats,
            "last_sync_details": {
                "last_sync": sync_log.get('last_sync'),
                "tickets_processed": sync_log.get('tickets_processed', 0),
                "errors": sync_log.get('errors', 0),
                "status": sync_log.get('last_status', 'unknown')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/performance", dependencies=[Depends(verify_api_key)])
async def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        # Get current performance metrics
        metrics = await heartbeat_monitor._get_performance_metrics()
        
        # Add query performance if available
        query_log = json_store.load('logs/query_log.json', {})
        recent_queries = query_log.get('recent_queries', [])
        
        if recent_queries:
            response_times = [q.get('response_time_ms', 0) for q in recent_queries[-100:]]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            
            metrics.update({
                'query_performance': {
                    'recent_query_count': len(recent_queries),
                    'avg_response_time_ms': round(avg_response_time, 2),
                    'max_response_time_ms': max_response_time,
                    'min_response_time_ms': min_response_time
                }
            })
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Health Check CLI Tool

### File: health_check_cli.py
```python
#!/usr/bin/env python3
"""
Command-line health check utility for RAG system
Usage: python health_check_cli.py [options]
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any
import requests
from tabulate import tabulate
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class HealthCheckCLI:
    """Command-line interface for health checking"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        colors = {
            'healthy': Fore.GREEN,
            'warning': Fore.YELLOW,
            'critical': Fore.RED,
            'unknown': Fore.MAGENTA
        }
        return colors.get(status.lower(), Fore.WHITE)
    
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in human readable format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
    def check_basic_health(self) -> Dict[str, Any]:
        """Check basic system health"""
        try:
            response = requests.get(f"{self.base_url}/health/summary", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def check_comprehensive_health(self) -> Dict[str, Any]:
        """Check comprehensive system health"""
        try:
            response = requests.get(
                f"{self.base_url}/heartbeat", 
                headers=self.headers, 
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def check_component_health(self) -> Dict[str, Any]:
        """Check individual component health"""
        try:
            response = requests.get(
                f"{self.base_url}/health/components", 
                headers=self.headers, 
                timeout=20
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def check_servicenow_health(self) -> Dict[str, Any]:
        """Check ServiceNow integration health"""
        try:
            response = requests.get(
                f"{self.base_url}/health/servicenow", 
                headers=self.headers, 
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            response = requests.get(
                f"{self.base_url}/health/performance", 
                headers=self.headers, 
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def display_basic_health(self):
        """Display basic health check results"""
        print(f"\n{Fore.CYAN}🔍 RAG SYSTEM - BASIC HEALTH CHECK{Style.RESET_ALL}")
        print("=" * 50)
        
        health = self.check_basic_health()
        
        if "error" in health:
            print(f"{Fore.RED}❌ Health check failed: {health['error']}{Style.RESET_ALL}")
            return False
        
        status = health.get('overall_status', 'unknown')
        status_color = self._get_status_color(status)
        
        print(f"Overall Status: {status_color}{status.upper()}{Style.RESET_ALL}")
        print(f"Uptime: {self._format_uptime(health.get('uptime_seconds', 0))}")
        print(f"Last Check: {health.get('timestamp', 'unknown')}")
        
        # Component summary
        if 'component_count' in health:
            print(f"\nComponent Summary:")
            print(f"  {Fore.GREEN}✅ Healthy: {health.get('healthy_components', 0)}{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}⚠️  Warning: {health.get('warning_components', 0)}{Style.RESET_ALL}")
            print(f"  {Fore.RED}🚨 Critical: {health.get('critical_components', 0)}{Style.RESET_ALL}")
        
        # Alerts
        alerts = health.get('alerts', [])
        if alerts:
            print(f"\n{Fore.YELLOW}⚠️ ALERTS:{Style.RESET_ALL}")
            for alert in alerts:
                print(f"  • {alert}")
        
        return status == 'healthy'
    
    def display_comprehensive_health(self):
        """Display comprehensive health check results"""
        print(f"\n{Fore.CYAN}🔍 RAG SYSTEM - COMPREHENSIVE HEALTH CHECK{Style.RESET_ALL}")
        print("=" * 60)
        
        health = self.check_comprehensive_health()
        
        if "error" in health:
            print(f"{Fore.RED}❌ Health check failed: {health['error']}{Style.RESET_ALL}")
            return False
        
        # Overall status
        status = health.get('overall_status', 'unknown')
        status_color = self._get_status_color(status)
        print(f"Overall Status: {status_color}{status.upper()}{Style.RESET_ALL}")
        print(f"Timestamp: {health.get('timestamp', 'unknown')}")
        print(f"Uptime: {self._format_uptime(health.get('uptime_seconds', 0))}")
        
        # Component details
        components = health.get('components', [])
        if components:
            print(f"\n{Fore.CYAN}📋 COMPONENT HEALTH:{Style.RESET_ALL}")
            
            table_data = []
            for comp in components:
                comp_status = comp.get('status', 'unknown')
                comp_color = self._get_status_color(comp_status)
                
                table_data.append([
                    comp.get('name', 'Unknown'),
                    f"{comp_color}{comp_status.upper()}{Style.RESET_ALL}",
                    f"{comp.get('response_time_ms', 0):.0f}ms",
                    comp.get('error_message', 'None')[:50]
                ])
            
            print(tabulate(
                table_data,
                headers=['Component', 'Status', 'Response Time', 'Error'],
                tablefmt='grid'
            ))
        
        # Performance metrics
        perf_metrics = health.get('performance_metrics', {})
        if perf_metrics:
            print(f"\n{Fore.CYAN}📊 PERFORMANCE METRICS:{Style.RESET_ALL}")
            
            perf_data = [
                ['CPU Usage', f"{perf_metrics.get('system_cpu_percent', 0)}%"],
                ['Memory Usage', f"{perf_metrics.get('system_memory_percent', 0)}%"],
                ['Disk Usage', f"{perf_metrics.get('system_disk_percent', 0)}%"],
                ['Total Files', perf_metrics.get('total_files', 0)],
                ['Total Chunks', perf_metrics.get('total_chunks', 0)],
                ['Total Vectors', perf_metrics.get('total_vectors', 0)],
                ['Total Tickets', perf_metrics.get('total_tickets', 0)]
            ]
            
            print(tabulate(
                perf_data,
                headers=['Metric', 'Value'],
                tablefmt='simple'
            ))
        
        # Alerts
        alerts = health.get('alerts', [])
        if alerts:
            print(f"\n{Fore.YELLOW}⚠️ SYSTEM ALERTS:{Style.RESET_ALL}")
            for i, alert in enumerate(alerts, 1):
                print(f"  {i}. {alert}")
        
        return status == 'healthy'
    
    def display_component_details(self):
        """Display detailed component information"""
        print(f"\n{Fore.CYAN}🔧 RAG SYSTEM - COMPONENT DETAILS{Style.RESET_ALL}")
        print("=" * 60)
        
        comp_health = self.check_component_health()
        
        if "error" in comp_health:
            print(f"{Fore.RED}❌ Component check failed: {comp_health['error']}{Style.RESET_ALL}")
            return False
        
        components = comp_health.get('components', [])
        
        for comp in components:
            name = comp.get('name', 'Unknown')
            status = comp.get('status', 'unknown')
            status_color = self._get_status_color(status)
            
            print(f"\n{Fore.BLUE}🔹 {name}{Style.RESET_ALL}")
            print(f"   Status: {status_color}{status.upper()}{Style.RESET_ALL}")
            print(f"   Response Time: {comp.get('response_time_ms', 0):.0f}ms")
            print(f"   Last Check: {comp.get('last_check', 'unknown')}")
            
            if comp.get('error_message'):
                print(f"   {Fore.RED}Error: {comp['error_message']}{Style.RESET_ALL}")
            
            # Display key details
            details = comp.get('details', {})
            if details:
                print(f"   Details:")
                for key, value in list(details.items())[:5]:  # Show first 5 details
                    if isinstance(value, (dict, list)):
                        print(f"     {key}: {type(value).__name__} with {len(value)} items")
                    else:
                        print(f"     {key}: {value}")
        
        return True
    
    def display_servicenow_details(self):
        """Display ServiceNow integration details"""
        print(f"\n{Fore.CYAN}🏢 SERVICENOW INTEGRATION HEALTH{Style.RESET_ALL}")
        print("=" * 50)
        
        sn_health = self.check_servicenow_health()
        
        if "error" in sn_health:
            print(f"{Fore.RED}❌ ServiceNow check failed: {sn_health['error']}{Style.RESET_ALL}")
            return False
        
        # Component health
        comp_health = sn_health.get('component_health', {})
        status = comp_health.get('status', 'unknown')
        status_color = self._get_status_color(status)
        
        print(f"Integration Status: {status_color}{status.upper()}{Style.RESET_ALL}")
        print(f"Response Time: {comp_health.get('response_time_ms', 0):.0f}ms")
        
        if comp_health.get('error_message'):
            print(f"{Fore.RED}Error: {comp_health['error_message']}{Style.RESET_ALL}")
        
        # ServiceNow details
        details = comp_health.get('details', {})
        if details:
            print(f"\nConfiguration:")
            print(f"  Enabled: {details.get('enabled', False)}")
            print(f"  Base URL: {details.get('base_url', 'Not configured')}")
            print(f"  Table: {details.get('table', 'unknown')}")
            print(f"  Connection Test: {details.get('connection_test', False)}")
            print(f"  Total Tickets: {details.get('total_tickets', 0)}")
        
        # Sync details
        sync_details = sn_health.get('last_sync_details', {})
        if sync_details:
            print(f"\nLast Sync:")
            print(f"  Time: {sync_details.get('last_sync', 'Never')}")
            print(f"  Status: {sync_details.get('status', 'unknown')}")
            print(f"  Tickets Processed: {sync_details.get('tickets_processed', 0)}")
            print(f"  Errors: {sync_details.get('errors', 0)}")
        
        # Ticket statistics
        ticket_stats = sn_health.get('ticket_statistics', {})
        if ticket_stats and ticket_stats.get('total_tickets', 0) > 0:
            print(f"\nTicket Statistics:")
            print(f"  Total: {ticket_stats.get('total_tickets', 0)}")
            
            # By status
            by_status = ticket_stats.get('by_status', {})
            if by_status:
                print(f"  By Status:")
                for status, count in by_status.items():
                    print(f"    {status}: {count}")
        
        return status == 'healthy'
    
    def continuous_monitor(self, interval: int = 30):
        """Run continuous health monitoring"""
        print(f"\n{Fore.CYAN}📡 CONTINUOUS HEALTH MONITORING{Style.RESET_ALL}")
        print(f"Checking every {interval} seconds. Press Ctrl+C to stop.")
        print("=" * 50)
        
        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] Checking system health...")
                
                health = self.check_basic_health()
                
                if "error" in health:
                    print(f"{Fore.RED}❌ {health['error']}{Style.RESET_ALL}")
                else:
                    status = health.get('overall_status', 'unknown')
                    status_color = self._get_status_color(status)
                    print(f"Status: {status_color}{status.upper()}{Style.RESET_ALL}")
                    
                    if status != 'healthy':
                        alerts = health.get('alerts', [])
                        for alert in alerts:
                            print(f"  ⚠️ {alert}")
                
                import time
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}🛑 Monitoring stopped by user{Style.RESET_ALL}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="RAG System Health Check CLI")
    parser.add_argument('--url', default='http://localhost:8000', help='RAG system base URL')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--mode', choices=['basic', 'comprehensive', 'components', 'servicenow', 'monitor'], 
                       default='basic', help='Health check mode')
    parser.add_argument('--interval', type=int, default=30, help='Monitor interval in seconds')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    # Create CLI instance
    cli = HealthCheckCLI(args.url, args.api_key)
    
    # Run health check based on mode
    try:
        if args.mode == 'basic':
            if args.json:
                result = cli.check_basic_health()
                print(json.dumps(result, indent=2))
            else:
                success = cli.display_basic_health()
                sys.exit(0 if success else 1)
                
        elif args.mode == 'comprehensive':
            if args.json:
                result = cli.check_comprehensive_health()
                print(json.dumps(result, indent=2))
            else:
                success = cli.display_comprehensive_health()
                sys.exit(0 if success else 1)
                
        elif args.mode == 'components':
            if args.json:
                result = cli.check_component_health()
                print(json.dumps(result, indent=2))
            else:
                success = cli.display_component_details()
                sys.exit(0 if success else 1)
                
        elif args.mode == 'servicenow':
            if args.json:
                result = cli.check_servicenow_health()
                print(json.dumps(result, indent=2))
            else:
                success = cli.display_servicenow_details()
                sys.exit(0 if success else 1)
                
        elif args.mode == 'monitor':
            cli.continuous_monitor(args.interval)
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Usage Examples

### 1. Basic Health Check
```bash
# Quick health status
python health_check_cli.py --mode basic

# With API key
python health_check_cli.py --mode basic --api-key rag_your_api_key_here
```

### 2. Comprehensive Health Check
```bash
# Full system health
python health_check_cli.py --mode comprehensive --api-key rag_your_api_key_here

# JSON output for monitoring tools
python health_check_cli.py --mode comprehensive --api-key rag_your_api_key_here --json
```

### 3. Component Details
```bash
# Detailed component status
python health_check_cli.py --mode components --api-key rag_your_api_key_here
```

### 4. ServiceNow Health
```bash
# ServiceNow integration status
python health_check_cli.py --mode servicenow --api-key rag_your_api_key_here
```

### 5. Continuous Monitoring
```bash
# Monitor every 30 seconds
python health_check_cli.py --mode monitor --interval 30

# Monitor with custom URL
python health_check_cli.py --mode monitor --url http://prod-server:8000 --api-key rag_prod_key
```

## Integration with Monitoring Tools

### Prometheus Metrics Endpoint
```bash
# Health status for Prometheus
curl -s http://localhost:8000/health/summary | jq -r '.overall_status'
```

### Nagios/Icinga Check
```bash
# Exit code 0 = OK, 1 = WARNING, 2 = CRITICAL
python health_check_cli.py --mode basic --json | jq -r '.overall_status' | \
  grep -q "healthy" && exit 0 || exit 2
```

This comprehensive heartbeat system provides:
- ✅ **9 Component Checks** including ServiceNow
- ✅ **Performance Monitoring** with thresholds
- ✅ **REST API Endpoints** for integration
- ✅ **CLI Tool** for manual checks
- ✅ **Continuous Monitoring** capability
- ✅ **JSON Output** for automation
- ✅ **Colored Console** output for readability

The system monitors everything from LLM connectivity to disk space, ensuring your RAG system is always healthy! 🩺