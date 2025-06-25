#!/usr/bin/env python3
"""
Simple Verification System Startup Script
Starts the RAG system with pipeline verification capabilities
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the verification system"""
    print("🚀 Starting RAG Pipeline Verification System...")
    print("=" * 60)
    
    try:
        # Set up basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("📋 Step 1: Importing system components...")
        from rag_system.src.core.system_init import initialize_system
        from rag_system.src.api.main import create_api_app
        
        print("📋 Step 2: Initializing system...")
        container = initialize_system()
        print("✅ System initialized successfully")
        
        print("📋 Step 3: Creating API application...")
        app = create_api_app(container)
        print("✅ API application created")
        
        print("📋 Step 4: Starting server...")
        import uvicorn
        
        # Get configuration
        config_manager = container.get('config_manager')
        config = config_manager.get_config()
        
        host = getattr(config.api, 'host', '0.0.0.0')
        port = getattr(config.api, 'port', 8000)
        
        print(f"🌐 Server starting on http://{host}:{port}")
        print(f"📊 Verification Dashboard: http://{host}:{port}/api/verification/dashboard")
        print(f"📚 API Documentation: http://{host}:{port}/docs")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the project root directory and dependencies are installed")
        return 1
    except Exception as e:
        print(f"❌ Failed to start system: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("👋 RAG Pipeline Verification System stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 