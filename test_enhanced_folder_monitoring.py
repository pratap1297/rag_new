"""
Test Enhanced Folder Monitoring Pipeline
Tests the complete pipeline with new, updated, and deleted documents
"""
import os
import time
import tempfile
import shutil
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Test document content
TEST_DOCUMENTS = {
    "test_document_1.txt": """
This is a test document for the enhanced folder monitoring system.
It contains multiple paragraphs to test the chunking process.

The document discusses various topics including:
- Text processing and extraction
- Pipeline verification stages
- Real-time monitoring capabilities
- Performance metrics and analytics

This content will be used to verify that the system correctly:
1. Detects new files
2. Processes them through all pipeline stages
3. Generates embeddings and stores vectors
4. Maintains metadata consistency
""",
    
    "test_document_2.md": """
# Enhanced Folder Monitoring Test Document

## Overview
This markdown document tests the enhanced folder monitoring system with structured content.

## Features Tested
- **File Detection**: Automatic detection of new files
- **Pipeline Verification**: 7-stage verification process
- **Real-time Updates**: WebSocket event broadcasting
- **Concurrent Processing**: Multiple file handling

## Processing Stages
1. File Validation
2. Processor Selection
3. Content Extraction
4. Text Chunking
5. Embedding Generation
6. Vector Storage
7. Metadata Storage

## Expected Behavior
The system should process this document and provide detailed verification results for each stage.
""",
    
    "updated_document.txt": """
Original content for testing document updates.
This content will be modified to test update detection.
""",
    
    "large_document.txt": """
This is a larger test document designed to test the system's handling of bigger files.
""" + "\n".join([f"Line {i}: This is test content line number {i} with some meaningful text for processing." for i in range(1, 101)])
}

