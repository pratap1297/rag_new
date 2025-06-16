#!/usr/bin/env python3
"""
Fix Metadata Store Configuration
This script fixes the metadata store to use persistent storage instead of memory-only
"""
import sys
import os
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def fix_metadata_store():
    print("🔧 Fixing Metadata Store Configuration")
    print("=" * 50)
    
    try:
        # 1. Clear existing test data
        print("🧹 Clearing test data...")
        
        # Clear FAISS index
        faiss_path = "data/vectors/faiss_index.bin"
        if os.path.exists(faiss_path):
            os.remove(faiss_path)
            print(f"   ✅ Removed FAISS index: {faiss_path}")
        
        # Clear metadata files
        metadata_path = "data/metadata"
        if os.path.exists(metadata_path):
            shutil.rmtree(metadata_path)
            print(f"   ✅ Removed metadata directory: {metadata_path}")
        
        # 2. Update dependency container
        print("\n🔧 Updating dependency container...")
        
        # Read current file
        container_file = "src/core/dependency_container.py"
        with open(container_file, 'r') as f:
            content = f.read()
        
        # Replace the memory metadata store with persistent one
        old_factory = '''def create_metadata_store(container: DependencyContainer):
    """Factory for MemoryMetadataStore"""
    from .memory_store import MemoryMetadataStore
    # Use default path to avoid circular dependency with config_manager
    return MemoryMetadataStore("data/metadata")'''
        
        new_factory = '''def create_metadata_store(container: DependencyContainer):
    """Factory for MetadataStore"""
    from ..storage.metadata_store import MetadataStore
    from .json_store import JSONStore
    
    # Create a simple JSON store factory
    def json_store_factory(path):
        return JSONStore(str(path))
    
    config_manager = container.get('config_manager')
    return MetadataStore(config_manager, json_store_factory)'''
        
        if old_factory in content:
            content = content.replace(old_factory, new_factory)
            
            # Write back
            with open(container_file, 'w') as f:
                f.write(content)
            print(f"   ✅ Updated {container_file}")
        else:
            print(f"   ⚠️ Factory not found in {container_file}")
        
        # 3. Test the fix
        print("\n🧪 Testing the fix...")
        
        # Initialize system with new configuration
        from src.core.system_init import initialize_system
        container = initialize_system()
        
        metadata_store = container.get('metadata_store')
        print(f"   ✅ Metadata store type: {type(metadata_store).__name__}")
        
        # Check if it has the right methods
        if hasattr(metadata_store, 'search_files'):
            print(f"   ✅ Has search_files method")
        else:
            print(f"   ❌ Missing search_files method")
            
        if hasattr(metadata_store, 'search_chunks'):
            print(f"   ✅ Has search_chunks method")
        else:
            print(f"   ❌ Missing search_chunks method")
        
        print("\n✅ Metadata store fix completed!")
        print("\nNext steps:")
        print("1. Restart the RAG system")
        print("2. Upload some documents")
        print("3. Test queries - they should now show proper document names")
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_metadata_store() 