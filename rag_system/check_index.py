#!/usr/bin/env python3
"""
Check what's in the FAISS index and metadata store
"""

import sys
import os
sys.path.append('src')

from src.core.dependency_container import DependencyContainer, register_core_services

def main():
    print("🔍 Checking FAISS Index and Metadata Store")
    print("=" * 50)
    
    try:
        # Initialize the system
        container = DependencyContainer()
        register_core_services(container)
        
        # Get stores
        faiss_store = container.get('faiss_store')
        metadata_store = container.get('metadata_store')
        
        print("✅ Stores initialized")
        
        # Check FAISS index
        print(f"\n📊 FAISS Index Stats:")
        index_info = faiss_store.get_index_info()
        print(f"  - Total vectors: {index_info.get('total_vectors', 0)}")
        print(f"  - Dimension: {index_info.get('dimension', 0)}")
        print(f"  - Index type: {index_info.get('index_type', 'N/A')}")
        print(f"  - Index exists: {index_info.get('index_exists', False)}")
        
        # Check metadata store
        print(f"\n📋 Metadata Store Stats:")
        all_chunks = metadata_store.get_all_chunks()
        all_files = metadata_store.get_all_files()
        print(f"  - Total files: {len(all_files)}")
        print(f"  - Total chunks: {len(all_chunks)}")
        
        # Show sample chunks
        if all_chunks:
            print(f"\n📄 Sample Chunks:")
            for i, chunk in enumerate(all_chunks[:5]):
                print(f"  {i+1}. ID: {chunk.get('chunk_id', 'N/A')[:8]}...")
                print(f"     - File: {chunk.get('filename', 'N/A')}")
                print(f"     - Type: {chunk.get('source_type', 'N/A')}")
                print(f"     - Record ID: {chunk.get('record_id', 'N/A')}")
                if 'is_servicenow_data' in chunk:
                    print(f"     - ServiceNow: {chunk.get('is_servicenow_data', 'N/A')}")
                print()
        
        # Search for ServiceNow specifically
        servicenow_docs = [
            chunk for chunk in all_chunks
            if chunk.get('is_servicenow_data', False) or 
               'servicenow' in chunk.get('source_type', '').lower() or
               'INC' in str(chunk.get('record_id', ''))
        ]
        
        print(f"🎫 ServiceNow Documents Found: {len(servicenow_docs)}")
        
        if servicenow_docs:
            print(f"\n📋 ServiceNow Incidents:")
            for chunk in servicenow_docs:
                record_id = chunk.get('record_id', 'N/A')
                file_name = chunk.get('filename', 'N/A')
                source_type = chunk.get('source_type', 'N/A')
                chunk_id = chunk.get('chunk_id', 'N/A')
                print(f"  - {record_id} (ID: {chunk_id[:8]}...)")
                print(f"    File: {file_name}")
                print(f"    Type: {source_type}")
                print()
        
        # Test a simple search
        print(f"\n🔍 Testing Simple Search:")
        if index_info.get('total_vectors', 0) > 0:
            embedder = container.get('embedder')
            test_query = "incident"
            query_embedding = embedder.embed_text(test_query)
            search_results = faiss_store.search_with_metadata(
                query_vector=query_embedding,
                k=5
            )
            print(f"  Query: '{test_query}'")
            print(f"  Results: {len(search_results)}")
            
            for i, result in enumerate(search_results[:3], 1):
                metadata = result.get('metadata', {})
                score = result.get('similarity_score', 0)
                print(f"    {i}. Score: {score:.3f}")
                print(f"       Record: {metadata.get('record_id', 'N/A')}")
                print(f"       Text: {result.get('text', '')[:100]}...")
                print()
        else:
            print("  No vectors in index to search")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 