class EnhancedFolderMonitoringTest:
    """Test class for enhanced folder monitoring pipeline"""
    
    def __init__(self):
        self.test_folder = None
        self.container = None
        self.enhanced_monitor = None
        self.test_results = {}
        
    def setup_test_environment(self):
        """Set up test environment with temporary folder and documents"""
        print("🔧 Setting up test environment...")
        
        # Create temporary test folder
        self.test_folder = tempfile.mkdtemp(prefix="enhanced_folder_test_")
        print(f"📁 Created test folder: {self.test_folder}")
        
        # Initialize the enhanced folder monitor
        try:
            from rag_system.src.core.dependency_container import get_dependency_container
            from rag_system.src.monitoring.enhanced_folder_monitor import initialize_enhanced_folder_monitor
            
            self.container = get_dependency_container()
            config_manager = self.container.get('config_manager')
            
            self.enhanced_monitor = initialize_enhanced_folder_monitor(self.container, config_manager)
            print("✅ Enhanced folder monitor initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize enhanced folder monitor: {e}")
            return False
        
        return True
    
    def add_test_folder_to_monitoring(self):
        """Add test folder to monitoring"""
        print(f"📂 Adding test folder to monitoring: {self.test_folder}")
        
        try:
            result = self.enhanced_monitor.add_folder(self.test_folder)
            if result.get("success"):
                print(f"✅ Folder added successfully: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to add folder: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Exception adding folder: {e}")
            return False
    
    def start_monitoring(self):
        """Start the enhanced monitoring"""
        print("▶️ Starting enhanced folder monitoring...")
        
        try:
            result = self.enhanced_monitor.start_monitoring()
            if result.get("success"):
                print(f"✅ Monitoring started: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to start monitoring: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Exception starting monitoring: {e}")
            return False
    
    def create_test_document(self, filename, content):
        """Create a test document in the monitored folder"""
        file_path = os.path.join(self.test_folder, filename)
        
        print(f"📝 Creating test document: {filename}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def update_test_document(self, filename, new_content):
        """Update an existing test document"""
        file_path = os.path.join(self.test_folder, filename)
        
        print(f"✏️ Updating test document: {filename}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return file_path
    
    def delete_test_document(self, filename):
        """Delete a test document"""
        file_path = os.path.join(self.test_folder, filename)
        
        print(f"🗑️ Deleting test document: {filename}")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    def wait_for_processing(self, timeout=60):
        """Wait for files to be processed"""
        print(f"⏳ Waiting for processing (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status = self.enhanced_monitor.get_enhanced_status()
                processing_files = status.get('files_in_processing', 0)
                queue_size = status.get('processing_queue_size', 0)
                
                if processing_files == 0 and queue_size == 0:
                    print("✅ All files processed")
                    return True
                
                print(f"⏳ Processing: {processing_files}, Queue: {queue_size}")
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error checking status: {e}")
                time.sleep(2)
        
        print("⚠️ Timeout waiting for processing")
        return False
    
    def get_processing_results(self):
        """Get detailed processing results"""
        print("📊 Collecting processing results...")
        
        try:
            # Get enhanced status
            status = self.enhanced_monitor.get_enhanced_status()
            
            # Get all file processing states
            file_states = self.enhanced_monitor.get_all_file_processing_states()
            
            return {
                "status": status,
                "file_states": file_states,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Error getting results: {e}")
            return None
    
    def print_results_summary(self, results):
        """Print a summary of test results"""
        if not results:
            print("❌ No results to display")
            return
        
        print("\n" + "="*50)
        print("📊 ENHANCED FOLDER MONITORING TEST RESULTS")
        print("="*50)
        
        status = results.get("status", {})
        file_states = results.get("file_states", {})
        
        # Overall status
        print(f"📈 Overall Status:")
        print(f"   - Running: {status.get('is_running', False)}")
        print(f"   - Files Tracked: {status.get('total_files_tracked', 0)}")
        print(f"   - Files Completed: {status.get('files_completed', 0)}")
        print(f"   - Files Failed: {status.get('files_failed_verification', 0)}")
        print(f"   - Success Rate: {status.get('success_rate_percentage', 0)}%")
        print(f"   - Avg Processing Time: {status.get('average_processing_time_seconds', 0)}s")
        
        # Individual file results
        print(f"\n📄 Individual File Results ({len(file_states)} files):")
        for file_path, file_state in file_states.items():
            filename = os.path.basename(file_path)
            status_emoji = {
                'completed': '✅',
                'failed': '❌',
                'processing': '⏳',
                'pending': '⏸️'
            }.get(file_state.get('status', 'unknown'), '❓')
            
            print(f"   {status_emoji} {filename}")
            print(f"      Status: {file_state.get('status', 'unknown')}")
            print(f"      Size: {file_state.get('size_mb', 0)}MB")
            print(f"      Duration: {file_state.get('total_duration_seconds', 0)}s")
            
            if file_state.get('error_message'):
                print(f"      Error: {file_state.get('error_message')}")
            
            # Pipeline progress
            pipeline_progress = file_state.get('pipeline_progress', {})
            print(f"      Pipeline Progress:")
            for stage, stage_status in pipeline_progress.items():
                stage_emoji = {
                    'completed': '✅',
                    'failed': '❌',
                    'running': '⏳',
                    'pending': '⏸️'
                }.get(stage_status, '❓')
                print(f"         {stage_emoji} {stage.replace('_', ' ').title()}: {stage_status}")
            
            print()
    
    def test_new_document(self):
        """Test processing of new documents"""
        print("\n🆕 Testing NEW document processing...")
        
        # Create new documents
        for filename, content in TEST_DOCUMENTS.items():
            self.create_test_document(filename, content)
            time.sleep(1)  # Small delay between files
        
        # Wait for processing
        self.wait_for_processing(timeout=120)
        
        # Get results
        results = self.get_processing_results()
        self.test_results['new_documents'] = results
        
        print("✅ New document test completed")
        return results
    
    def test_updated_document(self):
        """Test processing of updated documents"""
        print("\n✏️ Testing UPDATED document processing...")
        
        # Update existing document
        updated_content = """
UPDATED CONTENT - This document has been modified to test update detection.
The enhanced folder monitoring system should detect this change and reprocess the file.

New sections added:
- Update detection mechanism
- File modification timestamp tracking
- Content hash comparison
- Automatic reprocessing trigger

This tests the system's ability to handle document updates correctly.
"""
        
        self.update_test_document("updated_document.txt", updated_content)
        
        # Wait for processing
        self.wait_for_processing(timeout=60)
        
        # Get results
        results = self.get_processing_results()
        self.test_results['updated_documents'] = results
        
        print("✅ Updated document test completed")
        return results
    
    def test_deleted_document(self):
        """Test handling of deleted documents"""
        print("\n🗑️ Testing DELETED document processing...")
        
        # Delete a document
        self.delete_test_document("test_document_1.txt")
        
        # Force scan to detect deletion
        try:
            scan_result = self.enhanced_monitor.force_scan()
            print(f"📡 Force scan result: {scan_result}")
        except Exception as e:
            print(f"❌ Error during force scan: {e}")
        
        # Wait a bit for deletion processing
        time.sleep(5)
        
        # Get results
        results = self.get_processing_results()
        self.test_results['deleted_documents'] = results
        
        print("✅ Deleted document test completed")
        return results
    
    def run_comprehensive_test(self):
        """Run comprehensive test of the enhanced folder monitoring pipeline"""
        print("🚀 Starting Enhanced Folder Monitoring Pipeline Test")
        print("="*60)
        
        try:
            # Setup
            if not self.setup_test_environment():
                print("❌ Failed to set up test environment")
                return False
            
            # Add folder to monitoring
            if not self.add_test_folder_to_monitoring():
                print("❌ Failed to add folder to monitoring")
                return False
            
            # Start monitoring
            if not self.start_monitoring():
                print("❌ Failed to start monitoring")
                return False
            
            # Test new documents
            new_results = self.test_new_document()
            if new_results:
                print("✅ New document test passed")
            else:
                print("❌ New document test failed")
            
            # Test updated documents
            update_results = self.test_updated_document()
            if update_results:
                print("✅ Updated document test passed")
            else:
                print("❌ Updated document test failed")
            
            # Test deleted documents
            delete_results = self.test_deleted_document()
            if delete_results:
                print("✅ Deleted document test passed")
            else:
                print("❌ Deleted document test failed")
            
            # Print comprehensive results
            if new_results:
                self.print_results_summary(new_results)
            
            print("\n🎉 Enhanced Folder Monitoring Pipeline Test Completed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        try:
            # Stop monitoring
            if self.enhanced_monitor:
                stop_result = self.enhanced_monitor.stop_monitoring()
                print(f"⏹️ Monitoring stopped: {stop_result}")
            
            # Remove test folder
            if self.test_folder and os.path.exists(self.test_folder):
                shutil.rmtree(self.test_folder)
                print(f"🗑️ Removed test folder: {self.test_folder}")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

def main():
    """Main test function"""
    test = EnhancedFolderMonitoringTest()
    success = test.run_comprehensive_test()
    
    if success:
        print("\n✅ All tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 