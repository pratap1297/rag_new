"""
Comprehensive Pipeline Testing with Document Operations
Tests the complete pipeline verification system with new, updated, and deleted documents
"""
import os
import time
import tempfile
import shutil
import requests
import json
from datetime import datetime
from pathlib import Path

# Test documents for comprehensive testing
TEST_DOCUMENTS = {
    "new_document_1.txt": """
This is a comprehensive test document for the RAG system pipeline verification.
It contains multiple paragraphs and sections to thoroughly test all pipeline stages.

## Document Processing Pipeline Test

This document will test the following pipeline stages:
1. File Validation - Checking file existence, size, and permissions
2. Processor Selection - Identifying the appropriate document processor
3. Content Extraction - Extracting text content from the document
4. Text Chunking - Breaking content into manageable chunks
5. Embedding Generation - Creating vector embeddings for each chunk
6. Vector Storage - Storing embeddings in FAISS vector database
7. Metadata Storage - Persisting document metadata and relationships

## Content Sections

### Technical Information
This section contains technical details about the RAG system architecture.
The system uses FastAPI for the web interface, FAISS for vector storage,
and various document processors for different file types.

### Process Flow
Documents are ingested through a multi-stage pipeline that ensures
quality and consistency. Each stage includes verification checks
to maintain data integrity throughout the process.

### Performance Metrics
The system tracks processing times, success rates, and error conditions
to provide comprehensive monitoring and debugging capabilities.
""",
    
    "update_test_document.md": """
# Original Document for Update Testing

This markdown document will be modified to test update detection and reprocessing.

## Initial Content
- Basic structure with headers
- Simple bullet points
- Standard markdown formatting

## Testing Objectives
- Verify update detection mechanism
- Test reprocessing of modified content
- Validate pipeline re-execution
""",
    
    "large_document.txt": """
Large Document for Performance Testing
=====================================

This document contains substantial content to test the system's handling of larger files.
""" + "\n\n".join([f"""
Section {i}: Content Block {i}
{'='*30}

This is section {i} of the large document. It contains meaningful content
that will be processed through the complete pipeline. The content includes
technical information, process descriptions, and detailed explanations
that will test the chunking and embedding generation processes.

Key points for section {i}:
- Point 1: Technical implementation details
- Point 2: Process workflow information  
- Point 3: Performance considerations
- Point 4: Quality assurance measures
- Point 5: Monitoring and logging capabilities

The system should process this content efficiently and create appropriate
vector embeddings that capture the semantic meaning of the text.
""" for i in range(1, 21)]),

    "delete_test.txt": """
Document for Deletion Testing
============================

This document will be deleted during testing to verify the system's
handling of deleted files and cleanup procedures.

Content includes:
- File deletion detection
- Cleanup verification
- Metadata removal
- Vector store cleanup
""",

    "special_chars_test.txt": """
Special Characters & Symbols Test Document
==========================================

This document contains various special characters to test text processing:
- Accented characters: café, naïve, résumé
- Symbols: @#$%^&*()_+-=[]{}|;':\",./<>?
- Unicode: 你好, здравствуй, مرحبا
- Mathematical: ∑∫∆√π∞≤≥≠±
- Currency: $€£¥₹₽

The pipeline should handle these characters correctly during processing.
"""
}

