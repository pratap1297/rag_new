"""
Resource Management System
Centralized resource management with automatic cleanup to prevent memory leaks
"""
import atexit
import weakref
import threading
import signal
import sys
import time
import gc
import logging
import psutil
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

class ResourceManager:
    """Centralized resource management with automatic cleanup"""
    
    _instances = weakref.WeakSet()
    
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._cleanup_handlers: Dict[str, callable] = {}
        self._lock = threading.Lock()
        self._shutdown_initiated = False
        
        # Register cleanup handlers
        atexit.register(self.cleanup_all)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Track all managers for global cleanup
        ResourceManager._instances.add(self)
        
        logging.info("ResourceManager initialized")
    
    def register_resource(self, name: str, resource: Any, cleanup_handler: Optional[callable] = None):
        """Register a resource with optional cleanup handler"""
        with self._lock:
            if self._shutdown_initiated:
                logging.warning(f"Cannot register resource {name} during shutdown")
                return
                
            self._resources[name] = resource
            if cleanup_handler:
                self._cleanup_handlers[name] = cleanup_handler
            logging.info(f"Registered resource: {name}")
    
    def get_resource(self, name: str) -> Any:
        """Get a registered resource"""
        with self._lock:
            return self._resources.get(name)
    
    def cleanup_resource(self, name: str):
        """Clean up a specific resource"""
        with self._lock:
            if name not in self._resources:
                return
                
            resource = self._resources[name]
            
            try:
                # Call custom cleanup handler if exists
                if name in self._cleanup_handlers:
                    try:
                        self._cleanup_handlers[name](resource)
                        logging.info(f"Custom cleanup completed for {name}")
                    except Exception as e:
                        logging.error(f"Error in cleanup handler for {name}: {e}")
                
                # Generic cleanup based on resource type
                self._generic_cleanup(name, resource)
                
                # Remove from registry
                del self._resources[name]
                if name in self._cleanup_handlers:
                    del self._cleanup_handlers[name]
                
                logging.info(f"Cleaned up resource: {name}")
                
            except Exception as e:
                logging.error(f"Error cleaning up resource {name}: {e}")
    
    def _generic_cleanup(self, name: str, resource: Any):
        """Generic cleanup based on resource type"""
        try:
            # Thread pools
            if hasattr(resource, 'shutdown') and callable(resource.shutdown):
                logging.info(f"Shutting down thread pool: {name}")
                resource.shutdown(wait=True)
                
            # File handles
            elif hasattr(resource, 'close') and callable(resource.close):
                logging.info(f"Closing file handle: {name}")
                resource.close()
            
            # ML Models (SentenceTransformer, etc.)
            elif hasattr(resource, 'model'):
                logging.info(f"Cleaning up ML model: {name}")
                if hasattr(resource.model, 'to'):
                    # Move to CPU to free GPU memory
                    resource.model.to('cpu')
                del resource.model
                gc.collect()
            
            # Database connections
            elif hasattr(resource, 'commit') and hasattr(resource, 'close'):
                logging.info(f"Closing database connection: {name}")
                try:
                    resource.commit()
                except:
                    try:
                        resource.rollback()
                    except:
                        pass
                resource.close()
            
            # Generic objects with cleanup method
            elif hasattr(resource, 'cleanup') and callable(resource.cleanup):
                logging.info(f"Calling cleanup method for: {name}")
                resource.cleanup()
                
        except Exception as e:
            logging.error(f"Error in generic cleanup for {name}: {e}")
    
    def cleanup_all(self):
        """Clean up all resources"""
        if self._shutdown_initiated:
            return
        
        self._shutdown_initiated = True
        logging.info("Starting comprehensive resource cleanup...")
        
        with self._lock:
            resources_to_cleanup = list(self._resources.keys())
        
        # Cleanup in reverse order of registration
        for name in reversed(resources_to_cleanup):
            try:
                self.cleanup_resource(name)
            except Exception as e:
                logging.error(f"Error cleaning up {name}: {e}")
        
        # Force garbage collection
        gc.collect()
        
        logging.info("Resource cleanup completed")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}, initiating cleanup...")
        self.cleanup_all()
        sys.exit(0)
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get statistics about managed resources"""
        with self._lock:
            try:
                process = psutil.Process()
                return {
                    'total_resources': len(self._resources),
                    'resource_names': list(self._resources.keys()),
                    'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'open_files': len(process.open_files()),
                    'threads': process.num_threads()
                }
            except Exception as e:
                logging.error(f"Error getting resource stats: {e}")
                return {
                    'total_resources': len(self._resources),
                    'resource_names': list(self._resources.keys()),
                    'error': str(e)
                }
    
    @classmethod
    def cleanup_all_instances(cls):
        """Clean up all resource manager instances"""
        for manager in cls._instances:
            if manager:
                manager.cleanup_all()


class ManagedThreadPool:
    """Thread pool with automatic resource management"""
    
    def __init__(self, max_workers: int, name: str, resource_manager: ResourceManager):
        self.name = name
        self.max_workers = max_workers
        self.resource_manager = resource_manager
        self._shutdown = False
        
        # Create executor with timeout protection
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=f"managed_{name}"
        )
        
        # Custom cleanup handler with timeout
        def cleanup_with_timeout(executor):
            if self._shutdown:
                return
            self._shutdown = True
            
            logging.info(f"Shutting down thread pool '{name}' with {max_workers} workers")
            try:
                # Attempt graceful shutdown
                executor.shutdown(wait=True)
                logging.info(f"Thread pool '{name}' shutdown completed")
            except Exception as e:
                logging.error(f"Error shutting down thread pool '{name}': {e}")
                # Force shutdown
                try:
                    executor._threads.clear()
                    executor._shutdown = True
                except:
                    pass
        
        # Register with resource manager
        self.resource_manager.register_resource(
            f"threadpool_{name}",
            self._executor,
            cleanup_with_timeout
        )
        
        logging.info(f"Created managed thread pool '{name}' with {max_workers} workers")
    
    def submit(self, fn, *args, **kwargs):
        """Submit task to thread pool"""
        if self._shutdown:
            raise RuntimeError(f"Thread pool '{self.name}' is shutdown")
        return self._executor.submit(fn, *args, **kwargs)
    
    def map(self, fn, *iterables, timeout=None, chunksize=1):
        """Map function over iterables"""
        if self._shutdown:
            raise RuntimeError(f"Thread pool '{self.name}' is shutdown")
        return self._executor.map(fn, *iterables, timeout=timeout, chunksize=chunksize)
    
    def shutdown(self, wait=True):
        """Shutdown thread pool"""
        if not self._shutdown:
            self.resource_manager.cleanup_resource(f"threadpool_{self.name}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class ManagedModelLoader:
    """ML model loader with automatic memory management"""
    
    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager
        self._models = {}
        self._model_memory = {}
    
    def load_model(self, name: str, model_class: type, *args, **kwargs):
        """Load a model with resource tracking"""
        if name in self._models:
            logging.info(f"Returning cached model: {name}")
            return self._models[name]
        
        # Track memory before loading
        try:
            process = psutil.Process()
            memory_before = process.memory_info().rss
        except:
            memory_before = 0
        
        logging.info(f"Loading model '{name}' of type {model_class.__name__}")
        
        try:
            # Create model
            model = model_class(*args, **kwargs)
            
            # Track memory after loading
            try:
                memory_after = process.memory_info().rss
                memory_used = memory_after - memory_before
                self._model_memory[name] = memory_used
            except:
                memory_used = 0
            
            # Custom cleanup handler for models
            def cleanup_model(m):
                try:
                    logging.info(f"Cleaning up model '{name}'")
                    
                    # Free model memory
                    if hasattr(m, 'model'):
                        if hasattr(m.model, 'to'):
                            # Move to CPU to free GPU memory
                            m.model.to('cpu')
                        del m.model
                    
                    # Clear any caches
                    if hasattr(m, 'clear_cache'):
                        m.clear_cache()
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Log memory freed
                    if name in self._model_memory:
                        memory_freed = self._model_memory[name]
                        logging.info(f"Freed ~{memory_freed / 1024 / 1024:.2f} MB from model '{name}'")
                        del self._model_memory[name]
                        
                except Exception as e:
                    logging.error(f"Error cleaning up model '{name}': {e}")
            
            # Register with resource manager
            self.resource_manager.register_resource(f"model_{name}", model, cleanup_model)
            self._models[name] = model
            
            # Log memory usage
            if memory_used > 0:
                logging.info(f"Model '{name}' loaded successfully, using {memory_used / 1024 / 1024:.2f} MB")
            else:
                logging.info(f"Model '{name}' loaded successfully")
            
            return model
            
        except Exception as e:
            logging.error(f"Failed to load model '{name}': {e}")
            raise
    
    def unload_model(self, name: str):
        """Unload a specific model"""
        if name in self._models:
            logging.info(f"Unloading model: {name}")
            self.resource_manager.cleanup_resource(f"model_{name}")
            if name in self._models:
                del self._models[name]
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded models"""
        return {
            'loaded_models': list(self._models.keys()),
            'total_models': len(self._models),
            'memory_usage': {
                name: f"{mem / 1024 / 1024:.2f} MB" 
                for name, mem in self._model_memory.items()
            },
            'total_memory_mb': sum(self._model_memory.values()) / 1024 / 1024
        }


