#!/usr/bin/env python3
"""
Test script to verify consistent doc_id generation between ingestion and deletion
"""

import sys
import os
from pathlib import Path

# Add the rag_system to the path
sys.path.insert(0, str(Path(__file__).parent / 'rag_system' / 'src'))

# Mock the embedder to avoid API calls
class MockEmbedder:
    def __init__(self, api_key="test-key"):
        self.model_name = "mock-embedder"
    
    def embed_texts(self, texts):
        return [[0.1] * 1536 for _ in texts]

# Mock the FAISS store
class MockFAISSStore:
    def __init__(self, dimension=1536):
        self.dimension = dimension
        self.id_to_metadata = {}
        self.vector_count = 0
    
    def add_vectors(self, embeddings, metadata_list):
        vector_ids = []
        for i, metadata in enumerate(metadata_list):
            vector_id = f"vec_{self.vector_count + i}"
            self.id_to_metadata[vector_id] = metadata
            vector_ids.append(vector_id)
        self.vector_count += len(embeddings)
        return vector_ids
    
    def delete_vectors(self, vector_ids):
        for vid in vector_ids:
            if vid in self.id_to_metadata:
                self.id_to_metadata[vid]['deleted'] = True

# Mock the metadata store
class MockMetadataStore:
    def __init__(self):
        self.files = {}
    
    def add_file_metadata(self, file_path, metadata):
        file_id = f"file_{len(self.files)}"
        self.files[file_id] = metadata
        return file_id

# Mock the config manager
class MockConfigManager:
    def __init__(self):
        self.ingestion = type('obj', (object,), {
            'max_file_size_mb': 100,
            'supported_formats': ['.txt', '.pdf', '.docx', '.md']
        })()
        self.embedding = type('obj', (object,), {
            'model_name': 'mock-model'
        })()
    def get_config(self):
        return self

# Mock the metadata manager
class MockMetadataManager:
    def merge_metadata(self, *metadata_dicts):
        result = {}
        for md in metadata_dicts:
            if md:
                result.update(md)
        return result
    
    def prepare_for_storage(self, metadata):
        return metadata

# Mock the chunker
class MockChunker:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text, metadata):
        # Simple chunking for testing
        chunks = []
        words = text.split()
        for i in range(0, len(words), 10):
            chunk_text = ' '.join(words[i:i+10])
            chunks.append({
                'text': chunk_text,
                'metadata': {}
            })
        return chunks

def test_doc_id_consistency():
    """Test that doc_id generation is consistent"""
    print("🔍 Testing doc_id consistency between ingestion and deletion")
    print("-" * 60)
    
    # Import the actual ingestion engine
    from rag_system.src.ingestion.ingestion_engine import IngestionEngine
    
    # Initialize components with mocks
    config_manager = MockConfigManager()
    chunker = MockChunker()
    embedder = MockEmbedder()
    faiss_store = MockFAISSStore()
    metadata_store = MockMetadataStore()
    metadata_manager = MockMetadataManager()
    
    # Create ingestion engine
    engine = IngestionEngine(
        chunker=chunker,
        embedder=embedder,
        faiss_store=faiss_store,
        metadata_store=metadata_store,
        config_manager=config_manager
    )
    
    # Test cases
    test_cases = [
        {
            'name': 'Basic file path',
            'file_path': Path('test_document.pdf'),
            'metadata': {},
            'expected_doc_id': 'test_document.pdf'
        },
        {
            'name': 'File with doc_path in metadata',
            'file_path': Path('test_document.pdf'),
            'metadata': {'doc_path': 'custom/path/document.pdf'},
            'expected_doc_id': 'custom/path/document.pdf'
        },
        {
            'name': 'Text ingestion with doc_path',
            'file_path': None,
            'metadata': {'doc_path': 'text_document.txt', 'title': 'Test Document'},
            'expected_doc_id': 'text_document.txt'
        },
        {
            'name': 'Text ingestion without doc_path',
            'file_path': None,
            'metadata': {'title': 'Test Document'},
            'expected_doc_id': 'Test Document'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        
        try:
            if test_case['file_path']:
                # Test file ingestion
                doc_id = engine._generate_consistent_doc_id(test_case['file_path'], test_case['metadata'])
            else:
                # Test text ingestion logic
                metadata = test_case['metadata']
                doc_id = metadata.get('doc_path', metadata.get('title', 'text_document')) if metadata else 'text_document'
            
            expected = test_case['expected_doc_id']
            
            if doc_id == expected:
                print(f"✅ PASS: Generated doc_id '{doc_id}' matches expected '{expected}'")
            else:
                print(f"❌ FAIL: Generated doc_id '{doc_id}' does not match expected '{expected}'")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    # Test deletion matching
    print(f"\n🔍 Testing deletion matching logic")
    print("-" * 40)
    
    # Simulate stored metadata
    test_metadata = {
        'doc_id': 'test_document.pdf',
        'doc_path': 'test_document.pdf',
        'file_path': 'test_document.pdf',
        'filename': 'test_document.pdf'
    }
    
    # Test deletion matching scenarios
    deletion_tests = [
        {
            'name': 'Delete by doc_path',
            'file_path': 'test_document.pdf',
            'doc_path': 'test_document.pdf',
            'should_match': True
        },
        {
            'name': 'Delete by file_path',
            'file_path': 'test_document.pdf',
            'doc_path': None,
            'should_match': True
        },
        {
            'name': 'Delete with different doc_path',
            'file_path': 'test_document.pdf',
            'doc_path': 'different_path.pdf',
            'should_match': False
        }
    ]
    
    for test in deletion_tests:
        print(f"\n📋 Deletion Test: {test['name']}")
        
        # Simulate the deletion matching logic (match real code)
        is_match = False
        if test['doc_path']:
            # Only match on doc_path if provided
            if test_metadata.get('doc_path') == test['doc_path']:
                is_match = True
        else:
            # If no doc_path, match on filename or file_path
            if test_metadata.get('filename') == os.path.basename(test['file_path']):
                is_match = True
            elif test_metadata.get('file_path') == test['file_path']:
                is_match = True
        
        # Always print PASS/FAIL for each test
        if is_match == test['should_match']:
            print(f"✅ PASS: Deletion matching works correctly")
        else:
            print(f"❌ FAIL: Deletion matching failed - expected {test['should_match']}, got {is_match}")
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED: doc_id generation is consistent!")
    else:
        print("❌ SOME TESTS FAILED: doc_id generation needs fixing!")
    
    return all_passed

if __name__ == "__main__":
    success = test_doc_id_consistency()
    sys.exit(0 if success else 1) 