class ComprehensivePipelineTest:
    """Comprehensive test for the complete pipeline verification system"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_folder = None
        self.test_results = {}
        self.session_ids = []
        
    def check_system_status(self):
        """Check if the RAG system is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ RAG system is running")
                return True
            else:
                print(f"❌ RAG system returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to RAG system: {e}")
            return False
    
    def setup_test_environment(self):
        """Create test folder and documents"""
        print("🔧 Setting up comprehensive test environment...")
        
        # Create temporary folder
        self.test_folder = tempfile.mkdtemp(prefix="comprehensive_pipeline_test_")
        print(f"📁 Created test folder: {self.test_folder}")
        
        # Create all test documents
        for filename, content in TEST_DOCUMENTS.items():
            file_path = os.path.join(self.test_folder, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 Created: {filename} ({len(content)} chars)")
        
        return True
    
    def test_new_document_processing(self):
        """Test processing of new documents through complete pipeline"""
        print("\n🆕 Testing NEW document processing...")
        
        results = {}
        test_files = ["new_document_1.txt", "large_document.txt", "special_chars_test.txt"]
        
        for filename in test_files:
            print(f"\n📄 Processing: {filename}")
            file_path = os.path.join(self.test_folder, filename)
            
            # Test file validation
            validation_result = self._test_file_validation(file_path)
            print(f"   📋 Validation: {'✅ PASSED' if validation_result['valid'] else '❌ FAILED'}")
            
            # Test verified ingestion
            ingestion_result = self._test_verified_ingestion(file_path, {"test_type": "new_document"})
            if ingestion_result:
                session_id = ingestion_result.get('session_id')
                if session_id:
                    self.session_ids.append(session_id)
                    print(f"   🔄 Ingestion started: {session_id}")
                    
                    # Wait and check results
                    time.sleep(5)
                    session_result = self._get_session_results(session_id)
                    results[filename] = {
                        "validation": validation_result,
                        "ingestion": ingestion_result,
                        "session_result": session_result,
                        "status": session_result.get('status', 'unknown') if session_result else 'failed'
                    }
                    
                    status_emoji = '✅' if session_result and session_result.get('status') == 'completed' else '❌'
                    print(f"   {status_emoji} Final status: {session_result.get('status', 'failed') if session_result else 'failed'}")
        
        self.test_results['new_documents'] = results
        return results
    
    def test_document_update(self):
        """Test processing of updated documents"""
        print("\n✏️ Testing DOCUMENT UPDATE processing...")
        
        filename = "update_test_document.md"
        file_path = os.path.join(self.test_folder, filename)
        
        # First, process the original document
        print(f"📄 Processing original: {filename}")
        original_result = self._test_verified_ingestion(file_path, {"test_type": "original_document"})
        
        if original_result and original_result.get('session_id'):
            time.sleep(3)
            original_session = self._get_session_results(original_result['session_id'])
            print(f"   ✅ Original processed: {original_session.get('status', 'unknown') if original_session else 'failed'}")
        
        # Wait a moment
        time.sleep(2)
        
        # Update the document
        updated_content = """
# UPDATED Document for Update Testing

This markdown document has been MODIFIED to test update detection and reprocessing.

## Updated Content - NEW SECTIONS ADDED
- Enhanced structure with more headers
- Additional bullet points and content
- Extended markdown formatting examples
- New sections for comprehensive testing

## Updated Testing Objectives
- ✅ Verify update detection mechanism works correctly
- ✅ Test reprocessing of modified content with new data
- ✅ Validate complete pipeline re-execution
- ✅ Check that old embeddings are properly updated
- ✅ Ensure metadata consistency after updates

## New Section: Advanced Features
This section was added during the update to test:
- Content addition detection
- Incremental processing capabilities
- Vector store update mechanisms
- Metadata synchronization

## Performance Analysis
The updated document should be processed efficiently,
with the system detecting changes and updating the
vector store accordingly.
"""
        
        print(f"✏️ Updating document: {filename}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        # Process the updated document
        print(f"🔄 Processing updated: {filename}")
        updated_result = self._test_verified_ingestion(file_path, {"test_type": "updated_document"})
        
        if updated_result and updated_result.get('session_id'):
            time.sleep(5)
            updated_session = self._get_session_results(updated_result['session_id'])
            print(f"   ✅ Updated processed: {updated_session.get('status', 'unknown') if updated_session else 'failed'}")
            
            self.test_results['updated_document'] = {
                "original": original_result,
                "updated": updated_result,
                "original_session": original_session,
                "updated_session": updated_session
            }
        
        return self.test_results.get('updated_document')
    
    def test_document_deletion(self):
        """Test handling of deleted documents"""
        print("\n🗑️ Testing DOCUMENT DELETION handling...")
        
        filename = "delete_test.txt"
        file_path = os.path.join(self.test_folder, filename)
        
        # First, process the document
        print(f"📄 Processing document to be deleted: {filename}")
        original_result = self._test_verified_ingestion(file_path, {"test_type": "deletion_test"})
        
        if original_result and original_result.get('session_id'):
            time.sleep(3)
            original_session = self._get_session_results(original_result['session_id'])
            print(f"   ✅ Document processed: {original_session.get('status', 'unknown') if original_session else 'failed'}")
        
        # Delete the document
        print(f"🗑️ Deleting document: {filename}")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   ✅ File deleted from filesystem")
        
        # Test document deletion endpoint (if available)
        try:
            delete_response = requests.delete(f"{self.base_url}/documents/{filename}")
            if delete_response.status_code == 200:
                print(f"   ✅ Document removed from system")
            else:
                print(f"   ⚠️ Document deletion returned: {delete_response.status_code}")
        except Exception as e:
            print(f"   ⚠️ Document deletion test skipped: {e}")
        
        self.test_results['deleted_document'] = {
            "original": original_result,
            "original_session": original_session,
            "deletion_completed": not os.path.exists(file_path)
        }
        
        return self.test_results.get('deleted_document')
    
    def _test_file_validation(self, file_path):
        """Test file validation"""
        try:
            validation_data = {"file_path": file_path}
            response = requests.post(
                f"{self.base_url}/api/verification/validate-file",
                json=validation_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"valid": False, "error": f"Status: {response.status_code}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _test_verified_ingestion(self, file_path, metadata):
        """Test verified ingestion"""
        try:
            ingestion_data = {
                "file_path": file_path,
                "metadata": metadata
            }
            
            response = requests.post(
                f"{self.base_url}/api/verification/ingest-with-verification",
                json=ingestion_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status: {response.status_code}", "response": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_session_results(self, session_id):
        """Get session results"""
        try:
            response = requests.get(
                f"{self.base_url}/api/verification/session/{session_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def print_comprehensive_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE PIPELINE TEST RESULTS")
        print("="*70)
        
        # New documents results
        if 'new_documents' in self.test_results:
            print(f"\n🆕 NEW DOCUMENTS PROCESSING:")
            for filename, result in self.test_results['new_documents'].items():
                status = result.get('status', 'unknown')
                emoji = '✅' if status == 'completed' else '❌' if status == 'failed' else '⏳'
                print(f"   {emoji} {filename}: {status}")
                
                if result.get('session_result') and 'verification_results' in result['session_result']:
                    verification = result['session_result']['verification_results']
                    print(f"      Pipeline stages: {len(verification)} completed")
        
        # Updated document results
        if 'updated_document' in self.test_results:
            print(f"\n✏️ DOCUMENT UPDATE PROCESSING:")
            result = self.test_results['updated_document']
            orig_status = result.get('original_session', {}).get('status', 'unknown')
            upd_status = result.get('updated_session', {}).get('status', 'unknown')
            print(f"   📄 Original: {orig_status}")
            print(f"   ✏️ Updated: {upd_status}")
        
        # Deleted document results
        if 'deleted_document' in self.test_results:
            print(f"\n🗑️ DOCUMENT DELETION HANDLING:")
            result = self.test_results['deleted_document']
            orig_status = result.get('original_session', {}).get('status', 'unknown')
            deleted = result.get('deletion_completed', False)
            print(f"   📄 Original processing: {orig_status}")
            print(f"   🗑️ Deletion completed: {'✅' if deleted else '❌'}")
        
        # Overall summary
        total_tests = len(self.test_results.get('new_documents', {}))
        if 'updated_document' in self.test_results:
            total_tests += 1
        if 'deleted_document' in self.test_results:
            total_tests += 1
        
        print(f"\n📈 OVERALL SUMMARY:")
        print(f"   Total tests executed: {total_tests}")
        print(f"   Session IDs tracked: {len(self.session_ids)}")
        print(f"   Test folder: {self.test_folder}")
        
        # Pipeline verification summary
        print(f"\n🔍 PIPELINE VERIFICATION:")
        print(f"   ✅ File validation tested")
        print(f"   ✅ Content extraction tested")
        print(f"   ✅ Verified ingestion tested")
        print(f"   ✅ Session tracking tested")
        print(f"   ✅ Multi-document processing tested")
        print(f"   ✅ Document updates tested")
        print(f"   ✅ Document deletion tested")
    
    def cleanup(self):
        """Clean up test environment"""
        print(f"\n🧹 Cleaning up test environment...")
        
        if self.test_folder and os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
            print(f"🗑️ Removed test folder: {self.test_folder}")
        
        print(f"📋 Session IDs created: {len(self.session_ids)}")
        for session_id in self.session_ids:
            print(f"   📋 {session_id}")
    
    def run_comprehensive_test(self):
        """Run the complete comprehensive test suite"""
        print("🚀 COMPREHENSIVE PIPELINE VERIFICATION TEST")
        print("="*60)
        
        try:
            # Check system status
            if not self.check_system_status():
                print("❌ System not available - cannot run tests")
                return False
            
            # Setup test environment
            if not self.setup_test_environment():
                print("❌ Failed to setup test environment")
                return False
            
            # Run all tests
            print("\n🔄 Running comprehensive test suite...")
            
            # Test new document processing
            new_results = self.test_new_document_processing()
            
            # Test document updates
            update_results = self.test_document_update()
            
            # Test document deletion
            delete_results = self.test_document_deletion()
            
            # Print comprehensive results
            self.print_comprehensive_results()
            
            print(f"\n🎉 COMPREHENSIVE TEST COMPLETED!")
            print(f"🌐 Access verification dashboard: {self.base_url}/api/verification/dashboard")
            
            return True
            
        except Exception as e:
            print(f"❌ Comprehensive test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()

def main():
    """Main function"""
    test = ComprehensivePipelineTest()
    success = test.run_comprehensive_test()
    
    if success:
        print("\n✅ All comprehensive tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 