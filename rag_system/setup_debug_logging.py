#!/usr/bin/env python3
"""
Setup Debug Logging for Extraction Verification
Configures comprehensive logging for PDF/Excel processors and ingestion engine
"""
import os
import logging
import sys
from pathlib import Path

def setup_debug_logging(enable_extraction_debug=True, save_dumps=True):
    """Setup debug logging for extraction verification"""
    
    print("🔧 Setting up Debug Logging for Extraction Verification")
    print("=" * 60)
    
    # Set environment variables
    if enable_extraction_debug:
        os.environ['RAG_EXTRACTION_DEBUG'] = 'true'
        print("✅ RAG_EXTRACTION_DEBUG = true")
    
    if save_dumps:
        os.environ['RAG_SAVE_EXTRACTION_DUMPS'] = 'true'
        print("✅ RAG_SAVE_EXTRACTION_DUMPS = true")
    
    # Create logs directory
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Logs directory created: {logs_dir}")
    
    # Setup detailed logging configuration
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / 'rag_extraction.log', encoding='utf-8')
        ]
    )
    
    # Create extraction-specific handler for detailed debugging
    extraction_handler = logging.FileHandler(logs_dir / 'extraction_debug.log', encoding='utf-8')
    extraction_handler.setLevel(logging.DEBUG)
    extraction_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    extraction_handler.setFormatter(extraction_formatter)
    
    # Add handler to specific loggers for comprehensive tracking
    extraction_loggers = [
        'EnhancedPDFProcessor',
        'RobustExcelProcessor', 
        'IngestionEngine',
        'AzureAIClient',
        'RobustAzureAIClient'
    ]
    
    for logger_name in extraction_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(extraction_handler)
        logger.setLevel(logging.DEBUG)
        print(f"✅ Debug logging enabled for: {logger_name}")
    
    print(f"\n📋 Debug Configuration Summary:")
    print(f"  - General log file: {logs_dir / 'rag_extraction.log'}")
    print(f"  - Debug log file: {logs_dir / 'extraction_debug.log'}")
    print(f"  - Extraction dumps: {'Enabled' if save_dumps else 'Disabled'}")
    print(f"  - Debug mode: {'Enabled' if enable_extraction_debug else 'Disabled'}")
    
    return {
        'logs_dir': str(logs_dir),
        'general_log': str(logs_dir / 'rag_extraction.log'),
        'debug_log': str(logs_dir / 'extraction_debug.log'),
        'extraction_debug': enable_extraction_debug,
        'save_dumps': save_dumps
    }

def create_verification_script():
    """Create a verification script to test extraction with full logging"""
    
    script_content = '''#!/usr/bin/env python3
"""
Verify Extraction with Debug Logging
Tests PDF/Excel extraction with comprehensive logging enabled
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def verify_extraction(file_path: str):
    """Verify extraction for a specific file with full debug logging"""
    
    print(f"🧪 Verifying extraction for: {file_path}")
    print("=" * 60)
    
    # Setup debug logging
    from setup_debug_logging import setup_debug_logging
    debug_config = setup_debug_logging(enable_extraction_debug=True, save_dumps=True)
    
    print(f"Debug logging configured:")
    print(f"  - Logs directory: {debug_config['logs_dir']}")
    print(f"  - Debug log: {debug_config['debug_log']}")
    
    try:
        # Initialize system
        from src.core.system_init import initialize_system
        
        print("\\n🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        
        # Process file
        print(f"\\n📄 Processing file: {file_path}")
        result = ingestion_engine.ingest_file(file_path)
        
        # Display results
        print(f"\\n📊 Processing Results:")
        print(f"  - Status: {result.get('status', 'Unknown')}")
        print(f"  - Chunks created: {result.get('chunk_count', 0)}")
        print(f"  - Vectors added: {result.get('vector_count', 0)}")
        print(f"  - Processing time: {result.get('processing_time', 'Unknown')}")
        
        if result.get('metadata', {}).get('processor_used'):
            print(f"  - Processor used: {result['metadata']['processor_used']}")
            print(f"  - Processor chunks: {result['metadata'].get('processor_chunk_count', 0)}")
            print(f"  - Processor time: {result['metadata'].get('processor_processing_time', 'Unknown')}")
        
        # Save detailed result
        output_file = f"extraction_verify_{Path(file_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = Path(debug_config['logs_dir']) / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\\n✅ Verification complete!")
        print(f"  - Detailed results: {output_path}")
        print(f"  - Debug logs: {debug_config['debug_log']}")
        print(f"  - Extraction dumps in: {debug_config['logs_dir']}")
        
        return result
        
    except Exception as e:
        print(f"\\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = verify_extraction(sys.argv[1])
        if result:
            print(f"\\n🎯 Quick Test Recommendation:")
            print(f"   To test Azure Vision integration, try:")
            print(f"   python verify_extraction.py test_documents/BuildingA_Network_Layout.pdf")
        else:
            sys.exit(1)
    else:
        print("Usage: python verify_extraction.py <file_path>")
        print("\\nExample PDF files to test:")
        print("  - test_documents/BuildingA_Network_Layout.pdf")
        print("  - test_documents/BuildingB_Network_Layout.pdf")
        print("  - test_documents/BuildingC_Network_Layout.pdf")
'''
    
    script_path = Path("verify_extraction.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ Verification script created: {script_path}")
    return str(script_path)

def main():
    """Main function to setup debug logging and create verification tools"""
    print("🔍 Extraction Debug Setup")
    print("=" * 50)
    
    # Setup debug logging
    debug_config = setup_debug_logging(
        enable_extraction_debug=True,
        save_dumps=True
    )
    
    # Create verification script
    verification_script = create_verification_script()
    
    print(f"\n🎯 Ready for Extraction Debugging!")
    print(f"=" * 50)
    print(f"📋 What's been set up:")
    print(f"  ✅ Environment variables for debug mode")
    print(f"  ✅ Comprehensive logging configuration")
    print(f"  ✅ Debug log files in data/logs/")
    print(f"  ✅ Extraction dump files enabled")
    print(f"  ✅ Verification script: {verification_script}")
    
    print(f"\n🧪 How to test:")
    print(f"  1. Test PDF with Azure Vision:")
    print(f"     python {verification_script} test_documents/BuildingA_Network_Layout.pdf")
    print(f"  ")
    print(f"  2. Test Excel processing:")
    print(f"     python {verification_script} <your_excel_file.xlsx>")
    print(f"  ")
    print(f"  3. Check logs:")
    print(f"     tail -f {debug_config['debug_log']}")
    
    print(f"\n📁 Debug files will be saved to:")
    print(f"  - General logs: {debug_config['general_log']}")
    print(f"  - Debug logs: {debug_config['debug_log']}")
    print(f"  - Extraction dumps: {debug_config['logs_dir']}/debug_*_extract_*.json")
    print(f"  - Processor results: {debug_config['logs_dir']}/debug_processor_result_*.json")

if __name__ == "__main__":
    main() 