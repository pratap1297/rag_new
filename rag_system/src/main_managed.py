"""
Managed RAG System Main Application
Main application with comprehensive resource management to prevent leaks
"""
import logging
import sys
import signal
import asyncio
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.resource_manager import ApplicationLifecycle, managed_file_handle
from core.config_manager import ConfigManager
from core.dependency_container import DependencyContainer
from api.main import create_api_app
from monitoring.heartbeat_monitor import HeartbeatMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/rag_system.log')
    ]
)

logger = logging.getLogger(__name__)

class ManagedRAGSystem:
    """Main RAG System with comprehensive resource management"""
    
    def __init__(self):
        self.app_lifecycle = ApplicationLifecycle("RAGSystem")
        self.container = None
        self.heartbeat_monitor = None
        self.fastapi_app = None
        self.config_manager = None
        
    def initialize(self):
        """Initialize the RAG system with managed resources"""
        try:
            logger.info("🚀 Initializing Managed RAG System...")
            
            # Start application lifecycle
            self.app_lifecycle.startup()
            
            # Initialize configuration
            self.config_manager = ConfigManager()
            self.app_lifecycle.resource_manager.register_resource(
                "config_manager",
                self.config_manager
            )
            
            # Initialize container with managed thread pools
            self.container = DependencyContainer()
            self.container.config_manager = self.config_manager
            
            # Register container with resource manager
            self.app_lifecycle.resource_manager.register_resource(
                "container",
                self.container,
                lambda c: c.cleanup() if hasattr(c, 'cleanup') else None
            )
            
            # Initialize heartbeat monitor
            self.heartbeat_monitor = HeartbeatMonitor(
                container=self.container,
                thread_pool=self.app_lifecycle.get_thread_pool('background')
            )
            
            # Register heartbeat monitor
            self.app_lifecycle.resource_manager.register_resource(
                "heartbeat_monitor",
                self.heartbeat_monitor,
                lambda h: h.stop() if hasattr(h, 'stop') else None
            )
            
            # Create FastAPI application with managed resources
            self.fastapi_app = create_api_app(
                container=self.container,
                heartbeat_monitor_instance=self.heartbeat_monitor
            )
            
            logger.info("✅ Managed RAG System initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Managed RAG System: {e}")
            self.shutdown()
            raise
    
    def start_services(self):
        """Start all managed services"""
        try:
            logger.info("🔄 Starting managed services...")
            
            # Start heartbeat monitor
            if self.heartbeat_monitor:
                self.heartbeat_monitor.start()
                logger.info("✅ Heartbeat monitor started")
            
            # Load models through managed model loader
            self._load_managed_models()
            
            logger.info("✅ All managed services started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start services: {e}")
            raise
    
    def _load_managed_models(self):
        """Load ML models through managed model loader"""
        try:
            logger.info("🤖 Loading managed models...")
            
            # Load embedding model
            embedder = self.container.get('embedder')
            if hasattr(embedder, 'model_name'):
                from sentence_transformers import SentenceTransformer
                model = self.app_lifecycle.model_loader.load_model(
                    f"embedder_{embedder.model_name}",
                    SentenceTransformer,
                    embedder.model_name
                )
                # Replace the embedder's model with managed model
                embedder.model = model
                logger.info(f"✅ Loaded managed embedding model: {embedder.model_name}")
            
            # Load other models as needed
            # This can be extended for other ML models in the system
            
        except Exception as e:
            logger.error(f"❌ Failed to load managed models: {e}")
            # Don't raise - system can still work without models
    
    def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the FastAPI server with managed resources"""
        try:
            logger.info(f"🌐 Starting managed server on {host}:{port}")
            
            import uvicorn
            
            # Configure uvicorn with managed resources
            config = uvicorn.Config(
                app=self.fastapi_app,
                host=host,
                port=port,
                log_level="info",
                access_log=True,
                use_colors=True,
                loop="asyncio"
            )
            
            server = uvicorn.Server(config)
            
            # Register server with resource manager
            self.app_lifecycle.resource_manager.register_resource(
                "uvicorn_server",
                server,
                lambda s: s.shutdown() if hasattr(s, 'shutdown') else None
            )
            
            # Run server
            server.run()
            
        except KeyboardInterrupt:
            logger.info("🛑 Server interrupted by user")
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            raise
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the RAG system with comprehensive cleanup"""
        try:
            logger.info("🛑 Shutting down Managed RAG System...")
            
            # Application lifecycle will handle all cleanup automatically
            if self.app_lifecycle:
                self.app_lifecycle.shutdown()
            
            logger.info("✅ Managed RAG System shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

def main():
    """Main function with comprehensive resource management"""
    managed_system = None
    
    try:
        # Create managed system
        managed_system = ManagedRAGSystem()
        
        # Initialize system
        managed_system.initialize()
        
        # Start services
        managed_system.start_services()
        
        # Get configuration
        config = managed_system.config_manager.get_config()
        host = getattr(config.api, 'host', '0.0.0.0')
        port = getattr(config.api, 'port', 8000)
        
        logger.info("🎯 Managed RAG System ready!")
        
        # Run server
        managed_system.run_server(host=host, port=port)
        
    except KeyboardInterrupt:
        logger.info("🛑 Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)
    finally:
        if managed_system:
            managed_system.shutdown()

if __name__ == "__main__":
    main() 