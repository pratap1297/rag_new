#!/usr/bin/env python3
"""
Simple Ingestion Test
Test ingestion components directly without full system initialization
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_components():
    """Test basic components individually"""
    print("🧪 Testing Basic Ingestion Components")
    print("=" * 60)
    
    try:
        # Test 1: Config Manager
        print("🔧 Step 1: Testing Config Manager...")
        from src.core.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print(f"   ✅ Config loaded - Environment: {config.environment}")
        
        # Test 2: Embedder (with manual initialization)
        print("\n🔧 Step 2: Testing Embedder...")
        from src.ingestion.embedder import Embedder
        
        # Use sentence-transformers as it's more reliable
        embedder = Embedder(
            provider="sentence-transformers",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        
        test_text = "This is a test sentence for embedding."
        embedding = embedder.embed_text(test_text)
        print(f"   ✅ Embedder working - Dimension: {len(embedding)}")
        
        # Test 3: Chunker
        print("\n🔧 Step 3: Testing Chunker...")
        from src.ingestion.chunker import Chunker
        
        chunker = Chunker(chunk_size=500, chunk_overlap=100)
        test_long_text = "This is a test document. " * 50
        chunks = chunker.chunk_text(test_long_text)
        print(f"   ✅ Chunker working - Created {len(chunks)} chunks")
        
        # Test 4: FAISS Store
        print("\n🔧 Step 4: Testing FAISS Store...")
        from src.storage.faiss_store import FAISSStore
        
        # Create FAISS store with correct dimension
        faiss_store = FAISSStore(
            index_path="data/test_vectors/index.faiss",
            dimension=len(embedding)
        )
        
        # Test adding vectors
        test_embeddings = [embedding]
        test_metadata = [{
            'text': test_text,
            'chunk_index': 0,
            'title': 'Test Document',
            'source': 'test'
        }]
        
        vector_ids = faiss_store.add_vectors(test_embeddings, test_metadata)
        print(f"   ✅ FAISS store working - Added vector with ID: {vector_ids[0]}")
        
        # Test searching
        search_results = faiss_store.search(embedding, k=1)
        print(f"   ✅ FAISS search working - Found {len(search_results)} results")
        
        if search_results:
            result = search_results[0]
            print(f"      📊 Similarity score: {result.get('similarity_score', 0):.4f}")
            print(f"      📝 Text preview: {result.get('text', '')[:50]}...")
        
        # Test 5: Metadata Store (using MemoryMetadataStore for simplicity)
        print("\n🔧 Step 5: Testing Metadata Store...")
        from src.core.memory_store import MemoryMetadataStore
        
        metadata_store = MemoryMetadataStore("data/test_metadata")
        
        file_id = metadata_store.add_file_metadata("test_file.txt", {
            'title': 'Test File',
            'source': 'test',
            'file_size': 100
        })
        print(f"   ✅ Metadata store working - File ID: {file_id}")
        
        print("\n🎉 All basic components working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing basic components: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ingestion_flow():
    """Test the complete ingestion flow"""
    print("\n🚀 Testing Complete Ingestion Flow")
    print("=" * 60)
    
    try:
        # Initialize components
        from src.core.config_manager import ConfigManager
        from src.ingestion.embedder import Embedder
        from src.ingestion.chunker import Chunker
        from src.storage.faiss_store import FAISSStore
        from src.storage.metadata_store import MetadataStore
        
        print("🔧 Initializing components...")
        
        # Use sentence-transformers for reliability
        embedder = Embedder(
            provider="sentence-transformers",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        
        chunker = Chunker(chunk_size=500, chunk_overlap=100)
        
        # Get embedding dimension
        test_embedding = embedder.embed_text("test")
        embedding_dim = len(test_embedding)
        
        faiss_store = FAISSStore(
            index_path="data/test_vectors/flow_index.faiss",
            dimension=embedding_dim
        )
        
        # Use MemoryMetadataStore for simplicity
        from src.core.memory_store import MemoryMetadataStore
        metadata_store = MemoryMetadataStore("data/test_metadata_flow")
        
        print("   ✅ Components initialized")
        
        # Test data
        test_text = """
        Python is a high-level, interpreted programming language with dynamic semantics. 
        Its high-level built-in data structures, combined with dynamic typing and dynamic binding, 
        make it very attractive for Rapid Application Development, as well as for use as a 
        scripting or glue language to connect existing components together.
        
        Python's simple, easy to learn syntax emphasizes readability and therefore reduces 
        the cost of program maintenance. Python supports modules and packages, which encourages 
        program modularity and code reuse.
        """
        
        test_metadata = {
            'title': 'Python Programming Guide',
            'source': 'test_document',
            'category': 'programming',
            'author': 'Test Author'
        }
        
        print(f"\n📝 Processing text: {len(test_text)} characters")
        print(f"🏷️ Metadata: {test_metadata}")
        
        # Step 1: Chunk the text
        print("\n🔧 Step 1: Chunking text...")
        chunks = chunker.chunk_text(test_text, test_metadata)
        print(f"   ✅ Created {len(chunks)} chunks")
        
        # Step 2: Generate embeddings
        print("\n🔧 Step 2: Generating embeddings...")
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = embedder.embed_texts(chunk_texts)
        print(f"   ✅ Generated {len(embeddings)} embeddings")
        
        # Step 3: Prepare metadata for FAISS
        print("\n🔧 Step 3: Preparing metadata...")
        chunk_metadata_list = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                'text': chunk['text'],
                'chunk_index': chunk['chunk_index'],
                'doc_id': f"doc_python_{i}",
                **chunk['metadata']  # This should be flattened
            }
            chunk_metadata_list.append(chunk_meta)
        
        print(f"   ✅ Prepared {len(chunk_metadata_list)} metadata entries")
        
        # Step 4: Store in FAISS
        print("\n🔧 Step 4: Storing vectors...")
        vector_ids = faiss_store.add_vectors(embeddings, chunk_metadata_list)
        print(f"   ✅ Stored {len(vector_ids)} vectors with IDs: {vector_ids}")
        
        # Step 5: Store file metadata
        print("\n🔧 Step 5: Storing file metadata...")
        file_id = metadata_store.add_file_metadata("python_guide.txt", {
            **test_metadata,
            'chunk_count': len(chunks),
            'vector_ids': vector_ids
        })
        print(f"   ✅ Stored file metadata with ID: {file_id}")
        
        # Step 6: Test search
        print("\n🔧 Step 6: Testing search...")
        query_embedding = embedder.embed_text("What is Python programming?")
        search_results = faiss_store.search(query_embedding, k=3)
        print(f"   ✅ Found {len(search_results)} search results")
        
        for i, result in enumerate(search_results):
            print(f"      Result {i+1}:")
            print(f"        Score: {result.get('similarity_score', 0):.4f}")
            print(f"        Text: {result.get('text', '')[:60]}...")
            print(f"        Title: {result.get('title', 'N/A')}")
        
        print("\n🎉 Complete ingestion flow working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in ingestion flow: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple ingestion tests"""
    print("🧪 Simple RAG Ingestion Test")
    print("=" * 60)
    
    # Test basic components first
    basic_ok = test_basic_components()
    
    if basic_ok:
        # Test complete flow
        flow_ok = test_ingestion_flow()
        
        if flow_ok:
            print("\n🎉 All ingestion tests passed!")
            print("💡 Now you can test the API server:")
            print("   1. Run: python main.py")
            print("   2. In another terminal: python test_step_by_step.py")
        else:
            print("\n⚠️ Ingestion flow test failed")
    else:
        print("\n⚠️ Basic component tests failed")

if __name__ == "__main__":
    main() 