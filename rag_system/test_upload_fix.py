#!/usr/bin/env python3
"""
Test script to verify that upload fix preserves original filenames
"""

import os
import sys
import tempfile

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.storage.faiss_store import FAISSStore
from src.ingestion.embedder import Embedder
from src.ingestion.ingestion_engine import IngestionEngine
from src.ingestion.chunker import Chunker
from src.storage.persistent_metadata_store import PersistentJSONMetadataStore

def test_upload_fix():
    """Test that upload fix preserves original filenames"""
    
    print("🧪 Testing Upload Fix")
    print("=" * 50)
    
    # Initialize components
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Initialize embedder
    embedder = Embedder(
        provider=config.embedding.provider,
        model_name=config.embedding.model_name,
        device=config.embedding.device,
        batch_size=config.embedding.batch_size,
        api_key=config.embedding.api_key,
        endpoint=os.getenv('AZURE_EMBEDDINGS_ENDPOINT') if config.embedding.provider == 'azure' else None
    )
    
    # Initialize FAISS store
    faiss_store = FAISSStore(
        index_path="data/vectors/index.faiss",
        dimension=config.embedding.dimension
    )
    
    # Initialize metadata store
    metadata_store = PersistentJSONMetadataStore("data/metadata")
    
    # Initialize chunker
    chunker = Chunker(
        chunk_size=1000,
        chunk_overlap=200,
        use_semantic=True
    )
    
    # Initialize ingestion engine
    ingestion_engine = IngestionEngine(
        chunker=chunker,
        embedder=embedder,
        faiss_store=faiss_store,
        metadata_store=metadata_store,
        config_manager=config_manager
    )
    
    # Create a test Excel file content
    excel_content = """Manager Roster

Name: Maria Garcia
Position: Floor Manager
Location: Building A - Administrative Offices
Phone: 555-0102
Email: mgarcia@company.com
Start Date: July 22, 2020
Certification: Six Sigma
Shift: Day
Backup Contact: Michael Brown (Tuesdays, Day shift 6AM-2PM)

This information is from the Manager Roster Excel sheet."""
    
    # Create a temporary file (simulating upload)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp_file:
        tmp_file.write(excel_content)
        tmp_file_path = tmp_file.name
    
    # Simulate upload metadata (like the API would create)
    original_filename = "Manager_Roster_2024.xlsx"
    upload_metadata = {
        "filename": original_filename,
        "original_filename": original_filename,  # This is what we added to the API
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "file_size": len(excel_content),
        "upload_source": "web_interface"
    }
    
    print(f"📄 Original filename: {original_filename}")
    print(f"📄 Temporary file path: {tmp_file_path}")
    print(f"📋 Upload metadata: {upload_metadata}")
    
    try:
        # Process the file (simulating the API upload process)
        result = ingestion_engine.ingest_file(tmp_file_path, upload_metadata)
        
        print(f"\n✅ Ingestion result: {result}")
        
        # Test search to see if original filename is preserved
        test_query = "Maria Garcia manager information"
        query_embedding = embedder.embed_text(test_query)
        search_results = faiss_store.search_with_metadata(query_embedding, k=3)
        
        print(f"\n🔍 Search results for '{test_query}':")
        print(f"📋 Found {len(search_results)} results")
        
        for i, result in enumerate(search_results, 1):
            print(f"\n  Result {i}:")
            metadata = result.get('metadata', {})
            print(f"    original_filename: {metadata.get('original_filename', 'N/A')}")
            print(f"    filename: {result.get('filename', 'N/A')}")
            print(f"    file_path: {metadata.get('file_path', 'N/A')}")
            print(f"    text preview: {result.get('text', 'N/A')[:100]}...")
            
            # Check if original filename is preserved
            if metadata.get('original_filename') == original_filename:
                print(f"    ✅ Original filename preserved correctly!")
            else:
                print(f"    ❌ Original filename not preserved. Expected: {original_filename}, Got: {metadata.get('original_filename')}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
    
    print("\n✅ Upload fix test completed!")

if __name__ == "__main__":
    test_upload_fix() 