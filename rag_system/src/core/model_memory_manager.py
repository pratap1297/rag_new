"""
Model Memory Manager
Manages ML model memory with automatic cleanup and resource management
"""
import weakref
import gc
from typing import Optional, List, Dict, Any, Callable
import threading
import time
import logging
import atexit
from datetime import datetime, timedelta

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class ModelWrapper:
    """Wrapper for models to enable weak references"""
    def __init__(self, model, model_id: str):
        self.model = model
        self.model_id = model_id
        self.created_at = datetime.now()
    
    def __getattr__(self, name):
        # Delegate attribute access to the wrapped model
        return getattr(self.model, name)
    
    def __getitem__(self, key):
        # Delegate dictionary-style access to the wrapped model
        return self.model[key]
    
    def __setitem__(self, key, value):
        # Delegate dictionary-style assignment to the wrapped model
        self.model[key] = value
    
    def __contains__(self, key):
        # Delegate 'in' operator to the wrapped model
        return key in self.model
    
    def __call__(self, *args, **kwargs):
        # Make the wrapper callable if the model is callable
        if callable(self.model):
            return self.model(*args, **kwargs)
        raise TypeError(f"'{type(self.model).__name__}' object is not callable")
    
    def __len__(self):
        # Delegate len() to the wrapped model
        return len(self.model)
    
    def __str__(self):
        # String representation
        return f"ModelWrapper({self.model_id}, {type(self.model).__name__})"
    
    def __repr__(self):
        return self.__str__()

