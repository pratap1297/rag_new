#!/usr/bin/env python3
"""
Document Ingestion Test Module
Tests the document ingestion capabilities of the RAG system.
"""

import sys
import os
import json
from pathlib import Path
import shutil # For creating and cleaning up test files/dirs

# Add the project root and src to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'rag_system' / 'src'))

# Attempt to import necessary modules
try:
    from rag_system.src.ingestion.pipeline import IngestionPipeline
    from rag_system.src.ingestion.document_model import Document
    from rag_system.src.storage.vector_store_factory import VectorStoreFactory
    from rag_system.src.core.config_loader import get_config
    print("✅ Successfully imported RAG system modules.")
except ImportError as e:
    print(f"❌ Error importing RAG system modules: {e}")
    print("Please ensure the RAG system is correctly installed and paths are set up.")
    sys.exit(1)

# Configuration for tests
TEST_DATA_DIR = project_root / "test_data"
TEST_DB_PATH = TEST_DATA_DIR / "test_ingestion_vector_store.db"
TEST_FAISS_PATH = TEST_DATA_DIR / "test_ingestion_faiss.index"

def setup_test_environment():
    """Creates necessary directories and dummy files for testing."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Clean up previous test DB/Index if they exist
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    if TEST_FAISS_PATH.exists():
        TEST_FAISS_PATH.unlink()
    print(f"📂 Test data directory prepared at: {TEST_DATA_DIR}")

def cleanup_test_environment():
    """Removes temporary test files and directories."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    if TEST_FAISS_PATH.exists():
        TEST_FAISS_PATH.unlink()
    # Potentially remove other test files created within TEST_DATA_DIR
    # For now, just cleaning DB and Index
    print(f"🧹 Cleaned up test database and FAISS index.")

def test_ingestion_module():
    """Runs all document ingestion tests."""
    print("🧪 Starting Document Ingestion Tests")
    print("=" * 60)

    setup_test_environment()
    success_count = 0
    total_tests = 0

    # Initialize Ingestion Pipeline (assuming default config is sufficient for basic tests)
    # We might need to mock or use a specific test configuration for the vector store
    try:
        config = get_config()
        # Override vector store paths for testing
        config['vector_store']['db_path'] = str(TEST_DB_PATH)
        config['vector_store']['faiss_path'] = str(TEST_FAISS_PATH)
        
        vector_store = VectorStoreFactory.create_vector_store(config)
        ingestion_pipeline = IngestionPipeline(config=config, vector_store=vector_store)
        print("✅ Ingestion pipeline initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize ingestion pipeline: {e}")
        cleanup_test_environment()
        return False

    # --- Test Case: TC-ING-001: Basic File Format Support (.txt) ---
    total_tests += 1
    print("\n1️⃣ **TC-ING-001: Testing .txt File Ingestion**")
    txt_file_path = TEST_DATA_DIR / "sample.txt"
    try:
        with open(txt_file_path, "w") as f:
            f.write("This is a sample text file for testing ingestion.")
        print(f"   📄 Created dummy .txt file: {txt_file_path}")
        
        # Assuming ingest_file returns a Document object or similar identifier
        doc_id = ingestion_pipeline.ingest_file(str(txt_file_path))
        
        if doc_id:
            print(f"   ✅ .txt file ingested successfully. Document ID (or part of it): {str(doc_id)[:50]}")
            # Further checks: query vector store for the content
            retrieved_docs = vector_store.search_by_keyword("sample text file", top_k=1)
            if retrieved_docs and any(doc.metadata.get('doc_path') == str(txt_file_path) for doc in retrieved_docs):
                print("   ✅ Content verified in vector store.")
                success_count += 1
            else:
                print("   ❌ Content NOT verified in vector store.")
        else:
            print("   ❌ .txt file ingestion failed (no document ID returned).")
            
    except Exception as e:
        print(f"   ❌ Test case TC-ING-001 failed with error: {e}")
    finally:
        if txt_file_path.exists():
            txt_file_path.unlink()

    # --- Add more test cases here (e.g., for PDF, DOCX, XLSX) ---
    # Example for PDF (will require a dummy PDF and pdf processor)
    # total_tests += 1
    # print("\n2️⃣ **TC-ING-001: Testing .pdf File Ingestion**")
    # ... create dummy pdf, ingest, verify ...

    print("\n" + "=" * 60)
    print(f"🏁 Document Ingestion Tests Finished: {success_count}/{total_tests} passed.")
    
    cleanup_test_environment()
    return success_count == total_tests

if __name__ == "__main__":
    all_passed = test_ingestion_module()
    sys.exit(0 if all_passed else 1)
