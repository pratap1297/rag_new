#!/usr/bin/env python3
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
        
        print("\n🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        
        # Process file
        print(f"\n📄 Processing file: {file_path}")
        result = ingestion_engine.ingest_file(file_path)
        
        # Display results
        print(f"\n📊 Processing Results:")
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
        
        print(f"\n✅ Verification complete!")
        print(f"  - Detailed results: {output_path}")
        print(f"  - Debug logs: {debug_config['debug_log']}")
        print(f"  - Extraction dumps in: {debug_config['logs_dir']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = verify_extraction(sys.argv[1])
        if result:
            print(f"\n🎯 Quick Test Recommendation:")
            print(f"   To test Azure Vision integration, try:")
            print(f"   python verify_extraction.py test_documents/BuildingA_Network_Layout.pdf")
        else:
            sys.exit(1)
    else:
        print("Usage: python verify_extraction.py <file_path>")
        print("\nExample PDF files to test:")
        print("  - test_documents/BuildingA_Network_Layout.pdf")
        print("  - test_documents/BuildingB_Network_Layout.pdf")
        print("  - test_documents/BuildingC_Network_Layout.pdf")
