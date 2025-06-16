# Enhanced Metadata Store with Vector Linking
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional


class EnhancedMetadataStore:
    """Metadata store with proper vector linking"""
    
    def __init__(self, base_path: str = "data/metadata"):
        self.base_path = base_path
        self.collections = {}
        
        # Key collections for vector linking
        self.vector_metadata = {}  # vector_id -> full metadata
        self.doc_vectors = {}      # doc_id -> [vector_ids]
        self.chunk_vectors = {}    # chunk_id -> vector_id
    
    def add_chunk_with_vector(self, chunk_data: Dict[str, Any], 
                            vector_id: str) -> str:
        """Add chunk metadata with vector linking"""
        chunk_id = chunk_data.get('chunk_id') or f"chunk_{uuid.uuid4().hex[:8]}"
        
        # Enhanced chunk metadata
        enhanced_metadata = {
            **chunk_data,
            "chunk_id": chunk_id,
            "vector_id": vector_id,
            "created_at": datetime.now().isoformat(),
            "type": "chunk"
        }
        
        # Store in multiple indexes for fast lookup
        self.vector_metadata[vector_id] = enhanced_metadata
        self.chunk_vectors[chunk_id] = vector_id
        
        # Group by document
        doc_id = chunk_data.get('doc_id', 'unknown')
        if doc_id not in self.doc_vectors:
            self.doc_vectors[doc_id] = []
        self.doc_vectors[doc_id].append(vector_id)
        
        return chunk_id
    
    def get_metadata_by_vector_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata using vector ID"""
        return self.vector_metadata.get(vector_id)
    
    def get_vectors_by_doc_id(self, doc_id: str) -> List[str]:
        """Get all vector IDs for a document"""
        return self.doc_vectors.get(doc_id, [])
    
    def get_all_files_with_vectors(self) -> List[Dict[str, Any]]:
        """Get all files with their vector information"""
        files = []
        for doc_id, vector_ids in self.doc_vectors.items():
            if vector_ids:
                # Get metadata from first chunk
                first_vector_metadata = self.vector_metadata.get(vector_ids[0], {})
                
                file_info = {
                    "doc_id": doc_id,
                    "filename": first_vector_metadata.get('filename', 'unknown'),
                    "chunk_count": len(vector_ids),
                    "vector_count": len(vector_ids),
                    "file_path": first_vector_metadata.get('file_path', ''),
                    "created_at": first_vector_metadata.get('created_at', ''),
                    "vector_ids": vector_ids
                }
                files.append(file_info)
        
        return files
    
    def get_all_chunks_with_vectors(self) -> List[Dict[str, Any]]:
        """Get all chunks with their vector information"""
        return list(self.vector_metadata.values())
