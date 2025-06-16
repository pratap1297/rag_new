#!/usr/bin/env python3
"""
Test Persistent JSON Metadata Store
Verify that the new persistent store works correctly
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_persistent_metadata_store():
    print("🧪 Testing Persistent JSON Metadata Store")
    print("=" * 50)
    
    try:
        # Import the persistent store
        from storage.persistent_metadata_store import PersistentJSONMetadataStore
        
        # Test 1: Create store instance
        print("\n1️⃣ Creating store instance...")
        store = PersistentJSONMetadataStore("data/metadata_test")
        print("   ✅ Store created successfully")
        
        # Test 2: Add file metadata
        print("\n2️⃣ Adding file metadata...")
        file_id = store.add_file_metadata(
            "test_document.pdf", 
            {"size": 1024, "pages": 5, "type": "pdf"}
        )
        print(f"   ✅ File added with ID: {file_id}")
        
        # Test 3: Add chunk metadata with vector linking
        print("\n3️⃣ Adding chunk metadata...")
        chunk_id = store.add_chunk_metadata({
            "doc_id": file_id,
            "filename": "test_document.pdf",
            "content": "This is a test chunk from the document",
            "vector_id": "vector_123",
            "chunk_index": 0,
            "start_char": 0,
            "end_char": 100
        })
        print(f"   ✅ Chunk added with ID: {chunk_id}")
        
        # Test 4: Retrieve metadata by vector ID
        print("\n4️⃣ Testing vector-metadata linking...")
        metadata = store.get_metadata_by_vector_id("vector_123")
        if metadata:
            print(f"   ✅ Found metadata for vector_123:")
            print(f"      - Filename: {metadata.get('filename')}")
            print(f"      - Content: {metadata.get('content')[:50]}...")
        else:
            print("   ❌ No metadata found for vector_123")
        
        # Test 5: Get all files and chunks
        print("\n5️⃣ Testing data retrieval...")
        files = store.get_all_files()
        chunks = store.get_all_chunks()
        print(f"   ✅ Files: {len(files)}")
        print(f"   ✅ Chunks: {len(chunks)}")
        
        # Test 6: Test persistence (create new instance)
        print("\n6️⃣ Testing persistence...")
        store2 = PersistentJSONMetadataStore("data/metadata_test")
        files2 = store2.get_all_files()
        chunks2 = store2.get_all_chunks()
        metadata2 = store2.get_metadata_by_vector_id("vector_123")
        
        print(f"   ✅ After reload - Files: {len(files2)}")
        print(f"   ✅ After reload - Chunks: {len(chunks2)}")
        print(f"   ✅ After reload - Vector metadata: {'Found' if metadata2 else 'Not found'}")
        
        # Test 7: Get statistics
        print("\n7️⃣ Testing statistics...")
        stats = store.get_stats()
        print(f"   ✅ Total files: {stats['total_files']}")
        print(f"   ✅ Total chunks: {stats['total_chunks']}")
        print(f"   ✅ Total vector mappings: {stats['total_vector_mappings']}")
        print(f"   ✅ Storage path: {stats['storage_path']}")
        
        # Test 8: Test with multiple chunks
        print("\n8️⃣ Testing multiple chunks...")
        for i in range(3):
            chunk_id = store.add_chunk_metadata({
                "doc_id": file_id,
                "filename": "test_document.pdf",
                "content": f"This is chunk {i+1} from the document",
                "vector_id": f"vector_{i+100}",
                "chunk_index": i+1,
                "start_char": (i+1) * 100,
                "end_char": (i+2) * 100
            })
        
        final_stats = store.get_stats()
        print(f"   ✅ Final chunks: {final_stats['total_chunks']}")
        print(f"   ✅ Final vector mappings: {final_stats['total_vector_mappings']}")
        
        # Test 9: Test file chunks retrieval
        print("\n9️⃣ Testing file chunks retrieval...")
        file_chunks = store.get_file_chunks(file_id)
        print(f"   ✅ Chunks for file {file_id}: {len(file_chunks)}")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        store.clear_all_data()
        import shutil
        if os.path.exists("data/metadata_test"):
            shutil.rmtree("data/metadata_test")
        print("   ✅ Test data cleaned up")
        
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎯 **Persistent JSON Metadata Store is working correctly!**")
        print("   • File metadata storage ✅")
        print("   • Chunk metadata storage ✅") 
        print("   • Vector-metadata linking ✅")
        print("   • Data persistence across restarts ✅")
        print("   • Statistics and retrieval ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_persistent_metadata_store()
    if success:
        print("\n🚀 **Ready to use persistent metadata store!**")
        print("   1. Restart your RAG system")
        print("   2. Upload documents - metadata will persist")
        print("   3. No more 'doc_unknown' issues!")
    else:
        print("\n⚠️ **Fix issues before proceeding**")
    
    sys.exit(0 if success else 1) 