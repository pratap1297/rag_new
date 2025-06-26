#!/usr/bin/env python3
"""
RAG System Entry Point
"""
import logging
import sys
import atexit
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Global thread pool reference for cleanup
thread_pool = None

def cleanup_thread_pool():
    """Ensure thread pool is properly closed"""
    global thread_pool
    
    # Clean up the API thread pool
    if thread_pool:
        try:
            thread_pool.shutdown(wait=False)
            logging.info("✅ API thread pool shutdown complete")
        except Exception as e:
            logging.error(f"Error shutting down API thread pool: {e}")
        finally:
            thread_pool = None
    
    # Clean up global application lifecycle and all managed resources
    try:
        from src.core.resource_manager import get_global_app, ResourceManager
        app_lifecycle = get_global_app()
        if app_lifecycle:
            logging.info("🔄 Cleaning up global application lifecycle...")
            app_lifecycle.shutdown()
            logging.info("✅ Global application lifecycle cleanup complete")
        
        # Clean up all resource manager instances
        ResourceManager.cleanup_all_instances()
        logging.info("✅ All resource manager instances cleaned up")
        
    except Exception as e:
        logging.error(f"Error during global cleanup: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logging.info(f"Received signal {signum}, initiating cleanup...")
    cleanup_thread_pool()
    sys.exit(0)

# Register cleanup with atexit and signal handlers
atexit.register(cleanup_thread_pool)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point"""
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logging.info("Starting RAG System...")
        
        # Initialize core system
        from src.core.system_init import initialize_system
        logging.info("Initializing system components...")
        container = initialize_system()
        
        # Setup monitoring
        try:
            from src.monitoring.setup import setup_monitoring
            logging.info("Setting up monitoring...")
            monitoring = setup_monitoring(container.get('config_manager'))
        except ImportError:
            logging.warning("Monitoring setup not available, using basic monitoring")
            monitoring = None
        
        # Initialize heartbeat monitor
        heartbeat_monitor = None
        try:
            from src.monitoring.heartbeat_monitor import initialize_heartbeat_monitor
            logging.info("Initializing heartbeat monitor...")
            heartbeat_monitor = initialize_heartbeat_monitor(container)
            logging.info("✅ Heartbeat monitor initialized successfully")
        except Exception as e:
            logging.warning(f"Heartbeat monitor initialization failed: {e}")
            logging.info("System will continue without heartbeat monitoring")
        
        # Initialize folder monitor
        folder_monitor = None
        try:
            from src.monitoring.folder_monitor import initialize_folder_monitor
            logging.info("Initializing folder monitor...")
            config_manager = container.get('config_manager')
            folder_monitor = initialize_folder_monitor(container, config_manager)
            logging.info("✅ Folder monitor initialized successfully")
        except Exception as e:
            logging.warning(f"Folder monitor initialization failed: {e}")
            logging.info("System will continue without folder monitoring")
        
        # Initialize enhanced folder monitor
        enhanced_folder_monitor = None
        try:
            from src.monitoring.enhanced_folder_monitor import initialize_enhanced_folder_monitor
            logging.info("Initializing enhanced folder monitor...")
            config_manager = container.get('config_manager')
            enhanced_folder_monitor = initialize_enhanced_folder_monitor(container, config_manager)
            logging.info("✅ Enhanced folder monitor initialized successfully")
        except Exception as e:
            logging.warning(f"Enhanced folder monitor initialization failed: {e}")
            logging.info("System will continue without enhanced folder monitoring")
        
        # Update the global monitors in the API module
        try:
            import src.api.main as api_main
            api_main.heartbeat_monitor = heartbeat_monitor
            logging.info("✅ Heartbeat monitor registered with API")
        except Exception as e:
            logging.warning(f"Failed to register heartbeat monitor with API: {e}")
        
        # Register folder monitor with API module
        try:
            from src.monitoring import folder_monitor as folder_monitor_module
            folder_monitor_module.folder_monitor = folder_monitor
            logging.info("✅ Folder monitor registered with API")
        except Exception as e:
            logging.warning(f"Failed to register folder monitor with API: {e}")
        
        # Create API app
        from src.api.main import create_api_app
        logging.info("Creating FastAPI application...")
        api_app = create_api_app(container, monitoring, heartbeat_monitor, folder_monitor, enhanced_folder_monitor)
        
        # Capture thread pool reference for cleanup
        global thread_pool
        try:
            import src.api.main as api_main
            thread_pool = api_main.thread_pool
            if thread_pool:
                logging.info("✅ Thread pool captured for cleanup")
        except Exception as e:
            logging.warning(f"Could not capture thread pool reference: {e}")
        
        logging.info("FastAPI application created successfully")
        
        # Start continuous health monitoring (if enabled in config)
        if heartbeat_monitor:
            config_manager = container.get('config_manager')
            config = config_manager.get_config()
            
            # Check if heartbeat is enabled in config (default: False)
            heartbeat_enabled = getattr(config, 'heartbeat', {}).get('enabled', False)
            
            if heartbeat_enabled:
                logging.info("Starting continuous health monitoring...")
                heartbeat_monitor.start_monitoring()
            else:
                logging.info("Heartbeat monitoring disabled in config")
        else:
            logging.info("Heartbeat monitor not available, skipping continuous monitoring")
        
        # Start folder monitoring (if enabled in config and folders are configured)
        if folder_monitor:
            config_manager = container.get('config_manager')
            config = config_manager.get_config()
            
            # Check if folder monitoring is enabled in config
            folder_config = getattr(config, 'folder_monitoring', None)
            if folder_config and getattr(folder_config, 'enabled', True):
                monitored_folders = getattr(folder_config, 'monitored_folders', [])
                if monitored_folders:
                    logging.info(f"Starting folder monitoring for {len(monitored_folders)} folders...")
                    result = folder_monitor.start_monitoring()
                    if result.get('success'):
                        logging.info("✅ Folder monitoring started successfully")
                    else:
                        logging.warning(f"Failed to start folder monitoring: {result.get('error')}")
                else:
                    logging.info("No folders configured for monitoring")
            else:
                logging.info("Folder monitoring disabled in config")
        else:
            logging.info("Folder monitor not available, skipping folder monitoring")
        
        # Start API server
        import uvicorn
        config_manager = container.get('config_manager')
        config = config_manager.get_config()
        
        logging.info(f"Starting server on {config.api.host}:{config.api.port}")
        
        uvicorn.run(
            api_app,
            host=config.api.host,
            port=config.api.port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
        cleanup_thread_pool()
    except Exception as e:
        logging.error(f"Failed to start RAG System: {e}")
        cleanup_thread_pool()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 