#!/usr/bin/env python3
"""
Enhanced RAG System Management UI Launcher
Launches the enhanced Gradio interface with file upload and scheduler functionality
"""
import logging
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Launch the enhanced RAG System Management UI"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Import the enhanced UI
        from src.api.gradio_ui_enhanced import create_enhanced_interface
        
        # Configuration
        API_URL = "http://localhost:8000"
        UI_PORT = 7861
        
        logger.info("Starting Enhanced RAG System Management UI...")
        logger.info(f"API URL: {API_URL}")
        logger.info(f"Enhanced UI will be available at: http://0.0.0.0:{UI_PORT}")
        
        # Create and launch the enhanced interface
        interface = create_enhanced_interface(api_base_url=API_URL)
        
        # Launch with enhanced features
        interface.launch(
            server_name="0.0.0.0",
            server_port=UI_PORT,
            share=False,
            debug=True,
            show_tips=True,
            enable_queue=True
        )
        
    except ImportError as e:
        logger.error(f"Failed to import enhanced UI components: {e}")
        logger.error("Make sure all dependencies are installed:")
        logger.error("pip install gradio requests pandas")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start enhanced UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
