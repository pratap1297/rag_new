#!/usr/bin/env python3
"""
Test Ingestion Component in Isolation
Test the ingestion pipeline without the API layer
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_ingestion_components():
    """Test ingestion components individually"""
    print("🧪 Testing Ingestion Components in Isolation")
    print("=" * 60)
    
    try:
        # Import components using the same approach as main.py
        from src.core.system_init import initialize_system
        
        print("✅ Successfully imported core components")
        
        # Initialize system using the same method as main.py
        container = initialize_system()
        print("✅ System initialized successfully")
        
        # Test embedder
        print("\n🔍 Testing Embedder...")
        embedder = container.get('embedder')
        test_text = "This is a test sentence for embedding."
        embedding = embedder.embed_text(test_text)
        print(f"✅ Embedder working - Embedding dimension: {len(embedding)}")
        
        # Test chunker
        print("\n📄 Testing Chunker...")
        chunker = container.get('chunker')
        test_long_text = "This is a test document. " * 50  # Make it long enough to chunk
        chunks = chunker.chunk_text(test_long_text)
        print(f"✅ Chunker working - Created {len(chunks)} chunks")
        
        # Test FAISS store
        print("\n🔢 Testing FAISS Store...")
        faiss_store = container.get('faiss_store')
        
        # Test adding vectors
        test_embeddings = [embedding]
        test_metadata = [{
            'text': test_text,
            'chunk_index': 0,
            'title': 'Test Document',
            'source': 'test'
        }]
        
        vector_ids = faiss_store.add_vectors(test_embeddings, test_metadata)
        print(f"✅ FAISS store working - Added vector with ID: {vector_ids[0]}")
        
        # Test searching
        search_results = faiss_store.search(embedding, k=1)
        print(f"✅ FAISS search working - Found {len(search_results)} results")
        
        if search_results:
            result = search_results[0]
            print(f"   📊 Similarity score: {result.get('similarity_score', 0):.4f}")
            print(f"   📝 Text preview: {result.get('text', '')[:50]}...")
        
        # Test metadata store
        print("\n📚 Testing Metadata Store...")
        metadata_store = container.get('metadata_store')
        
        file_id = metadata_store.add_file_metadata("test_file.txt", {
            'title': 'Test File',
            'source': 'test',
            'file_size': 100
        })
        print(f"✅ Metadata store working - File ID: {file_id}")
        
        # Test full ingestion engine
        print("\n🚀 Testing Full Ingestion Engine...")
        ingestion_engine = container.get('ingestion_engine')
        
        # Test text ingestion
        test_text_long = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines 
        that can perform tasks that typically require human intelligence. These tasks include learning, 
        reasoning, problem-solving, perception, and language understanding.
        
        Machine Learning is a subset of AI that focuses on the development of algorithms and statistical models 
        that enable computers to improve their performance on a specific task through experience.
        """
        
        # Create a temporary file for testing
        temp_file = Path("temp_test.txt")
        temp_file.write_text(test_text_long)
        
        try:
            result = ingestion_engine.ingest_file(str(temp_file), {
                'title': 'AI Introduction',
                'source': 'test_document',
                'category': 'technology'
            })
            
            print(f"✅ Ingestion engine working")
            print(f"   📊 Status: {result.get('status')}")
            print(f"   📄 Chunks created: {result.get('chunks_created')}")
            print(f"   🔢 Vectors stored: {result.get('vectors_stored')}")
            
        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
        
        print("\n🎉 All ingestion components working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing ingestion components: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_text_ingestion():
    """Test simple text ingestion without files"""
    print("\n🔍 Testing Simple Text Ingestion")
    print("=" * 50)
    
    try:
        from src.core.system_init import initialize_system
        
        # Initialize
        container = initialize_system()
        
        # Get components
        embedder = container.get('embedder')
        chunker = container.get('chunker')
        faiss_store = container.get('faiss_store')
        
        # Test data
        test_text = "Python is a high-level programming language known for its simplicity and readability."
        test_metadata = {
            'title': 'Python Basics',
            'source': 'test',
            'category': 'programming'
        }
        
        print(f"📝 Text: {test_text}")
        print(f"🏷️ Metadata: {test_metadata}")
        
        # Step 1: Chunk the text
        chunks = chunker.chunk_text(test_text)
        print(f"✅ Chunking: Created {len(chunks)} chunks")
        
        # Step 2: Generate embeddings
        chunk_texts = [chunk.get('text', str(chunk)) for chunk in chunks]
        embeddings = embedder.embed_texts(chunk_texts)
        print(f"✅ Embeddings: Generated {len(embeddings)} embeddings")
        
        # Step 3: Prepare metadata for FAISS
        chunk_metadata_list = []
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get('text', str(chunk))
            chunk_meta = {
                'text': chunk_text,
                'chunk_index': i,
                'doc_id': f"doc_test_{i}",
                **test_metadata
            }
            chunk_metadata_list.append(chunk_meta)
        
        print(f"✅ Metadata: Prepared {len(chunk_metadata_list)} metadata entries")
        
        # Step 4: Store in FAISS
        vector_ids = faiss_store.add_vectors(embeddings, chunk_metadata_list)
        print(f"✅ Storage: Stored {len(vector_ids)} vectors with IDs: {vector_ids}")
        
        # Step 5: Test search
        query_embedding = embedder.embed_text("What is Python?")
        search_results = faiss_store.search(query_embedding, k=3)
        print(f"✅ Search: Found {len(search_results)} results")
        
        for i, result in enumerate(search_results):
            print(f"   Result {i+1}:")
            print(f"     Score: {result.get('similarity_score', 0):.4f}")
            print(f"     Text: {result.get('text', '')[:50]}...")
            print(f"     Title: {result.get('title', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in simple text ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run ingestion tests"""
    print("🧪 RAG System Ingestion Test")
    print("=" * 60)
    
    # Test components individually
    components_ok = test_ingestion_components()
    
    if components_ok:
        # Test simple ingestion flow
        simple_ok = test_simple_text_ingestion()
        
        if simple_ok:
            print("\n🎉 All ingestion tests passed!")
            print("💡 You can now test the API with: python test_step_by_step.py")
        else:
            print("\n⚠️ Simple ingestion test failed")
    else:
        print("\n⚠️ Component tests failed")

if __name__ == "__main__":
    main() 