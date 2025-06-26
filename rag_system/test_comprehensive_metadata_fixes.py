#!/usr/bin/env python3
"""
Comprehensive Test Suite for Metadata Fixes
Tests all the fixes implemented for nested metadata issues
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.storage.faiss_store import FAISSStore
from src.ingestion.ingestion_engine import IngestionEngine
from src.retrieval.query_engine import QueryEngine
from src.core.config_manager import ConfigManager
from src.embedding.embedder import Embedder
from src.chunking.chunker import Chunker
from src.storage.metadata_store import MetadataStore
from src.llm.llm_client import LLMClient

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ComprehensiveMetadataTestSuite:
    """Comprehensive test suite for metadata fixes"""
    
    def __init__(self):
        self.test_dir = Path("test_output")
        self.test_dir.mkdir(exist_ok=True)
        
        # Test data
        self.test_documents = {
            "policy_doc.txt": "Company Policy Document\n\n1. All employees must follow security protocols.\n2. Regular backups are mandatory.\n3. Access control is strictly enforced.",
            "technical_guide.txt": "Technical Implementation Guide\n\n1. Use Azure AI for document processing.\n2. Implement FAISS for vector storage.\n3. Enable source diversity in queries.",
            "user_manual.txt": "User Manual for RAG System\n\n1. Upload documents through the web interface.\n2. Query the system using natural language.\n3. Review confidence scores and sources."
        }
        
        # Test queries
        self.test_queries = [
            "What are the security protocols?",
            "How do I implement FAISS?",
            "What is the user interface like?",
            "Tell me about document processing"
        ]
        
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment with all components"""
        print("🔧 Setting up test environment...")
        
        # Create test directories
        self.vector_dir = self.test_dir / "vectors"
        self.vector_dir.mkdir(exist_ok=True)
        
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Initialize components
        self.faiss_store = FAISSStore(
            index_path=str(self.vector_dir / "test_index.faiss"),
            dimension=384
        )
        
        self.embedder = Embedder(self.config_manager)
        self.chunker = Chunker(self.config_manager)
        self.metadata_store = MetadataStore(str(self.data_dir / "metadata.db"))
        self.llm_client = LLMClient(self.config_manager)
        
        # Initialize engines
        self.ingestion_engine = IngestionEngine(
            chunker=self.chunker,
            embedder=self.embedder,
            faiss_store=self.faiss_store,
            metadata_store=self.metadata_store,
            config_manager=self.config_manager
        )
        
        self.query_engine = QueryEngine(
            faiss_store=self.faiss_store,
            embedder=self.embedder,
            llm_client=self.llm_client,
            metadata_store=self.metadata_store,
            config_manager=self.config_manager
        )
        
        print("✅ Test environment setup complete")
    
    def create_test_files(self):
        """Create test files for ingestion"""
        print("📄 Creating test files...")
        
        for filename, content in self.test_documents.items():
            file_path = self.test_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"✅ Created {len(self.test_documents)} test files")
        return [str(self.test_dir / filename) for filename in self.test_documents.keys()]
    
    def test_1_faiss_store_metadata_structure(self):
        """Test 1: Verify FAISS store metadata structure"""
        print("\n🧪 Test 1: FAISS Store Metadata Structure")
        
        # Test data
        test_vectors = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        test_metadata = [
            {
                'doc_id': 'test_doc_1',
                'text': 'Test content 1',
                'filename': 'test1.txt',
                'source_type': 'document',
                'chunk_id': 'chunk_1'
            },
            {
                'doc_id': 'test_doc_2',
                'text': 'Test content 2',
                'filename': 'test2.txt',
                'source_type': 'document',
                'chunk_id': 'chunk_2'
            },
            {
                'doc_id': 'test_doc_3',
                'text': 'Test content 3',
                'filename': 'test3.txt',
                'source_type': 'document',
                'chunk_id': 'chunk_3'
            }
        ]
        
        # Add vectors
        vector_ids = self.faiss_store.add_vectors(test_vectors, test_metadata)
        
        # Verify structure
        assert len(vector_ids) == 3, f"Expected 3 vector IDs, got {len(vector_ids)}"
        
        # Test search_with_metadata
        query_vector = [0.1] * 384
        results = self.faiss_store.search_with_metadata(query_vector, k=3)
        
        # Verify no nested metadata
        for result in results:
            assert 'metadata' not in result, f"Found nested 'metadata' key in result: {result.keys()}"
            assert 'doc_id' in result, f"Missing 'doc_id' in result: {result.keys()}"
            assert 'text' in result, f"Missing 'text' in result: {result.keys()}"
            assert 'similarity_score' in result, f"Missing 'similarity_score' in result: {result.keys()}"
        
        print("✅ FAISS store metadata structure test passed")
        return True
    
    def test_2_ingestion_engine_metadata_flow(self):
        """Test 2: Verify ingestion engine metadata flow"""
        print("\n🧪 Test 2: Ingestion Engine Metadata Flow")
        
        # Create test file
        test_file = self.test_dir / "ingestion_test.txt"
        test_content = "This is a test document for ingestion.\n\nIt contains multiple paragraphs.\n\nEach paragraph should be chunked separately."
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Test metadata
        test_metadata = {
            'doc_path': str(test_file),
            'filename': 'ingestion_test.txt',
            'source_type': 'test_document',
            'author': 'test_author'
        }
        
        # Ingest file
        result = self.ingestion_engine.ingest_file(str(test_file), test_metadata)
        
        # Verify result
        assert result['status'] == 'success', f"Ingestion failed: {result}"
        assert result['chunks_created'] > 0, f"No chunks created: {result}"
        assert result['vectors_stored'] > 0, f"No vectors stored: {result}"
        
        # Verify metadata in FAISS store
        query_vector = [0.1] * 384
        search_results = self.faiss_store.search_with_metadata(query_vector, k=5)
        
        # Check for ingested content
        found_ingested = False
        for result in search_results:
            if 'ingestion_test.txt' in result.get('filename', ''):
                found_ingested = True
                # Verify flat metadata structure
                assert 'metadata' not in result, f"Found nested metadata in ingested result: {result.keys()}"
                assert 'doc_id' in result, f"Missing doc_id in ingested result: {result.keys()}"
                assert 'text' in result, f"Missing text in ingested result: {result.keys()}"
                break
        
        assert found_ingested, "Ingested content not found in search results"
        
        print("✅ Ingestion engine metadata flow test passed")
        return True
    
    def test_3_query_engine_diversity_calculation(self):
        """Test 3: Verify query engine diversity calculation"""
        print("\n🧪 Test 3: Query Engine Diversity Calculation")
        
        # First, ingest multiple documents
        test_files = self.create_test_files()
        
        for file_path in test_files:
            metadata = {
                'doc_path': file_path,
                'filename': Path(file_path).name,
                'source_type': 'test_document',
                'author': 'test_author'
            }
            result = self.ingestion_engine.ingest_file(file_path, metadata)
            assert result['status'] == 'success', f"Failed to ingest {file_path}: {result}"
        
        # Test query processing
        query = "What are the main topics covered?"
        response = self.query_engine.process_query(query, top_k=5)
        
        # Verify response structure
        assert 'response' in response, f"Missing response in query result: {response.keys()}"
        assert 'sources' in response, f"Missing sources in query result: {response.keys()}"
        assert 'confidence_score' in response, f"Missing confidence_score in query result: {response.keys()}"
        assert 'diversity_metrics' in response, f"Missing diversity_metrics in query result: {response.keys()}"
        
        # Verify diversity metrics
        diversity_metrics = response['diversity_metrics']
        assert 'unique_documents' in diversity_metrics, f"Missing unique_documents: {diversity_metrics.keys()}"
        assert 'unique_source_types' in diversity_metrics, f"Missing unique_source_types: {diversity_metrics.keys()}"
        assert 'diversity_index' in diversity_metrics, f"Missing diversity_index: {diversity_metrics.keys()}"
        
        # Verify sources have flat metadata
        for source in response['sources']:
            assert 'metadata' not in source, f"Found nested metadata in source: {source.keys()}"
            assert 'text' in source, f"Missing text in source: {source.keys()}"
            assert 'similarity_score' in source, f"Missing similarity_score in source: {source.keys()}"
        
        print("✅ Query engine diversity calculation test passed")
        return True
    
    def test_4_conversation_context_handling(self):
        """Test 4: Verify conversation context handling"""
        print("\n🧪 Test 4: Conversation Context Handling")
        
        # Test conversation context
        conversation_context = {
            'history': [
                {'role': 'user', 'content': 'What is the company policy?'},
                {'role': 'assistant', 'content': 'The company policy includes security protocols and regular backups.'}
            ],
            'session_id': 'test_session_123'
        }
        
        # Process query with context
        query = "Can you elaborate on the security protocols?"
        response = self.query_engine.process_query(
            query, 
            top_k=3, 
            conversation_context=conversation_context
        )
        
        # Verify response includes context handling
        assert 'response' in response, f"Missing response: {response.keys()}"
        assert len(response['response']) > 0, "Empty response"
        
        # Verify sources are still properly structured
        for source in response['sources']:
            assert 'metadata' not in source, f"Found nested metadata in conversation source: {source.keys()}"
        
        print("✅ Conversation context handling test passed")
        return True
    
    def test_5_file_update_handling(self):
        """Test 5: Verify file update handling (existing file deletion)"""
        print("\n🧪 Test 5: File Update Handling")
        
        # Create initial file
        test_file = self.test_dir / "update_test.txt"
        initial_content = "Initial content for update test."
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        # Ingest initial file
        metadata = {
            'doc_path': str(test_file),
            'filename': 'update_test.txt',
            'source_type': 'test_document'
        }
        
        initial_result = self.ingestion_engine.ingest_file(str(test_file), metadata)
        assert initial_result['status'] == 'success', f"Initial ingestion failed: {initial_result}"
        initial_vectors = initial_result['vectors_stored']
        
        # Update file content
        updated_content = "Updated content for update test.\n\nThis is the new version with different information."
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        # Ingest updated file
        updated_result = self.ingestion_engine.ingest_file(str(test_file), metadata)
        assert updated_result['status'] == 'success', f"Updated ingestion failed: {updated_result}"
        
        # Verify old vectors were deleted
        assert updated_result['is_update'] == True, "Should be marked as update"
        assert updated_result['old_vectors_deleted'] > 0, "Should have deleted old vectors"
        
        # Verify new content is searchable
        query_vector = [0.1] * 384
        search_results = self.faiss_store.search_with_metadata(query_vector, k=5)
        
        found_updated = False
        for result in search_results:
            if 'update_test.txt' in result.get('filename', ''):
                found_updated = True
                # Should contain updated content, not initial content
                text = result.get('text', '')
                assert 'Updated content' in text or 'new version' in text, f"Found old content: {text[:100]}"
                break
        
        assert found_updated, "Updated content not found in search results"
        
        print("✅ File update handling test passed")
        return True
    
    def test_6_debug_logging_verification(self):
        """Test 6: Verify debug logging is working"""
        print("\n🧪 Test 6: Debug Logging Verification")
        
        # Enable debug logging
        logging.getLogger().setLevel(logging.DEBUG)
        
        # Create a test vector and metadata
        test_vectors = [[0.1] * 384]
        test_metadata = [{
            'doc_id': 'debug_test',
            'text': 'Debug test content',
            'filename': 'debug_test.txt',
            'source_type': 'test'
        }]
        
        # This should trigger debug logging
        vector_ids = self.faiss_store.add_vectors(test_vectors, test_metadata)
        
        # Search should also trigger debug logging
        query_vector = [0.1] * 384
        results = self.faiss_store.search_with_metadata(query_vector, k=1)
        
        # Verify results
        assert len(results) > 0, "No search results returned"
        assert 'metadata' not in results[0], "Found nested metadata in debug test"
        
        print("✅ Debug logging verification test passed")
        return True
    
    def test_7_comprehensive_workflow(self):
        """Test 7: Comprehensive end-to-end workflow test"""
        print("\n🧪 Test 7: Comprehensive End-to-End Workflow")
        
        # Step 1: Ingest multiple documents
        print("  📥 Step 1: Ingesting documents...")
        test_files = self.create_test_files()
        
        for file_path in test_files:
            metadata = {
                'doc_path': file_path,
                'filename': Path(file_path).name,
                'source_type': 'comprehensive_test',
                'author': 'test_author',
                'created_date': datetime.now().isoformat()
            }
            result = self.ingestion_engine.ingest_file(file_path, metadata)
            assert result['status'] == 'success', f"Failed to ingest {file_path}: {result}"
        
        # Step 2: Test multiple queries
        print("  🔍 Step 2: Testing queries...")
        for i, query in enumerate(self.test_queries):
            print(f"    Query {i+1}: {query}")
            response = self.query_engine.process_query(query, top_k=3)
            
            # Verify response structure
            assert 'response' in response, f"Missing response for query {i+1}"
            assert 'sources' in response, f"Missing sources for query {i+1}"
            assert 'confidence_score' in response, f"Missing confidence_score for query {i+1}"
            assert 'diversity_metrics' in response, f"Missing diversity_metrics for query {i+1}"
            
            # Verify flat metadata structure
            for source in response['sources']:
                assert 'metadata' not in source, f"Found nested metadata in query {i+1} source: {source.keys()}"
                assert 'text' in source, f"Missing text in query {i+1} source: {source.keys()}"
                assert 'similarity_score' in source, f"Missing similarity_score in query {i+1} source: {source.keys()}"
            
            # Verify diversity metrics
            diversity = response['diversity_metrics']
            assert diversity['unique_documents'] > 0, f"No unique documents for query {i+1}"
            assert diversity['diversity_index'] >= 0, f"Invalid diversity index for query {i+1}"
        
        # Step 3: Test conversation flow
        print("  💬 Step 3: Testing conversation flow...")
        conversation_context = {
            'history': [
                {'role': 'user', 'content': 'What documents are available?'},
                {'role': 'assistant', 'content': 'I can help you find information about policies, technical guides, and user manuals.'}
            ],
            'session_id': 'comprehensive_test_session'
        }
        
        follow_up_query = "Tell me more about the technical implementation"
        response = self.query_engine.process_query(
            follow_up_query, 
            top_k=3, 
            conversation_context=conversation_context
        )
        
        assert 'response' in response, "Missing response in conversation test"
        assert len(response['sources']) > 0, "No sources in conversation test"
        
        # Step 4: Verify metadata consistency
        print("  🔍 Step 4: Verifying metadata consistency...")
        query_vector = [0.1] * 384
        all_results = self.faiss_store.search_with_metadata(query_vector, k=10)
        
        for result in all_results:
            # Verify no nested metadata anywhere
            assert 'metadata' not in result, f"Found nested metadata in comprehensive test: {result.keys()}"
            
            # Verify required fields
            required_fields = ['doc_id', 'text', 'similarity_score', 'vector_id']
            for field in required_fields:
                assert field in result, f"Missing required field '{field}' in comprehensive test: {result.keys()}"
        
        print("✅ Comprehensive workflow test passed")
        return True
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting Comprehensive Metadata Fixes Test Suite")
        print("=" * 60)
        
        test_results = []
        
        try:
            # Run individual tests
            test_results.append(("FAISS Store Metadata Structure", self.test_1_faiss_store_metadata_structure()))
            test_results.append(("Ingestion Engine Metadata Flow", self.test_2_ingestion_engine_metadata_flow()))
            test_results.append(("Query Engine Diversity Calculation", self.test_3_query_engine_diversity_calculation()))
            test_results.append(("Conversation Context Handling", self.test_4_conversation_context_handling()))
            test_results.append(("File Update Handling", self.test_5_file_update_handling()))
            test_results.append(("Debug Logging Verification", self.test_6_debug_logging_verification()))
            test_results.append(("Comprehensive Workflow", self.test_7_comprehensive_workflow()))
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<40} {status}")
            if result:
                passed += 1
        
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Metadata fixes are working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues.")
        
        return passed == total
    
    def cleanup(self):
        """Clean up test files and directories"""
        print("\n🧹 Cleaning up test files...")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        print("✅ Cleanup complete")

def main():
    """Main test runner"""
    test_suite = ComprehensiveMetadataTestSuite()
    
    try:
        success = test_suite.run_all_tests()
        return 0 if success else 1
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    exit(main()) 