# Enhanced FAISS Store with Metadata Linking
import numpy as np
import json
import uuid
from datetime import datetime
import os


class EnhancedFAISSStore:
    """FAISS Store with proper metadata linking"""
    
    def __init__(self, index_path: str, dimension: int):
        self.index_path = index_path
        self.dimension = dimension
        self.metadata_path = index_path.replace('.bin', '_metadata.json')
        
        # Vector ID to FAISS index mapping
        self.vector_id_to_index = {}  # {"chunk_001": 0, "chunk_002": 1}
        self.index_to_vector_id = {}  # {0: "chunk_001", 1: "chunk_002"}
        
        self._initialize_index()
        self._load_metadata_mapping()
    
    def add_vectors_with_metadata(self, vectors: List[List[float]], 
                                 metadata_list: List[Dict[str, Any]]) -> List[str]:
        """Add vectors with proper metadata linking"""
        vector_ids = []
        
        for i, (vector, metadata) in enumerate(zip(vectors, metadata_list)):
            # Generate unique vector ID
            vector_id = f"chunk_{uuid.uuid4().hex[:8]}_{metadata.get('doc_id', 'unknown')}"
            
            # Add to FAISS index
            current_index = self.index.ntotal
            self.index.add(np.array([vector], dtype=np.float32))
            
            # Create bidirectional mapping
            self.vector_id_to_index[vector_id] = current_index
            self.index_to_vector_id[current_index] = vector_id
            
            # Store enhanced metadata
            enhanced_metadata = {
                **metadata,
                "vector_id": vector_id,
                "faiss_index": current_index,
                "created_at": datetime.now().isoformat()
            }
            
            vector_ids.append(vector_id)
        
        # Save mappings
        self._save_metadata_mapping()
        self._save_index()
        
        return vector_ids
    
    def search_with_metadata(self, query_vector: List[float], 
                           k: int = 5) -> List[Dict[str, Any]]:
        """Search and return results with proper metadata"""
        # FAISS search
        similarities, indices = self.index.search(
            np.array([query_vector], dtype=np.float32), k
        )
        
        results = []
        for similarity, faiss_idx in zip(similarities[0], indices[0]):
            if faiss_idx == -1:  # No more results
                break
                
            # Get vector ID from FAISS index
            vector_id = self.index_to_vector_id.get(faiss_idx)
            
            if vector_id:
                result = {
                    "vector_id": vector_id,
                    "faiss_index": int(faiss_idx),
                    "similarity_score": float(similarity),
                    "doc_id": vector_id.split('_')[-1] if '_' in vector_id else "unknown"
                }
                results.append(result)
        
        return results
    
    def _save_metadata_mapping(self):
        """Save vector ID mappings"""
        mapping_data = {
            "vector_id_to_index": self.vector_id_to_index,
            "index_to_vector_id": {str(k): v for k, v in self.index_to_vector_id.items()},
            "total_vectors": self.index.ntotal,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.metadata_path, 'w') as f:
            json.dump(mapping_data, f, indent=2)
    
    def _load_metadata_mapping(self):
        """Load vector ID mappings"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    mapping_data = json.load(f)
                
                self.vector_id_to_index = mapping_data.get("vector_id_to_index", {})
                self.index_to_vector_id = {
                    int(k): v for k, v in mapping_data.get("index_to_vector_id", {}).items()
                }
            except Exception as e:
                print(f"Warning: Could not load metadata mapping: {e}")
                self.vector_id_to_index = {}
                self.index_to_vector_id = {}