class ModelMemoryManager:
    """Manage ML model memory with automatic cleanup"""
    
    def __init__(self, max_memory_mb: int = 1024, idle_timeout: int = 300):
        self.max_memory_mb = max_memory_mb
        self.idle_timeout = idle_timeout  # seconds
        self._models: Dict[str, Any] = {}
        self._model_refs: Dict[str, weakref.ref] = {}
        self._last_used: Dict[str, float] = {}
        self._model_info: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()  # Use RLock for nested calls
        self._cleanup_thread = None
        self._running = True
        self._stats = {
            'models_loaded': 0,
            'models_evicted': 0,
            'memory_cleanups': 0,
            'last_cleanup': None
        }
        
        # Register cleanup on exit
        atexit.register(self.shutdown)
        
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        self.logger.info(f"Model memory manager initialized - Max memory: {max_memory_mb}MB, Idle timeout: {idle_timeout}s")
    
    def get_model(self, model_id: str, loader_func: Callable, *args, **kwargs) -> Any:
        """Get or load a model with memory management"""
        with self._lock:
            # Check if model exists and is alive
            if model_id in self._model_refs:
                model_ref = self._model_refs[model_id]
                model = model_ref()
                if model is not None:
                    self._last_used[model_id] = time.time()
                    self.logger.debug(f"Retrieved cached model: {model_id}")
                    return model
                else:
                    # Model was garbage collected, clean up references
                    self._cleanup_dead_reference(model_id)
            
            # Check memory before loading
            if not self._check_memory_available():
                self._evict_models_for_memory()
            
            # Load model
            self.logger.info(f"Loading model: {model_id}")
            start_time = time.time()
            
            try:
                raw_model = loader_func(*args, **kwargs)
                load_time = time.time() - start_time
                
                # Wrap model to enable weak references
                model_wrapper = ModelWrapper(raw_model, model_id)
                
                # Store model with weak reference
                self._models[model_id] = model_wrapper
                self._model_refs[model_id] = weakref.ref(model_wrapper, self._create_cleanup_callback(model_id))
                self._last_used[model_id] = time.time()
                self._model_info[model_id] = {
                    'loaded_at': datetime.now(),
                    'load_time': load_time,
                    'args': args,
                    'kwargs': kwargs,
                    'access_count': 1
                }
                
                self._stats['models_loaded'] += 1
                
                # Log memory usage if available
                memory_info = self._get_memory_info()
                if memory_info:
                    self.logger.info(f"Model {model_id} loaded in {load_time:.2f}s. "
                                   f"Current memory: {memory_info['current_mb']:.2f}MB")
                
                # Return the wrapped model (acts like the original)
                return model_wrapper
                
            except Exception as e:
                self.logger.error(f"Failed to load model {model_id}: {e}")
                raise
    
    def _create_cleanup_callback(self, model_id: str):
        """Create a cleanup callback for weak reference"""
        def cleanup_callback(ref):
            self._on_model_deleted(model_id, ref)
        return cleanup_callback
    
    def _check_memory_available(self) -> bool:
        """Check if enough memory is available"""
        if not PSUTIL_AVAILABLE:
            return True  # Can't check, assume available
        
        try:
            process = psutil.Process()
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            available = current_memory_mb < self.max_memory_mb
            
            if not available:
                self.logger.warning(f"Memory limit reached: {current_memory_mb:.2f}MB >= {self.max_memory_mb}MB")
            
            return available
        except Exception as e:
            self.logger.warning(f"Failed to check memory: {e}")
            return True
    
    def _get_memory_info(self) -> Optional[Dict[str, float]]:
        """Get current memory information"""
        if not PSUTIL_AVAILABLE:
            return None
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'current_mb': memory_info.rss / 1024 / 1024,
                'peak_mb': memory_info.peak_wss / 1024 / 1024 if hasattr(memory_info, 'peak_wss') else 0
            }
        except Exception:
            return None
    
    def _evict_models_for_memory(self):
        """Evict models to free memory"""
        if not self._last_used:
            self.logger.warning("No models to evict for memory")
            return
        
        # Sort by last used time (oldest first)
        models_by_age = sorted(self._last_used.items(), key=lambda x: x[1])
        
        # Evict up to half of the models or until memory is available
        models_to_evict = min(len(models_by_age) // 2 + 1, len(models_by_age))
        
        for i in range(models_to_evict):
            model_id, _ = models_by_age[i]
            self.logger.info(f"Evicting model due to memory pressure: {model_id}")
            self._unload_model(model_id)
            
            # Check if we have enough memory now
            if self._check_memory_available():
                break
        
        self._stats['memory_cleanups'] += 1
    
    def _evict_oldest_model(self):
        """Evict the least recently used model"""
        if not self._last_used:
            return
        
        # Find oldest model
        oldest_id = min(self._last_used, key=self._last_used.get)
        
        self.logger.info(f"Evicting oldest model: {oldest_id}")
        self._unload_model(oldest_id)
    
    def _unload_model(self, model_id: str):
        """Unload a specific model"""
        if model_id not in self._models:
            return
        
        try:
            model = self._models[model_id]
            
            # Clean up model-specific resources
            self._cleanup_model_resources(model)
            
            # Remove from tracking
            del self._models[model_id]
            if model_id in self._model_refs:
                del self._model_refs[model_id]
            if model_id in self._last_used:
                del self._last_used[model_id]
            if model_id in self._model_info:
                del self._model_info[model_id]
            
            self._stats['models_evicted'] += 1
            
            # Force garbage collection
            gc.collect()
            
            # Additional cleanup for PyTorch
            if TORCH_AVAILABLE:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            # Log memory after cleanup
            memory_info = self._get_memory_info()
            if memory_info:
                self.logger.info(f"Model {model_id} unloaded. Current memory: {memory_info['current_mb']:.2f}MB")
            else:
                self.logger.info(f"Model {model_id} unloaded")
                
        except Exception as e:
            self.logger.error(f"Error unloading model {model_id}: {e}")
    
    def _cleanup_model_resources(self, model_wrapper):
        """Clean up model-specific resources"""
        try:
            # Get the actual model from wrapper
            if isinstance(model_wrapper, ModelWrapper):
                actual_model = model_wrapper.model
            else:
                actual_model = model_wrapper
            
            # PyTorch model cleanup
            if TORCH_AVAILABLE and hasattr(actual_model, 'to'):
                # Move to CPU to free GPU memory
                try:
                    actual_model.to('cpu')
                    self.logger.debug("Model moved to CPU")
                except Exception as e:
                    self.logger.debug(f"Failed to move model to CPU: {e}")
            
            # Sentence transformer cleanup
            if hasattr(actual_model, '_modules'):
                # Clear module cache
                try:
                    if hasattr(actual_model, 'tokenizer'):
                        del actual_model.tokenizer
                    if hasattr(actual_model, '_target_device'):
                        actual_model._target_device = None
                except Exception as e:
                    self.logger.debug(f"Sentence transformer cleanup failed: {e}")
            
            # Generic cleanup for objects with close/cleanup methods
            for method_name in ['close', 'cleanup', 'clear_cache']:
                if hasattr(actual_model, method_name):
                    try:
                        getattr(actual_model, method_name)()
                        self.logger.debug(f"Called {method_name} on model")
                    except Exception as e:
                        self.logger.debug(f"Failed to call {method_name}: {e}")
                        
        except Exception as e:
            self.logger.debug(f"Model resource cleanup failed: {e}")
    
    def _cleanup_dead_reference(self, model_id: str):
        """Clean up references to a dead model"""
        if model_id in self._model_refs:
            del self._model_refs[model_id]
        if model_id in self._last_used:
            del self._last_used[model_id]
        if model_id in self._model_info:
            del self._model_info[model_id]
    
    def _on_model_deleted(self, model_id: str, ref):
        """Callback when model is garbage collected"""
        with self._lock:
            self.logger.debug(f"Model {model_id} was garbage collected")
            self._cleanup_dead_reference(model_id)
    
    def _cleanup_idle_models(self):
        """Clean up models that haven't been used recently"""
        while self._running:
            try:
                time.sleep(60)  # Check every minute
                
                with self._lock:
                    current_time = time.time()
                    models_to_unload = []
                    
                    for model_id, last_used in self._last_used.items():
                        if current_time - last_used > self.idle_timeout:
                            models_to_unload.append(model_id)
                    
                    if models_to_unload:
                        self.logger.info(f"Cleaning up {len(models_to_unload)} idle models")
                        for model_id in models_to_unload:
                            self._unload_model(model_id)
                        
                        self._stats['last_cleanup'] = datetime.now()
                        
            except Exception as e:
                self.logger.error(f"Error in cleanup thread: {e}")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_idle_models,
                daemon=True,
                name="ModelMemoryCleanup"
            )
            self._cleanup_thread.start()
            self.logger.debug("Started model cleanup thread")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics"""
        with self._lock:
            memory_info = self._get_memory_info()
            
            return {
                'active_models': len(self._models),
                'models_loaded': self._stats['models_loaded'],
                'models_evicted': self._stats['models_evicted'],
                'memory_cleanups': self._stats['memory_cleanups'],
                'last_cleanup': self._stats['last_cleanup'].isoformat() if self._stats['last_cleanup'] else None,
                'memory_info': memory_info,
                'max_memory_mb': self.max_memory_mb,
                'idle_timeout': self.idle_timeout,
                'model_details': {
                    model_id: {
                        'loaded_at': info['loaded_at'].isoformat(),
                        'load_time': info['load_time'],
                        'access_count': info['access_count'],
                        'last_used': datetime.fromtimestamp(self._last_used.get(model_id, 0)).isoformat()
                    }
                    for model_id, info in self._model_info.items()
                }
            }
    
    def force_cleanup(self):
        """Force cleanup of all idle models"""
        with self._lock:
            current_time = time.time()
            models_to_unload = []
            
            for model_id, last_used in self._last_used.items():
                if current_time - last_used > 60:  # More than 1 minute idle
                    models_to_unload.append(model_id)
            
            for model_id in models_to_unload:
                self._unload_model(model_id)
            
            # Force garbage collection
            gc.collect()
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info(f"Force cleanup completed - {len(models_to_unload)} models unloaded")
    
    def unload_model(self, model_id: str) -> bool:
        """Manually unload a specific model"""
        with self._lock:
            if model_id in self._models:
                self._unload_model(model_id)
                return True
            return False
    
    def shutdown(self):
        """Shutdown memory manager and clean up all models"""
        self.logger.info("Shutting down model memory manager...")
        self._running = False
        
        with self._lock:
            model_ids = list(self._models.keys())
            for model_id in model_ids:
                self._unload_model(model_id)
        
        # Final cleanup
        gc.collect()
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.logger.info("Model memory manager shutdown complete")
    
    def __del__(self):
        """Cleanup when manager is deleted"""
        try:
            self.shutdown()
        except Exception:
            pass


# Singleton model manager
_model_memory_manager = None
_manager_lock = threading.Lock()

def get_model_memory_manager() -> ModelMemoryManager:
    """Get singleton model memory manager"""
    global _model_memory_manager
    
    if _model_memory_manager is None:
        with _manager_lock:
            if _model_memory_manager is None:
                _model_memory_manager = ModelMemoryManager(
                    max_memory_mb=2048,  # 2GB max for models
                    idle_timeout=300  # 5 minutes idle timeout
                )
    
    return _model_memory_manager

def shutdown_model_memory_manager():
    """Shutdown the global model memory manager"""
    global _model_memory_manager
    
    if _model_memory_manager is not None:
        _model_memory_manager.shutdown()
        _model_memory_manager = None 