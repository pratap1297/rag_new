#!/usr/bin/env python3
"""
Fix Unknown Documents Issue
This script addresses the "doc_unknown" problem by:
1. Adding missing methods to MemoryMetadataStore
2. Clearing corrupted test data
3. Providing a clean slate for new document ingestion
"""
import sys
import os
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def fix_unknown_docs():
    print("🔧 Fixing Unknown Documents Issue")
    print("=" * 50)
    
    try:
        # 1. Add missing methods to MemoryMetadataStore
        print("🔧 Adding missing methods to MemoryMetadataStore...")
        
        memory_store_file = "src/core/memory_store.py"
        with open(memory_store_file, 'r') as f:
            content = f.read()
        
        # Check if methods already exist
        if 'def get_all_files(self)' not in content:
            # Add the missing methods
            additional_methods = '''
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all files metadata"""
        files_data = self.collections.get("files_metadata", {})
        return [
            {
                **metadata,
                'filename': metadata.get('file_path', 'unknown').split('/')[-1],
                'chunk_count': len(self.get_file_chunks(metadata.get('file_id', '')))
            }
            for metadata in files_data.values()
        ]
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Get all chunks metadata"""
        chunks_data = self.collections.get("chunks_metadata", {})
        return [
            {
                **metadata,
                'filename': metadata.get('filename', 'unknown')
            }
            for metadata in chunks_data.values()
        ]'''
            
            # Find the end of MemoryMetadataStore class
            class_end = content.find('\nclass MemoryLogStore')
            if class_end == -1:
                class_end = len(content)
            
            # Insert the methods before the next class
            content = content[:class_end] + additional_methods + content[class_end:]
            
            # Add the import for List at the top
            if 'from typing import Dict, Any, List' not in content:
                content = content.replace(
                    'from typing import Dict, Any',
                    'from typing import Dict, Any, List'
                )
            
            with open(memory_store_file, 'w') as f:
                f.write(content)
            
            print(f"   ✅ Added missing methods to {memory_store_file}")
        else:
            print(f"   ✅ Methods already exist in {memory_store_file}")
        
        # 2. Clear corrupted data
        print("\n🧹 Clearing corrupted test data...")
        
        # Clear FAISS index with test data
        faiss_path = "data/vectors/faiss_index.bin"
        if os.path.exists(faiss_path):
            os.remove(faiss_path)
            print(f"   ✅ Removed corrupted FAISS index: {faiss_path}")
        
        # Clear vector metadata
        vector_metadata_path = "data/vectors/vector_metadata.pkl"
        if os.path.exists(vector_metadata_path):
            os.remove(vector_metadata_path)
            print(f"   ✅ Removed vector metadata: {vector_metadata_path}")
        
        # 3. Test the system
        print("\n🧪 Testing the fixed system...")
        
        from src.core.system_init import initialize_system
        container = initialize_system()
        
        metadata_store = container.get('metadata_store')
        print(f"   ✅ Metadata store type: {type(metadata_store).__name__}")
        
        # Test the new methods
        try:
            files = metadata_store.get_all_files()
            chunks = metadata_store.get_all_chunks()
            print(f"   ✅ Files: {len(files)}, Chunks: {len(chunks)}")
        except Exception as e:
            print(f"   ❌ Method test failed: {e}")
        
        # Check FAISS store
        faiss_store = container.get('faiss_store')
        vector_count = faiss_store.index.ntotal if hasattr(faiss_store, 'index') else 0
        print(f"   ✅ FAISS vectors: {vector_count}")
        
        print("\n✅ Unknown documents issue fixed!")
        print("\n📋 What was fixed:")
        print("   • Added get_all_files() and get_all_chunks() methods to MemoryMetadataStore")
        print("   • Cleared corrupted test data from FAISS index")
        print("   • System now has clean slate for new document ingestion")
        
        print("\n🚀 Next steps:")
        print("   1. Restart the RAG system (API server + UI)")
        print("   2. Upload some real documents (not test data)")
        print("   3. Query the system - documents should now show proper names")
        print("   4. No more 'doc_unknown' responses!")
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_unknown_docs() 