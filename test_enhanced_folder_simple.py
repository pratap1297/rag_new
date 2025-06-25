"""
Simple Test for Enhanced Folder Monitoring
Tests the pipeline with the running RAG system
"""
import os
import time
import tempfile
import shutil
import requests
import json
from pathlib import Path

# Test documents
TEST_DOCS = {
    "new_document.txt": """
This is a new test document for enhanced folder monitoring.
It contains sample content to test the complete pipeline process.

Topics covered:
- Document ingestion and processing
- Pipeline verification stages
- Real-time monitoring capabilities
- Performance tracking and metrics

The system should process this through all 7 pipeline stages:
1. File Validation
2. Processor Selection  
3. Content Extraction
4. Text Chunking
5. Embedding Generation
6. Vector Storage
7. Metadata Storage
""",
    
    "update_test.md": """
# Original Document for Update Testing

This document will be modified to test update detection and reprocessing.

## Initial Content
- Basic markdown structure
- Simple content for processing
""",
    
    "large_test.txt": "Large test document.\n" + "\n".join([f"Line {i}: Sample content for testing pipeline processing capabilities." for i in range(50)])
}

class SimpleEnhancedFolderTest:
    """Simple test for enhanced folder monitoring"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_folder = None
        
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
            print("💡 Make sure to start the RAG system first:")
            print("   python -m rag_system.src.main")
            return False
    
    def check_enhanced_monitoring(self):
        """Check if enhanced folder monitoring is available"""
        try:
            response = requests.get(f"{self.base_url}/api/enhanced-folder/status", timeout=5)
            if response.status_code == 200:
                print("✅ Enhanced folder monitoring is available")
                return True
            else:
                print(f"❌ Enhanced monitoring returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Enhanced monitoring not available: {e}")
            return False
    
    def setup_test_folder(self):
        """Create test folder and documents"""
        print("📁 Setting up test folder...")
        
        # Create temporary folder
        self.test_folder = tempfile.mkdtemp(prefix="enhanced_test_")
        print(f"Created: {self.test_folder}")
        
        # Create test documents
        for filename, content in TEST_DOCS.items():
            file_path = os.path.join(self.test_folder, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 Created: {filename}")
        
        return True
    
    def test_folder_monitoring_api(self):
        """Test the folder monitoring API endpoints"""
        print("\n🔍 Testing Enhanced Folder Monitoring API...")
        
        # Test 1: Check status
        print("1️⃣ Testing status endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/enhanced-folder/status")
            if response.status_code == 200:
                status = response.json()
                print(f"   ✅ Status: {status.get('status', 'unknown')}")
                if 'data' in status:
                    data = status['data']
                    print(f"   📊 Files tracked: {data.get('total_files_tracked', 0)}")
                    print(f"   📈 Success rate: {data.get('success_rate_percentage', 0)}%")
            else:
                print(f"   ❌ Status check failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Status check error: {e}")
        
        # Test 2: Check dashboard
        print("\n2️⃣ Testing dashboard endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/enhanced-folder/dashboard")
            if response.status_code == 200:
                print("   ✅ Dashboard is accessible")
                print(f"   🌐 Access at: {self.base_url}/api/enhanced-folder/dashboard")
            else:
                print(f"   ❌ Dashboard check failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Dashboard check error: {e}")
    
    def test_pipeline_verification_api(self):
        """Test the pipeline verification API"""
        print("\n🔍 Testing Pipeline Verification API...")
        
        # Test file validation
        test_file = os.path.join(self.test_folder, "new_document.txt")
        
        print("1️⃣ Testing file validation...")
        try:
            validation_data = {"file_path": test_file}
            response = requests.post(
                f"{self.base_url}/api/verification/validate-file",
                json=validation_data
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ File validation: {'valid' if result.get('valid') else 'invalid'}")
                checks = result.get('checks', [])
                for check in checks:
                    status = check.get('status', 'unknown')
                    message = check.get('message', 'No message')
                    emoji = '✅' if status == 'passed' else '❌' if status == 'failed' else '⚠️'
                    print(f"   {emoji} {message}")
            else:
                print(f"   ❌ Validation failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Validation error: {e}")
        
        # Test content extraction
        print("\n2️⃣ Testing content extraction...")
        try:
            extraction_data = {"file_path": test_file}
            response = requests.post(
                f"{self.base_url}/api/verification/test-extraction",
                json=extraction_data
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Processor: {result.get('processor', 'unknown')}")
                print(f"   📄 Chunks: {result.get('chunks', 0)}")
                print(f"   📊 Status: {result.get('status', 'unknown')}")
            else:
                print(f"   ❌ Extraction failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Extraction error: {e}")
    
    def test_verified_ingestion(self):
        """Test verified ingestion of a document"""
        print("\n🔍 Testing Verified Ingestion...")
        
        test_file = os.path.join(self.test_folder, "new_document.txt")
        
        try:
            ingestion_data = {
                "file_path": test_file,
                "metadata": {
                    "source": "enhanced_folder_test",
                    "test_type": "verified_ingestion"
                }
            }
            
            print(f"📤 Ingesting: {os.path.basename(test_file)}")
            response = requests.post(
                f"{self.base_url}/api/verification/ingest-with-verification",
                json=ingestion_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Ingestion started")
                
                # Check if we got a session ID
                if 'session_id' in result:
                    session_id = result['session_id']
                    print(f"   📋 Session ID: {session_id}")
                    
                    # Wait and check session status
                    print("   ⏳ Waiting for processing...")
                    time.sleep(10)
                    
                    session_response = requests.get(
                        f"{self.base_url}/api/verification/session/{session_id}"
                    )
                    
                    if session_response.status_code == 200:
                        session_data = session_response.json()
                        print(f"   📊 Session Status: {session_data.get('status', 'unknown')}")
                        
                        # Print verification results if available
                        if 'verification_results' in session_data:
                            results = session_data['verification_results']
                            print("   📋 Verification Results:")
                            for stage, stage_results in results.items():
                                print(f"      {stage}: {len(stage_results)} checks")
                
            else:
                print(f"   ❌ Ingestion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ingestion error: {e}")
    
    def cleanup(self):
        """Clean up test folder"""
        if self.test_folder and os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
            print(f"🧹 Cleaned up: {self.test_folder}")
    
    def run_test(self):
        """Run the complete test"""
        print("🚀 Enhanced Folder Monitoring - Simple Test")
        print("=" * 50)
        
        try:
            # Check system status
            if not self.check_system_status():
                return False
            
            # Check enhanced monitoring
            if not self.check_enhanced_monitoring():
                print("⚠️ Enhanced monitoring not available, testing basic verification...")
            
            # Setup test environment
            if not self.setup_test_folder():
                return False
            
            # Run tests
            self.test_folder_monitoring_api()
            self.test_pipeline_verification_api()
            self.test_verified_ingestion()
            
            print("\n✅ Test completed successfully!")
            print(f"\n🌐 Access the dashboards at:")
            print(f"   Pipeline Verification: {self.base_url}/api/verification/dashboard")
            print(f"   Enhanced Monitoring: {self.base_url}/api/enhanced-folder/dashboard")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        finally:
            self.cleanup()

def main():
    """Main function"""
    test = SimpleEnhancedFolderTest()
    success = test.run_test()
    
    if not success:
        print("\n💡 To test with actual folder monitoring:")
        print("1. Start the RAG system: python -m rag_system.src.main")
        print("2. Access the dashboard: http://localhost:8000/api/enhanced-folder/dashboard")
        print("3. Add a folder to monitor and upload documents")
        
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 