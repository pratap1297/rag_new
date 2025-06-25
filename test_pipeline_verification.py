#!/usr/bin/env python3
"""
Pipeline Verification Test Script
Demonstrates the complete pipeline verification workflow with visualization
"""

import sys
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def test_pipeline_verification():
    """Test the complete pipeline verification workflow"""
    print("🔍 RAG PIPELINE VERIFICATION TEST")
    print("=" * 50)
    
    try:
        # Import system components
        from rag_system.src.core.dependency_container import DependencyContainer, register_core_services, set_dependency_container
        from rag_system.src.core.pipeline_verifier import PipelineVerifier
        from rag_system.src.core.verified_ingestion_engine import VerifiedIngestionEngine
        
        print("\n1️⃣ Initializing System Components...")
        # Create and initialize dependency container
        container = DependencyContainer()
        register_core_services(container)
        set_dependency_container(container)
        print("✅ Dependency container initialized")
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        if not ingestion_engine:
            print("❌ Ingestion engine not available")
            return False
        print("✅ Ingestion engine loaded")
        
        print("\n2️⃣ Creating Verification System...")
        # Create pipeline verifier with debug mode
        verifier = PipelineVerifier(debug_mode=True, save_intermediate=True)
        print("✅ Pipeline verifier created")
        
        # Create verified ingestion engine
        verified_engine = VerifiedIngestionEngine(ingestion_engine, verifier)
        print("✅ Verified ingestion engine created")
        
        print("\n3️⃣ Creating Test Document...")
        # Create a test document
        test_dir = Path("test_data")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "pipeline_test_document.txt"
        test_content = """
        # Pipeline Verification Test Document
        
        This is a test document for demonstrating the RAG pipeline verification system.
        
        ## Section 1: Introduction
        The pipeline verification system provides comprehensive monitoring and validation
        of each stage in the document ingestion process.
        
        ## Section 2: Features
        - Real-time monitoring of pipeline stages
        - Comprehensive error checking and validation
        - Interactive web dashboard for visualization
        - WebSocket-based live updates
        - Detailed verification reports
        
        ## Section 3: Technical Details
        The system verifies:
        1. File validation (existence, size, permissions)
        2. Processor selection and initialization
        3. Content extraction and parsing
        4. Text chunking with quality checks
        5. Embedding generation and validation
        6. Vector storage in FAISS
        7. Metadata persistence
        
        ## Section 4: Benefits
        - Improved reliability and debugging capabilities
        - Better visibility into the ingestion process
        - Early detection of issues and bottlenecks
        - Enhanced system monitoring and maintenance
        """
        
        test_file.write_text(test_content.strip())
        print(f"✅ Test document created: {test_file} ({test_file.stat().st_size} bytes)")
        
        print("\n4️⃣ Setting up Real-time Monitoring...")
        verification_events = []
        
        def event_callback(event):
            verification_events.append(event)
            event_type = event.get('type', 'unknown')
            data = event.get('data', {})
            timestamp = event.get('timestamp', datetime.now().isoformat())
            
            if event_type == 'stage_started':
                stage = data.get('stage', 'unknown').replace('_', ' ').title()
                print(f"   🔄 {timestamp}: Started {stage}")
            elif event_type == 'stage_completed':
                stage = data.get('stage', 'unknown').replace('_', ' ').title()
                status = data.get('status', 'unknown')
                duration = data.get('duration_ms', 0)
                print(f"   ✅ {timestamp}: Completed {stage} ({status}) - {duration:.1f}ms")
            elif event_type == 'error_occurred':
                stage = data.get('stage', 'unknown')
                error = data.get('error_message', 'Unknown error')
                print(f"   ❌ {timestamp}: Error in {stage}: {error}")
        
        verified_engine.add_verification_callback(event_callback)
        print("✅ Real-time monitoring configured")
        
        print("\n5️⃣ Running Verified Ingestion...")
        start_time = datetime.now()
        
        result = verified_engine.ingest_file_with_verification(
            str(test_file),
            metadata={
                "source": "test_verification",
                "document_type": "test_document",
                "created_by": "pipeline_verification_test"
            }
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n6️⃣ Verification Results (Duration: {duration:.2f}s)")
        print("=" * 50)
        
        if result["success"]:
            print("🎉 VERIFICATION SUCCESSFUL!")
            
            # Display verification summary
            verification_results = result.get("verification_results", {})
            total_checks = 0
            passed_checks = 0
            failed_checks = 0
            warning_checks = 0
            
            for stage, checks in verification_results.items():
                stage_name = stage.replace('_', ' ').title()
                print(f"\n📋 {stage_name}:")
                
                for check in checks:
                    total_checks += 1
                    status = check.get('status', 'unknown')
                    check_name = check.get('check_name', 'unknown').replace('_', ' ').title()
                    message = check.get('message', 'No message')
                    duration_ms = check.get('duration_ms', 0)
                    
                    if status == 'passed':
                        passed_checks += 1
                        icon = "✅"
                    elif status == 'failed':
                        failed_checks += 1
                        icon = "❌"
                    elif status == 'warning':
                        warning_checks += 1
                        icon = "⚠️"
                    else:
                        icon = "❓"
                    
                    print(f"   {icon} {check_name}: {message} ({duration_ms:.1f}ms)")
            
            print(f"\n📊 Verification Summary:")
            print(f"   • Total Checks: {total_checks}")
            print(f"   • Passed: {passed_checks}")
            print(f"   • Failed: {failed_checks}")
            print(f"   • Warnings: {warning_checks}")
            
            # Display ingestion results
            ingestion_result = result.get("ingestion_result", {})
            if ingestion_result:
                print(f"\n📄 Ingestion Results:")
                print(f"   • File ID: {ingestion_result.get('file_id', 'N/A')}")
                print(f"   • Chunks Created: {ingestion_result.get('chunks_created', 0)}")
                print(f"   • Vectors Stored: {ingestion_result.get('vectors_stored', 0)}")
                print(f"   • Processor Used: {ingestion_result.get('processor_used', 'N/A')}")
        
        else:
            print("❌ VERIFICATION FAILED!")
            error = result.get("error", "Unknown error")
            print(f"   Error: {error}")
            
            if "error_trace" in result:
                print(f"   Error Trace: {len(result['error_trace'])} entries")
        
        print(f"\n7️⃣ Real-time Events Captured: {len(verification_events)}")
        
        # Save results for analysis
        results_file = test_dir / f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_metadata": {
                    "test_file": str(test_file),
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration
                },
                "verification_result": result,
                "captured_events": verification_events
            }, f, indent=2, default=str)
        
        print(f"📁 Results saved to: {results_file}")
        
        return result["success"]
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_api_usage():
    """Demonstrate how to use the verification API endpoints"""
    print("\n" + "=" * 60)
    print("🌐 API USAGE DEMONSTRATION")
    print("=" * 60)
    
    print("\nThe pipeline verification system provides the following API endpoints:")
    print("\n📡 WebSocket Endpoint:")
    print("   ws://localhost:8000/api/verification/ws")
    print("   - Real-time verification updates")
    print("   - Event streaming during ingestion")
    
    print("\n🔍 Validation Endpoints:")
    print("   POST /api/verification/validate-file")
    print("   POST /api/verification/test-extraction")
    print("   POST /api/verification/test-chunking")
    print("   POST /api/verification/test-embedding")
    
    print("\n⚙️ Ingestion Endpoints:")
    print("   POST /api/verification/ingest-with-verification")
    print("   GET /api/verification/session/{session_id}")
    print("   GET /api/verification/sessions")
    
    print("\n📊 Analysis Endpoints:")
    print("   GET /api/verification/performance-stats")
    print("   POST /api/verification/analyze-chunks/{session_id}")
    print("   POST /api/verification/similarity-test")
    
    print("\n🔧 Debug Endpoints:")
    print("   GET /api/verification/debug/file-access/{file_path}")
    print("   GET /api/verification/health")
    
    print("\n📱 Web Dashboard:")
    print("   Access the verification dashboard at:")
    print("   http://localhost:8000/api/verification/dashboard")
    print("   - Interactive pipeline visualization")
    print("   - Real-time progress monitoring")
    print("   - Detailed verification results")
    print("   - WebSocket-based live updates")
    print("   - File upload and drag-and-drop")
    
    print("\n🚀 Getting Started:")
    print("   1. Start the RAG system API server")
    print("   2. Open the dashboard in your browser")
    print("   3. Upload a file for verification")
    print("   4. Watch real-time progress updates")
    print("   5. Review detailed verification results")
    
    print("\n💡 Example API Usage:")
    print("""
   # Validate a file
   curl -X POST "http://localhost:8000/api/verification/validate-file" \\
        -H "Content-Type: application/json" \\
        -d '{"file_path": "/path/to/document.pdf"}'
   
   # Start verified ingestion
   curl -X POST "http://localhost:8000/api/verification/ingest-with-verification" \\
        -H "Content-Type: application/json" \\
        -d '{"file_path": "/path/to/document.pdf", "metadata": {"source": "api"}}'
   
   # Check session status
   curl "http://localhost:8000/api/verification/session/{session_id}"
   """)

