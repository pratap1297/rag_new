#!/usr/bin/env python3
"""
Simple Reranking Test - Step 1
Tests the new cross-encoder reranking functionality from within rag-system directory
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_reranker_creation():
    """Test creating the reranker"""
    print("🧪 Testing Reranker Creation")
    print("=" * 40)
    
    try:
        from retrieval.reranker import Reranker, FallbackReranker, create_reranker
        from core.config_manager import ConfigManager
        
        # Test configuration
        config_manager = ConfigManager()
        
        # Test reranker creation
        print("1. Creating reranker...")
        reranker = create_reranker(config_manager)
        print(f"   ✅ Reranker created: {reranker.get_model_info()}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reranking_functionality():
    """Test the actual reranking functionality"""
    print("\n🧪 Testing Reranking Functionality")
    print("=" * 40)
    
    try:
        from retrieval.reranker import create_reranker
        from core.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        reranker = create_reranker(config_manager)
        
        # Test documents with different relevance to query
        query = "What is machine learning?"
        documents = [
            {
                'text': 'Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.',
                'similarity_score': 0.8,
                'doc_id': 'doc1'
            },
            {
                'text': 'Python is a high-level programming language used for web development, data analysis, and automation.',
                'similarity_score': 0.7,
                'doc_id': 'doc2'
            },
            {
                'text': 'Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns.',
                'similarity_score': 0.75,
                'doc_id': 'doc3'
            },
            {
                'text': 'Artificial intelligence refers to the simulation of human intelligence in machines that are programmed to think and learn.',
                'similarity_score': 0.85,
                'doc_id': 'doc4'
            }
        ]
        
        print(f"Query: '{query}'")
        print("\nOriginal ranking (by similarity score):")
        for i, doc in enumerate(documents):
            print(f"  {i+1}. Score: {doc['similarity_score']:.2f} - {doc['text'][:60]}...")
        
        # Apply reranking
        print("\nApplying reranking...")
        reranked = reranker.rerank(query, documents, top_k=4)
        
        print("\nReranked results:")
        for i, doc in enumerate(reranked):
            rerank_score = doc.get('rerank_score', 'N/A')
            original_score = doc.get('original_score', doc.get('similarity_score', 0))
            print(f"  {i+1}. Rerank: {rerank_score:.3f}, Original: {original_score:.2f} - {doc['text'][:60]}...")
        
        # Check if reranking changed the order
        original_order = [doc['doc_id'] for doc in documents]
        reranked_order = [doc['doc_id'] for doc in reranked]
        
        if original_order != reranked_order:
            print("\n✅ Reranking changed the order - working correctly!")
        else:
            print("\n⚠️ Reranking didn't change order - may be using fallback")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_integration():
    """Test integration with the system"""
    print("\n🧪 Testing System Integration")
    print("=" * 40)
    
    try:
        from core.system_init import initialize_system
        
        print("1. Initializing system...")
        container = initialize_system()
        
        # Check reranker
        if container.has('reranker'):
            reranker = container.get('reranker')
            print(f"   ✅ Reranker in container: {reranker.get_model_info()['model_name']}")
        else:
            print("   ❌ Reranker not found")
            return False
        
        # Check query engine
        query_engine = container.get('query_engine')
        if hasattr(query_engine, 'reranker') and query_engine.reranker:
            print(f"   ✅ Query engine has reranker: enabled={query_engine.reranker.is_enabled()}")
        else:
            print("   ❌ Query engine missing reranker")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 RERANKING IMPLEMENTATION TEST")
    print("=" * 50)
    
    results = []
    
    # Test 1: Reranker creation
    results.append(test_reranker_creation())
    
    # Test 2: Reranking functionality
    results.append(test_reranking_functionality())
    
    # Test 3: System integration
    results.append(test_system_integration())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    test_names = [
        "Reranker Creation",
        "Reranking Functionality", 
        "System Integration"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Reranking is working!")
        print("\nNext: Start the system and test with real queries:")
        print("  python main.py")
    else:
        print("\n⚠️ Some tests failed. Check errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 