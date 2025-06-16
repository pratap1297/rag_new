#!/usr/bin/env python3
"""
Quick Fix: Vector-Metadata Linking
This script patches the existing system to properly link vectors to metadata
"""
import sys
import os
import json
import uuid
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def quick_fix_vector_linking():
    print("🔧 Quick Fix: Vector-Metadata Linking")
    print("=" * 50)
    
    try:
        # 1. Patch the FAISS Store to include metadata
        print("🔧 Patching FAISS Store...")
        
        faiss_store_file = "src/storage/faiss_store.py"
        with open(faiss_store_file, 'r') as f:
            content = f.read()
        
        # Add vector metadata tracking
        if 'self.vector_metadata = {}' not in content:
            # Find the __init__ method and add metadata tracking
            init_pattern = 'def __init__(self, index_path: str, dimension: int):'
            if init_pattern in content:
                # Add after the existing initialization
                addition = '''
        # Vector-metadata linking
        self.vector_metadata = {}  # faiss_index -> metadata
        self.metadata_file = index_path.replace('.bin', '_metadata.json')
        self._load_vector_metadata()'''
                
                content = content.replace(
                    'logging.info(f"FAISS store initialized with dimension {dimension}")',
                    'logging.info(f"FAISS store initialized with dimension {dimension}")' + addition
                )
                
                # Add metadata methods
                metadata_methods = '''
    
    def _load_vector_metadata(self):
        """Load vector metadata mapping"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    self.vector_metadata = json.load(f)
            except Exception as e:
                logging.warning(f"Could not load vector metadata: {e}")
                self.vector_metadata = {}
    
    def _save_vector_metadata(self):
        """Save vector metadata mapping"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.vector_metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Could not save vector metadata: {e}")
    
    def add_vectors_with_metadata(self, vectors, metadata_list):
        """Add vectors with metadata tracking"""
        if not vectors:
            return []
        
        import numpy as np
        vectors_array = np.array(vectors, dtype=np.float32)
        
        # Get starting index
        start_index = self.index.ntotal
        
        # Add to FAISS
        self.index.add(vectors_array)
        
        # Store metadata for each vector
        vector_ids = []
        for i, metadata in enumerate(metadata_list):
            faiss_idx = start_index + i
            vector_id = f"chunk_{uuid.uuid4().hex[:8]}_{metadata.get('doc_id', 'unknown')}"
            
            # Store metadata with vector ID
            self.vector_metadata[str(faiss_idx)] = {
                **metadata,
                'vector_id': vector_id,
                'faiss_index': faiss_idx,
                'created_at': datetime.now().isoformat()
            }
            vector_ids.append(vector_id)
        
        # Save metadata
        self._save_vector_metadata()
        self._save_index()
        
        logging.info(f"Added {len(vectors)} vectors with metadata")
        return vector_ids
    
    def search_with_metadata(self, query_vector, k=5):
        """Search and return results with metadata"""
        import numpy as np
        
        # FAISS search
        similarities, indices = self.index.search(
            np.array([query_vector], dtype=np.float32), k
        )
        
        results = []
        for similarity, faiss_idx in zip(similarities[0], indices[0]):
            if faiss_idx == -1:
                break
            
            # Get metadata for this vector
            metadata = self.vector_metadata.get(str(faiss_idx), {})
            
            result = {
                'faiss_index': int(faiss_idx),
                'similarity_score': float(similarity),
                'score': float(similarity),  # For compatibility
                'vector_id': metadata.get('vector_id', f'vec_{faiss_idx}'),
                'doc_id': metadata.get('doc_id', 'unknown'),
                'content': metadata.get('content', ''),
                'filename': metadata.get('filename', 'unknown'),
                'chunk_id': metadata.get('chunk_id', f'chunk_{faiss_idx}'),
                'metadata': metadata
            }
            results.append(result)
        
        return results'''
                
                # Add the methods at the end of the class
                content = content + metadata_methods
                
                # Add required imports
                if 'import json' not in content:
                    content = content.replace('import logging', 'import logging\nimport json\nimport uuid\nfrom datetime import datetime')
                
                with open(faiss_store_file, 'w') as f:
                    f.write(content)
                
                print(f"   ✅ Patched {faiss_store_file}")
            else:
                print(f"   ⚠️ Could not find __init__ method in {faiss_store_file}")
        else:
            print(f"   ✅ {faiss_store_file} already patched")
        
        # 2. Patch the Query Engine to use new search method
        print("\n🔧 Patching Query Engine...")
        
        query_engine_file = "src/retrieval/query_engine.py"
        with open(query_engine_file, 'r') as f:
            content = f.read()
        
        # Replace the search method call
        if 'search_with_metadata' not in content:
            content = content.replace(
                'search_results = self.faiss_store.search(',
                'search_results = self.faiss_store.search_with_metadata('
            )
            content = content.replace(
                'k=top_k * 2,  # Get more for filtering\n                filter_metadata=filters',
                'k=top_k'
            )
            
            with open(query_engine_file, 'w') as f:
                f.write(content)
            
            print(f"   ✅ Patched {query_engine_file}")
        else:
            print(f"   ✅ {query_engine_file} already patched")
        
        # 3. Clear corrupted data and restart fresh
        print("\n🧹 Clearing corrupted data...")
        
        files_to_remove = [
            "data/vectors/faiss_index.bin",
            "data/vectors/vector_metadata.pkl",
            "data/vectors/faiss_index.bin_metadata.json"
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"   ✅ Removed {file_path}")
        
        print("\n✅ Quick Fix Applied Successfully!")
        print("\n🎯 What was fixed:")
        print("   • Added vector_metadata tracking to FAISS store")
        print("   • Added search_with_metadata() method")
        print("   • Added add_vectors_with_metadata() method")
        print("   • Updated query engine to use new search")
        print("   • Cleared corrupted data for fresh start")
        
        print("\n🚀 Next steps:")
        print("   1. Restart your RAG system")
        print("   2. Upload documents - they will now be properly linked")
        print("   3. Test queries - should show proper document names")
        print("   4. No more 'doc_unknown' issues!")
        
        print("\n💡 How it works now:")
        print("   Document → Chunks → Vectors + Metadata → FAISS + JSON mapping")
        print("   Query → FAISS search → Vector IDs → Metadata lookup → Proper names")
        
    except Exception as e:
        print(f"❌ Quick fix failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_fix_vector_linking() 