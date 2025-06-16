#!/usr/bin/env python3
"""
Simplified RAG System Entry Point
Bypasses potential hanging points for debugging
"""
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_basic_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('rag_system.log')
        ]
    )

def test_imports():
    """Test all imports to identify issues"""
    print("🔍 Testing imports...")
    
    try:
        print("  📦 Testing core imports...")
        from src.core.config_manager import ConfigManager
        print("    ✅ ConfigManager")
        
        from src.core.dependency_container import DependencyContainer
        print("    ✅ DependencyContainer")
        
        from src.core.json_store import JSONStore
        print("    ✅ JSONStore")
        
        print("  📦 Testing storage imports...")
        from src.storage.faiss_store import FAISSStore
        print("    ✅ FAISSStore")
        
        from src.storage.metadata_store import MetadataStore
        print("    ✅ MetadataStore")
        
        print("  📦 Testing API imports...")
        from src.api.main import create_api_app
        print("    ✅ create_api_app")
        
        print("  📦 Testing FastAPI...")
        import fastapi
        print("    ✅ FastAPI")
        
        import uvicorn
        print("    ✅ Uvicorn")
        
        print("✅ All imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_minimal_container():
    """Create a minimal dependency container"""
    print("🔧 Creating minimal container...")
    
    from src.core.dependency_container import DependencyContainer
    from src.core.config_manager import ConfigManager
    
    container = DependencyContainer()
    
    # Register only essential services
    print("  📦 Registering config manager...")
    container.register('config_manager', lambda container: ConfigManager())
    
    print("  📦 Getting config...")
    config_manager = container.get('config_manager')
    config = config_manager.get_config()
    print(f"    ✅ Config loaded: {config.environment}")
    
    return container

def create_minimal_api(container):
    """Create minimal API without full initialization"""
    print("🔧 Creating minimal API...")
    
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="RAG System API - Minimal Mode")
    
    @app.get("/")
    async def root():
        return {"message": "RAG System API is running in minimal mode"}
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "mode": "minimal",
            "message": "Basic API is running"
        }
    
    print("✅ Minimal API created")
    return app

def main():
    """Main entry point with step-by-step debugging"""
    print("🚀 Starting RAG System (Debug Mode)")
    print("=" * 50)
    
    try:
        # Step 1: Setup logging
        print("Step 1: Setting up logging...")
        setup_basic_logging()
        logging.info("Starting RAG System in debug mode")
        print("✅ Logging setup complete")
        
        # Step 2: Test imports
        print("\nStep 2: Testing imports...")
        if not test_imports():
            print("❌ Import test failed")
            return 1
        
        # Step 3: Create minimal container
        print("\nStep 3: Creating minimal container...")
        container = create_minimal_container()
        print("✅ Container created")
        
        # Step 4: Try full initialization (optional)
        print("\nStep 4: Attempting full initialization...")
        try:
            from src.core.system_init import initialize_system
            print("  🔧 Running full initialization...")
            full_container = initialize_system()
            print("  ✅ Full initialization successful")
            container = full_container
        except Exception as e:
            print(f"  ⚠️ Full initialization failed: {e}")
            print("  📝 Continuing with minimal container...")
            logging.warning(f"Full initialization failed: {e}")
        
        # Step 5: Create API
        print("\nStep 5: Creating API...")
        try:
            from src.api.main import create_api_app
            print("  🔧 Creating full API...")
            api_app = create_api_app(container, None)
            print("  ✅ Full API created")
        except Exception as e:
            print(f"  ⚠️ Full API creation failed: {e}")
            print("  📝 Creating minimal API...")
            api_app = create_minimal_api(container)
            logging.warning(f"Full API creation failed: {e}")
        
        # Step 6: Start server
        print("\nStep 6: Starting server...")
        config_manager = container.get('config_manager')
        config = config_manager.get_config()
        
        host = config.api.host
        port = config.api.port
        
        print(f"🌐 Starting server on {host}:{port}")
        print(f"📚 API docs will be available at: http://{host}:{port}/docs")
        print("🛑 Press Ctrl+C to stop")
        
        import uvicorn
        uvicorn.run(
            api_app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
        logging.info("Shutdown requested by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("👋 RAG System stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 