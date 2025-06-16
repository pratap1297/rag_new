#!/usr/bin/env python3
"""
RAG System Test Script
Simple test to verify system components are working
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_system_initialization():
    """Test system initialization"""
    print("🧪 Testing RAG System Components...")
    
    try:
        from src.core.system_init import initialize_system
        print("✅ System initialization module imported successfully")
        
        # Initialize the system
        container = initialize_system()
        print("✅ System initialized successfully")
        
        # Test configuration
        config_manager = container.get('config_manager')
        config = config_manager.get_config()
        print(f"✅ Configuration loaded: {config.environment} environment")
        
        # Test JSON store
        json_store = container.get('json_store')
        test_data = {"test": "data", "timestamp": "2024-01-01"}
        json_store.write("test_collection", test_data)
        retrieved_data = json_store.read("test_collection")
        assert retrieved_data == test_data
        print("✅ JSON store working correctly")
        
        # Test FAISS store
        faiss_store = container.get('faiss_store')
        info = faiss_store.get_index_info()
        print(f"✅ FAISS store initialized: {info}")
        
        # Test embedder
        embedder = container.get('embedder')
        test_texts = ["Hello world", "This is a test"]
        embeddings = embedder.embed_texts(test_texts)
        print(f"✅ Embedder working: Generated {len(embeddings)} embeddings")
        
        # Test chunker
        chunker = container.get('chunker')
        test_text = "This is a long text that should be chunked into smaller pieces for better processing."
        chunks = chunker.chunk_text(test_text)
        print(f"✅ Chunker working: Generated {len(chunks)} chunks")
        
        # Test metadata store
        metadata_store = container.get('metadata_store')
        stats = metadata_store.get_stats()
        print(f"✅ Metadata store working: {stats}")
        
        print("\n🎉 All core components are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_creation():
    """Test API creation"""
    try:
        from src.core.system_init import initialize_system
        from src.api.main import create_api_app
        
        container = initialize_system()
        app = create_api_app(container)
        
        print("✅ FastAPI application created successfully")
        return True
        
    except Exception as e:
        print(f"❌ API creation failed: {e}")
        return False

def test_ingestion_engine():
    """Test ingestion engine"""
    try:
        from src.core.system_init import initialize_system
        
        container = initialize_system()
        ingestion_engine = container.get('ingestion_engine')
        
        # Create a test file
        test_file = Path("test_document.txt")
        test_file.write_text("This is a test document for ingestion. It contains some sample text to verify the ingestion process works correctly.")
        
        # Test ingestion
        result = ingestion_engine.ingest_file(str(test_file))
        print(f"✅ Ingestion engine working: {result}")
        
        # Cleanup
        test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Ingestion test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting RAG System Tests\n")
    
    tests = [
        ("System Initialization", test_system_initialization),
        ("API Creation", test_api_creation),
        ("Ingestion Engine", test_ingestion_engine)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG system is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.template to .env and add your API keys")
        print("2. Run: python main.py")
        print("3. Access API docs at: http://localhost:8000/docs")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 