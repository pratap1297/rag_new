#!/usr/bin/env python3
"""
Simple PDF Test - Step by Step
"""
import sys
import os
import time
from pathlib import Path

# Add the src directory to the path
sys.path.append('.')

def test_step_by_step():
    """Test each step of the ingestion process"""
    
    print("🔧 Step 1: Testing imports...")
    try:
        from src.core.dependency_container import DependencyContainer, register_core_services
        print("   ✅ Dependency container imported")
        
        from src.ingestion.ingestion_engine import IngestionEngine
        print("   ✅ Ingestion engine imported")
        
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    print("\n🔧 Step 2: Creating container...")
    try:
        container = DependencyContainer()
        print("   ✅ Container created")
        
        register_core_services(container)
        print("   ✅ Services registered")
        
    except Exception as e:
        print(f"   ❌ Container creation failed: {e}")
        return False
    
    print("\n🔧 Step 3: Getting individual components...")
    try:
        print("   📦 Getting config manager...")
        config_manager = container.get('config_manager')
        print("   ✅ Config manager obtained")
        
        print("   📦 Getting chunker...")
        chunker = container.get('chunker')
        print("   ✅ Chunker obtained")
        
        print("   📦 Getting embedder...")
        embedder = container.get('embedder')
        print("   ✅ Embedder obtained")
        
        print("   📦 Getting FAISS store...")
        faiss_store = container.get('faiss_store')
        print("   ✅ FAISS store obtained")
        
        print("   📦 Getting metadata store...")
        metadata_store = container.get('metadata_store')
        print("   ✅ Metadata store obtained")
        
    except Exception as e:
        print(f"   ❌ Component creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🔧 Step 4: Getting ingestion engine...")
    try:
        ingestion_engine = container.get('ingestion_engine')
        print("   ✅ Ingestion engine obtained")
        
    except Exception as e:
        print(f"   ❌ Ingestion engine creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🔧 Step 5: Testing PDF text extraction...")
    try:
        pdf_file = Path("test_documents/employee_handbook.pdf")
        text = ingestion_engine._extract_text(pdf_file)
        print(f"   ✅ Text extracted: {len(text)} characters")
        
    except Exception as e:
        print(f"   ❌ Text extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🔧 Step 6: Testing chunking...")
    try:
        chunks = chunker.chunk_text(text, {"file_path": str(pdf_file)})
        print(f"   ✅ Text chunked: {len(chunks)} chunks")
        
    except Exception as e:
        print(f"   ❌ Chunking failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🔧 Step 7: Testing embedding (first chunk only)...")
    try:
        if chunks:
            chunk_texts = [chunks[0]['text']]
            print(f"   📝 Embedding text: {len(chunk_texts[0])} characters")
            embeddings = embedder.embed_texts(chunk_texts)
            print(f"   ✅ Embeddings generated: {len(embeddings)} vectors")
        else:
            print("   ⚠️  No chunks to embed")
            
    except Exception as e:
        print(f"   ❌ Embedding failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🔧 Step 8: Testing full ingestion...")
    try:
        print("   📄 Starting full PDF ingestion...")
        result = ingestion_engine.ingest_file("test_documents/employee_handbook.pdf")
        print(f"   ✅ Full ingestion completed: {result}")
        
    except Exception as e:
        print(f"   ❌ Full ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Step-by-Step PDF Ingestion Test")
    print("=" * 50)
    
    success = test_step_by_step()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All steps completed successfully!")
    else:
        print("❌ Test failed at some step!") 