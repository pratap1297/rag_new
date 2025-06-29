#!/usr/bin/env python3
"""
Script to enable debug logging and extraction dumps for the RAG system
"""

import os
import logging
import sys
from pathlib import Path

def enable_debug_dumps():
    """Enable debug logging and extraction dumps"""
    
    # Set environment variable for extraction dumps
    os.environ['RAG_SAVE_EXTRACTION_DUMPS'] = 'true'
    print("✅ Set RAG_SAVE_EXTRACTION_DUMPS=true")
    
    # Configure logging to DEBUG level
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/debug_extraction.log', mode='a')
        ]
    )
    
    # Set root logger to DEBUG
    logging.getLogger().setLevel(logging.DEBUG)
    print("✅ Set logging level to DEBUG")
    
    # Create logs directory if it doesn't exist
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    print("✅ Created data/logs directory")
    
    print("\n🔧 Debug configuration enabled:")
    print(f"   - RAG_SAVE_EXTRACTION_DUMPS: {os.getenv('RAG_SAVE_EXTRACTION_DUMPS')}")
    print(f"   - Root logger level: {logging.getLogger().level}")
    print(f"   - DEBUG enabled: {logging.getLogger().isEnabledFor(logging.DEBUG)}")
    print(f"   - Extraction dumps will be saved to: data/logs/")
    
    return True

if __name__ == "__main__":
    enable_debug_dumps()
    print("\n🚀 Debug dumps are now enabled. Upload a file to see extraction dumps.") 