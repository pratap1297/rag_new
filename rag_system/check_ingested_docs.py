#!/usr/bin/env python3
"""
Check what documents are ingested in the RAG system
"""
import sys
import os
sys.path.insert(0, 'src')

def check_ingested_documents():
    """Check what documents are currently ingested"""
    print("📚 Checking Ingested Documents")
    print("=" * 50)
    
    try:
        from src.core.dependency_container import DependencyContainer
        from src.core.system_init import register_core_services
        
        container = DependencyContainer()
        register_core_services(container)
        
        metadata_store = container.get('metadata_store')
        if metadata_store:
            files = metadata_store.get_all_files()
            print(f"📁 Total files in system: {len(files)}")
            
            if len(files) == 0:
                print("⚠️  No documents found in the system!")
                print("   This explains why Sarah Johnson information is not available.")
                return
            
            print("\n📄 Ingested Documents:")
            for i, file_info in enumerate(files[:20], 1):  # Show first 20 files
                filename = file_info.get('filename', 'Unknown')
                chunk_count = file_info.get('chunk_count', 0)
                file_path = file_info.get('file_path', 'Unknown')
                print(f"   {i}. {filename} ({chunk_count} chunks)")
                print(f"      Path: {file_path}")
                
            if len(files) > 20:
                print(f"   ... and {len(files) - 20} more files")
                
        else:
            print("❌ Could not access metadata store")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_ingested_documents() 