@contextmanager
def managed_file_handle(filepath: Union[str, Path], mode: str, resource_manager: ResourceManager):
    """Context manager for file handles with automatic cleanup"""
    file_handle = None
    filepath = Path(filepath)
    resource_name = f"file_{filepath.name}_{id(str(filepath))}"
    
    try:
        logging.debug(f"Opening file: {filepath} in mode {mode}")
        file_handle = open(filepath, mode)
        resource_manager.register_resource(
            resource_name, 
            file_handle,
            lambda f: f.close() if not f.closed else None
        )
        yield file_handle
    except Exception as e:
        logging.error(f"Error opening file {filepath}: {e}")
        raise
    finally:
        if file_handle:
            resource_manager.cleanup_resource(resource_name)


class ApplicationLifecycle:
    """Application lifecycle manager with comprehensive resource management"""
    
    def __init__(self, app_name: str = "RAGSystem"):
        self.app_name = app_name
        self.resource_manager = ResourceManager()
        self.thread_pools = {}
        self.model_loader = ManagedModelLoader(self.resource_manager)
        self._startup_complete = False
        self._shutdown_complete = False
        
        logging.info(f"Initialized {app_name} lifecycle manager")
    
    def startup(self):
        """Application startup with resource initialization"""
        if self._startup_complete:
            logging.warning("Application already started")
            return
            
        logging.info(f"Starting {self.app_name}...")
        
        try:
            # Create managed thread pools
            self.thread_pools['main'] = ManagedThreadPool(4, 'main', self.resource_manager)
            self.thread_pools['io'] = ManagedThreadPool(8, 'io', self.resource_manager)
            self.thread_pools['compute'] = ManagedThreadPool(2, 'compute', self.resource_manager)
            self.thread_pools['background'] = ManagedThreadPool(2, 'background', self.resource_manager)
            
            # Register application-level cleanup
            atexit.register(self.shutdown)
            
            self._startup_complete = True
            logging.info(f"{self.app_name} startup completed successfully")
            
        except Exception as e:
            logging.error(f"Error during {self.app_name} startup: {e}")
            self.shutdown()
            raise
    
    def shutdown(self):
        """Application shutdown with comprehensive cleanup"""
        if self._shutdown_complete:
            return
            
        logging.info(f"Shutting down {self.app_name}...")
        
        try:
            # Get final stats before cleanup
            stats = self.resource_manager.get_resource_stats()
            logging.info(f"Pre-shutdown stats: {stats}")
            
            # Cleanup all resources
            self.resource_manager.cleanup_all()
            
            # Clear references
            self.thread_pools.clear()
            
            # Force garbage collection
            gc.collect()
            
            self._shutdown_complete = True
            logging.info(f"{self.app_name} shutdown completed")
            
        except Exception as e:
            logging.error(f"Error during {self.app_name} shutdown: {e}")
    
    def get_thread_pool(self, name: str) -> Optional[ManagedThreadPool]:
        """Get a managed thread pool"""
        return self.thread_pools.get(name)
    
    def create_custom_thread_pool(self, name: str, max_workers: int) -> ManagedThreadPool:
        """Create a custom managed thread pool"""
        if name in self.thread_pools:
            logging.warning(f"Thread pool '{name}' already exists")
            return self.thread_pools[name]
        
        pool = ManagedThreadPool(max_workers, name, self.resource_manager)
        self.thread_pools[name] = pool
        return pool
    
    @contextmanager
    def managed_operation(self, operation_name: str):
        """Context manager for managed operations with timing and cleanup"""
        logging.info(f"Starting operation: {operation_name}")
        start_time = time.time()
        
        # Get initial memory
        try:
            process = psutil.Process()
            memory_before = process.memory_info().rss
        except:
            memory_before = 0
        
        try:
            yield self
        except Exception as e:
            logging.error(f"Error in operation '{operation_name}': {e}")
            raise
        finally:
            # Calculate metrics
            elapsed = time.time() - start_time
            try:
                memory_after = process.memory_info().rss
                memory_delta = memory_after - memory_before
                
                logging.info(
                    f"Operation '{operation_name}' completed in {elapsed:.2f}s, "
                    f"memory delta: {memory_delta / 1024 / 1024:.2f} MB"
                )
            except:
                logging.info(f"Operation '{operation_name}' completed in {elapsed:.2f}s")
            
            # Cleanup any operation-specific resources
            gc.collect()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        resource_stats = self.resource_manager.get_resource_stats()
        model_stats = self.model_loader.get_model_stats()
        
        return {
            'app_name': self.app_name,
            'startup_complete': self._startup_complete,
            'shutdown_complete': self._shutdown_complete,
            'thread_pools': {
                name: {
                    'max_workers': pool.max_workers,
                    'shutdown': pool._shutdown
                } for name, pool in self.thread_pools.items()
            },
            'resources': resource_stats,
            'models': model_stats,
            'timestamp': time.time()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on managed resources"""
        health = {
            'status': 'healthy',
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check thread pools
            for name, pool in self.thread_pools.items():
                if pool._shutdown:
                    health['issues'].append(f"Thread pool '{name}' is shutdown")
            
            # Check memory usage
            stats = self.resource_manager.get_resource_stats()
            if 'memory_usage_mb' in stats and stats['memory_usage_mb'] > 1000:  # 1GB threshold
                health['warnings'].append(f"High memory usage: {stats['memory_usage_mb']:.2f} MB")
            
            # Check open files
            if 'open_files' in stats and stats['open_files'] > 100:
                health['warnings'].append(f"Many open files: {stats['open_files']}")
            
            if health['issues']:
                health['status'] = 'unhealthy'
            elif health['warnings']:
                health['status'] = 'warning'
                
        except Exception as e:
            health['status'] = 'error'
            health['issues'].append(f"Health check failed: {e}")
        
        return health


# Global application instance
_global_app = None

def get_global_app() -> ApplicationLifecycle:
    """Get or create global application instance"""
    global _global_app
    if _global_app is None:
        _global_app = ApplicationLifecycle("GlobalRAGSystem")
        _global_app.startup()
    return _global_app

def create_managed_app(app_name: str = "RAGSystem") -> ApplicationLifecycle:
    """Create application with managed resources"""
    app = ApplicationLifecycle(app_name)
    app.startup()
    return app

# Ensure cleanup on module exit
atexit.register(ResourceManager.cleanup_all_instances) 