def cleanup_test_files():
    """Clean up test files created during testing"""
    print("\n🧹 Cleaning up test files...")
    test_dir = Path("test_data")
    
    if test_dir.exists():
        for file in test_dir.glob("pipeline_test_*"):
            try:
                file.unlink()
                print(f"   🗑️ Removed: {file}")
            except Exception as e:
                print(f"   ⚠️ Could not remove {file}: {e}")
        
        for file in test_dir.glob("verification_results_*"):
            try:
                file.unlink()
                print(f"   🗑️ Removed: {file}")
            except Exception as e:
                print(f"   ⚠️ Could not remove {file}: {e}")

def main():
    """Main test function"""
    print("🔬 RAG PIPELINE VERIFICATION SYSTEM TEST")
    print("=" * 60)
    print("This script demonstrates the complete pipeline verification workflow")
    print("with real-time monitoring and interactive visualization capabilities.")
    print("=" * 60)
    
    try:
        # Run the verification test
        success = test_pipeline_verification()
        
        # Demonstrate API usage
        demonstrate_api_usage()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 PIPELINE VERIFICATION TEST COMPLETED SUCCESSFULLY!")
            print("\n✨ Key Features Demonstrated:")
            print("   • Comprehensive stage-by-stage verification")
            print("   • Real-time event monitoring and callbacks")
            print("   • Detailed error checking and validation")
            print("   • Interactive web dashboard with live updates")
            print("   • Complete API endpoint coverage")
            print("   • WebSocket-based real-time communication")
            
            print("\n🌟 Next Steps:")
            print("   1. Start your RAG system API server")
            print("   2. Open http://localhost:8000/api/verification/dashboard")
            print("   3. Upload files and monitor verification in real-time")
            print("   4. Use the API endpoints for programmatic access")
        else:
            print("❌ PIPELINE VERIFICATION TEST FAILED")
            print("Please check the error messages above and ensure:")
            print("   • All dependencies are installed")
            print("   • The RAG system is properly configured")
            print("   • You're running from the project root directory")
        
        print("=" * 60)
        
        # Cleanup option
        cleanup_choice = input("\n🧹 Clean up test files? (y/N): ").lower().strip()
        if cleanup_choice == 'y':
            cleanup_test_files()
            print("✅ Cleanup completed")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 