"""
FAISS Vector Store
High-performance vector similarity search using FAISS with thread safety and optimization
"""
import faiss
import numpy as np
import pickle
import logging
import threading
import tempfile
import shutil
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from enum import Enum

try:
    from ..core.error_handling import (
        FAISSError, StorageError, ErrorCode, ErrorInfo, ErrorContext, 
        Result, with_error_handling
    )
except ImportError:
    try:
        from rag_system.src.core.error_handling import (
            FAISSError, StorageError, ErrorCode, ErrorInfo, ErrorContext, 
            Result, with_error_handling
        )
    except ImportError:
        # Fallback for when running as script
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
        from error_handling import (
            FAISSError, StorageError, ErrorCode, ErrorInfo, ErrorContext, 
            Result, with_error_handling
        )

class IndexType(Enum):
    FLAT = "flat"  # Brute force
    IVF = "ivf"    # Inverted file index
    HNSW = "hnsw"  # Hierarchical Navigable Small World
    LSH = "lsh"    # Locality Sensitive Hashing
    COMPOSITE = "composite"  # IVF + PQ for very large scale

class OptimizedFAISSIndex:
    """FAISS index with automatic type selection and optimization"""
    
    def __init__(self, dimension: int, initial_size_estimate: int = 1000):
        self.dimension = dimension
        self.size_estimate = initial_size_estimate
        self.index = None
        self.index_type = None
        self.is_trained = False
        self.training_data = []
        self.training_sample_size = 50000  # Max training samples
        
        # Create initial index
        self._create_index()
    
    def _create_index(self):
        """Create optimal index based on estimated size"""
        if self.size_estimate < 10000:
            # Small dataset - use flat index
            self._create_flat_index()
        elif self.size_estimate < 100000:
            # Medium dataset - use IVF
            self._create_ivf_index()
        elif self.size_estimate < 1000000:
            # Large dataset - use HNSW
            self._create_hnsw_index()
        else:
            # Very large dataset - use composite index
            self._create_composite_index()
    
    def _create_flat_index(self):
        """Create flat index for small datasets"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index_type = IndexType.FLAT
        self.is_trained = True  # Flat index doesn't need training
        logging.info(f"Created FLAT index for dimension {self.dimension}")
    
    def _create_ivf_index(self):
        """Create IVF index for medium datasets"""
        # Number of clusters (rule of thumb: sqrt(n) to 4*sqrt(n))
        n_clusters = int(np.sqrt(self.size_estimate) * 2)
        n_clusters = max(min(n_clusters, 4096), 100)  # Clamp between 100-4096
        
        # Create quantizer
        quantizer = faiss.IndexFlatIP(self.dimension)
        
        # Create IVF index
        self.index = faiss.IndexIVFFlat(quantizer, self.dimension, n_clusters)
        
        # Set search parameters
        self.index.nprobe = min(n_clusters // 10, 64)  # Search 10% of clusters
        
        self.index_type = IndexType.IVF
        self.is_trained = False
        logging.info(f"Created IVF index with {n_clusters} clusters, nprobe={self.index.nprobe}")
    
    def _create_hnsw_index(self):
        """Create HNSW index for large datasets"""
        # HNSW parameters
        M = 32  # Number of connections per layer
        ef_construction = 200  # Size of dynamic candidate list
        
        # Create HNSW index
        self.index = faiss.IndexHNSWFlat(self.dimension, M)
        self.index.hnsw.efConstruction = ef_construction
        
        # Set search parameters
        self.index.hnsw.efSearch = 64  # Size of search candidate list
        
        self.index_type = IndexType.HNSW
        self.is_trained = True  # HNSW doesn't need training
        logging.info(f"Created HNSW index with M={M}, efConstruction={ef_construction}")
    
    def _create_composite_index(self):
        """Create composite index for very large datasets"""
        # Use IVF with Product Quantization for compression
        n_clusters = 4096
        m = 64  # Number of subquantizers
        n_bits = 8  # Bits per subquantizer
        
        # Create quantizer
        quantizer = faiss.IndexFlatIP(self.dimension)
        
        # Create index with PQ
        self.index = faiss.IndexIVFPQ(
            quantizer, self.dimension, n_clusters,
            m, n_bits
        )
        
        # Set search parameters
        self.index.nprobe = 64
        
        self.index_type = IndexType.COMPOSITE
        self.is_trained = False
        logging.info(f"Created Composite IVF-PQ index with {n_clusters} clusters, m={m}")
    
    def add_vectors(self, vectors: np.ndarray):
        """Add vectors with automatic training if needed"""
        if not self.is_trained and self.index_type in [IndexType.IVF, IndexType.COMPOSITE]:
            # Collect training data
            if len(self.training_data) < self.training_sample_size:
                self.training_data.extend(vectors[:self.training_sample_size - len(self.training_data)])
            
            # Train when we have enough data
            if len(self.training_data) >= min(10000, self.size_estimate // 10):
                self._train_index()
        
        # Add vectors
        if self.is_trained:
            self.index.add(vectors)
        else:
            # Store vectors temporarily until training
            logging.warning(f"Index not trained yet. Collected {len(self.training_data)} training samples")
    
    def _train_index(self):
        """Train the index with collected data"""
        if self.is_trained or not self.training_data:
            return
        
        training_vectors = np.array(self.training_data, dtype=np.float32)
        
        logging.info(f"Training {self.index_type.value} index with {len(training_vectors)} vectors")
        start_time = time.time()
        
        self.index.train(training_vectors)
        self.is_trained = True
        
        # Add training vectors to index
        self.index.add(training_vectors)
        
        # Clear training data
        self.training_data = []
        
        elapsed = time.time() - start_time
        logging.info(f"Index training completed in {elapsed:.2f}s")
    
    def optimize_for_current_size(self):
        """Re-optimize index based on current size"""
        current_size = self.index.ntotal
        
        # Determine if we need a different index type
        new_type = self._determine_optimal_type(current_size)
        
        if new_type != self.index_type:
            logging.info(f"Re-optimizing index from {self.index_type.value} to {new_type.value}")
            self._migrate_to_new_index_type(new_type)
    
    def _determine_optimal_type(self, size: int) -> IndexType:
        """Determine optimal index type for given size"""
        if size < 10000:
            return IndexType.FLAT
        elif size < 100000:
            return IndexType.IVF
        elif size < 1000000:
            return IndexType.HNSW
        else:
            return IndexType.COMPOSITE
    
    def _migrate_to_new_index_type(self, new_type: IndexType):
        """Migrate existing data to new index type"""
        if self.index.ntotal == 0:
            return
        
        # Extract all vectors
        vectors = self.index.reconstruct_n(0, self.index.ntotal)
        
        # Store old index
        old_index = self.index
        old_type = self.index_type
        
        # Create new index
        self.size_estimate = self.index.ntotal
        self.index_type = new_type
        
        if new_type == IndexType.FLAT:
            self._create_flat_index()
        elif new_type == IndexType.IVF:
            self._create_ivf_index()
        elif new_type == IndexType.HNSW:
            self._create_hnsw_index()
        elif new_type == IndexType.COMPOSITE:
            self._create_composite_index()
        
        # Add vectors to new index
        batch_size = 10000
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            self.add_vectors(batch)
        
        logging.info(f"Migration completed: {old_type.value} -> {new_type.value}")
    
    def search(self, query_vectors: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Search with automatic parameter tuning"""
        if not self.is_trained:
            # Force training if we have data
            if self.training_data:
                self._train_index()
            else:
                return np.array([]), np.array([])
        
        # Adjust search parameters based on index type and size
        if self.index_type == IndexType.IVF:
            # Dynamic nprobe based on recall requirements
            self.index.nprobe = min(
                max(k * 2, self.index.nlist // 20),  # At least 5% of clusters
                self.index.nlist
            )
        elif self.index_type == IndexType.HNSW:
            # Dynamic efSearch
            self.index.hnsw.efSearch = max(k * 2, 64)
        
        return self.index.search(query_vectors, k)
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get detailed index statistics"""
        stats = {
            'type': self.index_type.value,
            'dimension': self.dimension,
            'total_vectors': self.index.ntotal if self.index else 0,
            'is_trained': self.is_trained,
            'index_size_bytes': self._estimate_index_size()
        }
        
        # Type-specific stats
        if self.index_type == IndexType.IVF:
            stats['n_clusters'] = self.index.nlist
            stats['nprobe'] = self.index.nprobe
        elif self.index_type == IndexType.HNSW:
            stats['M'] = self.index.hnsw.M
            stats['efSearch'] = self.index.hnsw.efSearch
            stats['max_level'] = self.index.hnsw.max_level
        elif self.index_type == IndexType.COMPOSITE:
            stats['n_clusters'] = self.index.nlist
            stats['compression_ratio'] = self._estimate_compression_ratio()
        
        return stats
    
    def _estimate_index_size(self) -> int:
        """Estimate index memory size"""
        if not self.index:
            return 0
        
        base_size = self.index.ntotal * self.dimension * 4  # float32
        
        if self.index_type == IndexType.FLAT:
            return base_size
        elif self.index_type == IndexType.IVF:
            # Add overhead for inverted lists
            return int(base_size * 1.1)
        elif self.index_type == IndexType.HNSW:
            # HNSW has significant overhead for graph structure
            M = getattr(self.index.hnsw, 'M', 32)
            return base_size + (self.index.ntotal * M * 8)  # Graph links
        elif self.index_type == IndexType.COMPOSITE:
            # PQ compression reduces size
            return int(base_size * 0.25)  # Approximate 4x compression
        
        return base_size
    
    def _estimate_compression_ratio(self) -> float:
        """Estimate compression ratio for composite index"""
        if self.index_type != IndexType.COMPOSITE:
            return 1.0
        
        # PQ compression ratio
        original_bits = self.dimension * 32  # float32
        compressed_bits = getattr(self.index, 'm', 64) * getattr(self.index, 'nbits', 8)
        return original_bits / compressed_bits

class FAISSStore:
    """Thread-safe FAISS-based vector store for similarity search with optimization"""
    
    def __init__(self, index_path: str = "data/vectors/index.faiss", dimension: int = 1024):  # Updated to match Azure Cohere-embed-v3-english dimension
        self.index_path = Path(index_path)
        self.dimension = dimension
        self.metadata_path = self.index_path.parent / "vector_metadata.pkl"
        self.id_to_metadata = {}
        self.index_to_id = {}  # Maps FAISS index position to our vector ID
        self.next_id = 0
        self.deleted_indices = set()  # Track deleted indices for cleanup
        
        # Thread safety components
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._write_lock = threading.Lock()  # Exclusive lock for writes
        self._readers = 0
        self._readers_cv = threading.Condition(self._lock)
        
        # Optimized index
        self.optimized_index = None
        
        # Create directory if it doesn't exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load index
        self._initialize_index()
        
        logging.info(f"Thread-safe optimized FAISS store initialized with dimension {dimension}")
    
    @contextmanager
    def _read_lock(self):
        """Acquire read lock - multiple readers allowed"""
        with self._lock:
            self._readers += 1
        try:
            yield
        finally:
            with self._lock:
                self._readers -= 1
                if self._readers == 0:
                    self._readers_cv.notify_all()
    
    @contextmanager
    def _write_lock_context(self):
        """Acquire write lock - exclusive access"""
        with self._write_lock:
            # Wait for all readers to finish
            with self._lock:
                while self._readers > 0:
                    self._readers_cv.wait()
            yield
    
    def _initialize_index(self):
        """Initialize or load existing FAISS index"""
        if self.index_path.exists():
            try:
                # Load existing index
                index = faiss.read_index(str(self.index_path))
                self._load_metadata()
                
                # Estimate current size
                current_size = max(index.ntotal, len(self.id_to_metadata))
                
                # Create optimized index and migrate
                self.optimized_index = OptimizedFAISSIndex(self.dimension, current_size)
                
                # Migrate existing data if any
                if index.ntotal > 0:
                    vectors = index.reconstruct_n(0, index.ntotal)
                    self.optimized_index.add_vectors(vectors)
                
                # Clean up any deleted vectors on startup
                self._cleanup_deleted_vectors()
                logging.info(f"Loaded existing FAISS index with {self.optimized_index.index.ntotal} vectors")
            except Exception as e:
                logging.warning(f"Failed to load existing index: {e}. Creating new index.")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _cleanup_deleted_vectors(self):
        """Efficiently clean up deleted vectors without full reconstruction"""
        try:
            # Get all vector IDs that are marked as deleted
            deleted_ids = {
                vector_id for vector_id, metadata in self.id_to_metadata.items()
                if metadata and metadata.get('deleted', False)
            }
            
            if not deleted_ids:
                return
            
            # Only rebuild if significant number of deletions (> 20%)
            total_vectors = len(self.id_to_metadata)
            deletion_ratio = len(deleted_ids) / max(total_vectors, 1)
            
            if deletion_ratio > 0.2:  # 20% threshold
                self._efficient_rebuild_index()
                logging.info(f"Efficiently cleaned up {len(deleted_ids)} deleted vectors")
            else:
                # Just mark for later cleanup
                self.deleted_indices.update(deleted_ids)
                logging.info(f"Marked {len(deleted_ids)} vectors for deferred cleanup")
            
        except Exception as e:
            logging.error(f"Failed to clean up deleted vectors: {e}")
            raise FAISSError(f"Failed to clean up deleted vectors: {e}")
    
    def _efficient_rebuild_index(self):
        """Efficiently rebuild index using optimized approach"""
        try:
            # Get active vectors and metadata
            active_vectors = []
            active_metadata = []
            new_index_to_id = {}
            new_id_to_metadata = {}
            
            current_idx = 0
            for vector_id, metadata in self.id_to_metadata.items():
                if metadata and not metadata.get('deleted', False):
                    # Get vector from current index
                    old_faiss_idx = None
                    for idx, vid in self.index_to_id.items():
                        if vid == vector_id:
                            old_faiss_idx = idx
                            break
                    
                    if old_faiss_idx is not None and old_faiss_idx < self.optimized_index.index.ntotal:
                        try:
                            vector = self.optimized_index.index.reconstruct(old_faiss_idx)
                            active_vectors.append(vector)
                            new_index_to_id[current_idx] = vector_id
                            new_id_to_metadata[vector_id] = metadata
                            current_idx += 1
                        except Exception as e:
                            logging.warning(f"Failed to reconstruct vector {vector_id}: {e}")
                            continue
            
            if not active_vectors:
                # No active vectors, create empty index
                self._create_new_index()
                return
            
            # Create new optimized index
            self.optimized_index = OptimizedFAISSIndex(self.dimension, len(active_vectors))
            
            # Add vectors in batches for efficiency
            batch_size = 10000
            vectors_array = np.array(active_vectors, dtype=np.float32)
            
            for i in range(0, len(vectors_array), batch_size):
                batch = vectors_array[i:i+batch_size]
                self.optimized_index.add_vectors(batch)
            
            # Update mappings
            self.index_to_id = new_index_to_id
            self.id_to_metadata = new_id_to_metadata
            self.deleted_indices.clear()
            
            # Optimize index type if needed
            self.optimized_index.optimize_for_current_size()
            
            logging.info(f"Efficiently rebuilt index with {len(active_vectors)} active vectors")
            
        except Exception as e:
            logging.error(f"Failed to efficiently rebuild index: {e}")
            raise FAISSError(f"Failed to efficiently rebuild index: {e}")
    
    def _create_new_index(self):
        """Create a new optimized FAISS index"""
        # Create optimized index with initial estimate
        self.optimized_index = OptimizedFAISSIndex(self.dimension, 1000)
        self.id_to_metadata = {}
        self.index_to_id = {}
        self.next_id = 0
        self.deleted_indices = set()
        logging.info(f"Created new optimized FAISS index with dimension {self.dimension}")
    
    def _load_metadata(self):
        """Load vector metadata"""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.id_to_metadata = data.get('id_to_metadata', {})
                    self.index_to_id = data.get('index_to_id', {})
                    self.next_id = data.get('next_id', 0)
                    self.deleted_indices = set(data.get('deleted_indices', []))
            except Exception as e:
                logging.warning(f"Failed to load metadata: {e}")
                self.id_to_metadata = {}
                self.index_to_id = {}
                self.next_id = 0
                self.deleted_indices = set()
    
    def _save_atomic(self):
        """Atomically save index and metadata"""
        try:
            # Save to temporary files first
            with tempfile.NamedTemporaryFile(delete=False, suffix='.faiss') as tmp_index:
                faiss.write_index(self.optimized_index.index, tmp_index.name)
                tmp_index_path = tmp_index.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_meta:
                data = {
                    'id_to_metadata': self.id_to_metadata,
                    'index_to_id': self.index_to_id,
                    'next_id': self.next_id,
                    'deleted_indices': list(self.deleted_indices),
                    'index_stats': self.optimized_index.get_index_stats(),
                    'saved_at': datetime.now().isoformat()
                }
                pickle.dump(data, tmp_meta)
                tmp_meta_path = tmp_meta.name
            
            # Atomic move
            shutil.move(tmp_index_path, str(self.index_path))
            shutil.move(tmp_meta_path, str(self.metadata_path))
            
        except Exception as e:
            # Clean up temp files on error
            try:
                if 'tmp_index_path' in locals():
                    Path(tmp_index_path).unlink(missing_ok=True)
                if 'tmp_meta_path' in locals():
                    Path(tmp_meta_path).unlink(missing_ok=True)
            except:
                pass
            raise StorageError(f"Failed to save index atomically: {e}")
    
    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        return vectors / norms
    
    def validate_dimension(self, new_dimension: int) -> bool:
        """Check if dimension change requires index rebuild"""
        if self.optimized_index and self.optimized_index.index and self.optimized_index.index.d != new_dimension:
            logging.error(f"Dimension mismatch: index has {self.optimized_index.index.d}, trying to add {new_dimension}")
            return False
        return True
    
    def get_current_dimension(self) -> int:
        """Get the current dimension of the index"""
        if self.optimized_index and self.optimized_index.index:
            return self.optimized_index.index.d
        return self.dimension
    
    def migrate_to_new_dimension(self, new_dimension: int, new_embedder, original_texts: List[str] = None):
        """Migrate existing vectors to new dimension by re-embedding original texts"""
        if not self.optimized_index or not self.optimized_index.index:
            logging.info("No existing index to migrate")
            self.dimension = new_dimension
            self._create_new_index()
            return
        
        current_dim = self.optimized_index.index.d
        if current_dim == new_dimension:
            logging.info(f"Index already has dimension {new_dimension}, no migration needed")
            return
        
        logging.info(f"Migrating index from dimension {current_dim} to {new_dimension}")
        
        if not original_texts:
            logging.warning("No original texts provided for migration. Cannot re-embed vectors.")
            logging.warning("Consider providing original texts or re-ingesting documents with new embedder.")
            return False
        
        try:
            # Backup current index
            backup_path = f"{self.index_path}.backup_{int(time.time())}"
            self.backup_index(backup_path)
            logging.info(f"Created backup at {backup_path}")
            
            # Collect all active vectors and their metadata
            active_vectors = []
            active_metadata = []
            active_texts = []
            
            for vector_id, metadata in self.id_to_metadata.items():
                if metadata and not metadata.get('deleted', False):
                    # Find the FAISS index for this vector
                    faiss_idx = None
                    for idx, vid in self.index_to_id.items():
                        if vid == vector_id:
                            faiss_idx = idx
                            break
                    
                    if faiss_idx is not None and faiss_idx < self.optimized_index.index.ntotal:
                        try:
                            # Get the original text for this vector
                            text = metadata.get('text', metadata.get('content', ''))
                            if text and text in original_texts:
                                active_vectors.append(vector_id)
                                active_metadata.append(metadata)
                                active_texts.append(text)
                        except Exception as e:
                            logging.warning(f"Failed to process vector {vector_id}: {e}")
                            continue
            
            if not active_texts:
                logging.warning("No valid texts found for migration")
                return False
            
            # Re-embed texts with new embedder
            logging.info(f"Re-embedding {len(active_texts)} texts with new embedder")
            new_vectors = []
            
            # Process in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(active_texts), batch_size):
                batch_texts = active_texts[i:i+batch_size]
                try:
                    batch_embeddings = new_embedder.embed_documents(batch_texts)
                    new_vectors.extend(batch_embeddings)
                    logging.info(f"Re-embedded batch {i//batch_size + 1}/{(len(active_texts) + batch_size - 1)//batch_size}")
                except Exception as e:
                    logging.error(f"Failed to re-embed batch {i//batch_size + 1}: {e}")
                    return False
            
            # Validate new vectors have correct dimension
            if len(new_vectors) != len(active_texts):
                logging.error(f"Dimension mismatch: expected {len(active_texts)} vectors, got {len(new_vectors)}")
                return False
            
            # Create new index with new dimension
            self.dimension = new_dimension
            self._create_new_index()
            
            # Add re-embedded vectors
            vector_ids = self.add_vectors(new_vectors, active_metadata)
            
            logging.info(f"Successfully migrated {len(vector_ids)} vectors to dimension {new_dimension}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to migrate to new dimension: {e}")
            # Restore from backup if migration failed
            try:
                self.restore_index(backup_path)
                logging.info("Restored index from backup after failed migration")
            except Exception as restore_error:
                logging.error(f"Failed to restore from backup: {restore_error}")
            return False
    
    def force_rebuild_for_new_dimension(self, new_dimension: int):
        """Force rebuild index for new dimension (loses all existing vectors)"""
        logging.warning(f"Force rebuilding index for new dimension {new_dimension}. All existing vectors will be lost!")
        
        try:
            # Backup current index if it exists
            if self.optimized_index and self.optimized_index.index and self.optimized_index.index.ntotal > 0:
                backup_path = f"{self.index_path}.backup_{int(time.time())}"
                self.backup_index(backup_path)
                logging.info(f"Created backup at {backup_path}")
            
            # Update dimension and create new index
            self.dimension = new_dimension
            self._create_new_index()
            
            # Save empty index
            self._save_atomic()
            
            logging.info(f"Successfully rebuilt index for dimension {new_dimension}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to force rebuild index: {e}")
            return False
    
    def check_dimension_compatibility(self, new_dimension: int) -> Dict[str, Any]:
        """Check compatibility and provide migration options"""
        current_dim = self.get_current_dimension()
        
        result = {
            'compatible': current_dim == new_dimension,
            'current_dimension': current_dim,
            'new_dimension': new_dimension,
            'migration_required': current_dim != new_dimension,
            'vector_count': 0,
            'migration_options': []
        }
        
        if self.optimized_index and self.optimized_index.index:
            result['vector_count'] = self.optimized_index.index.ntotal
        
        if result['migration_required']:
            result['migration_options'] = [
                {
                    'type': 're_embed',
                    'description': 'Re-embed original texts with new embedder (requires original texts)',
                    'method': 'migrate_to_new_dimension'
                },
                {
                    'type': 'force_rebuild',
                    'description': 'Force rebuild index (loses all existing vectors)',
                    'method': 'force_rebuild_for_new_dimension'
                }
            ]
        
        return result

    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[int]:
        """Thread-safe vector addition with optimization"""
        if len(vectors) != len(metadata):
            raise FAISSError("Number of vectors must match number of metadata entries")
        
        if not vectors:
            return []
        
        # Pre-process metadata to ensure no nesting
        cleaned_metadata = []
        for meta in metadata:
            # If metadata has nested 'metadata' key, flatten it
            if isinstance(meta.get('metadata'), dict):
                logging.warning("Found nested metadata in FAISS store input - flattening")
                nested = meta.pop('metadata')
                flat_meta = meta.copy()
                # Merge nested metadata, but don't override existing keys
                for k, v in nested.items():
                    if k not in flat_meta and k != 'metadata':
                        flat_meta[k] = v
                cleaned_metadata.append(flat_meta)
            else:
                cleaned_metadata.append(meta)
        
        # Debug log to verify structure
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            for i, meta in enumerate(cleaned_metadata[:1]):  # Log first item
                logging.debug(f"Adding vector with metadata keys: {list(meta.keys())}")
                if 'metadata' in meta:
                    logging.error("Still found nested 'metadata' key after cleaning!")
        
        with self._write_lock_context():
            try:
                # Convert to numpy array and validate
                vector_array = np.array(vectors, dtype=np.float32)
                
                # Check dimension compatibility
                if not self.validate_dimension(vector_array.shape[1]):
                    raise FAISSError(
                        f"Vector dimension {vector_array.shape[1]} doesn't match index dimension {self.get_current_dimension()}. "
                        f"Use check_dimension_compatibility() to see migration options."
                    )
                
                normalized_vectors = self._normalize_vectors(vector_array)
                
                # Get current index size atomically
                current_index_size = self.optimized_index.index.ntotal
                
                # Add to optimized index
                self.optimized_index.add_vectors(normalized_vectors)
                
                # Update metadata atomically
                vector_ids = []
                for i, meta in enumerate(cleaned_metadata):
                    vector_id = self.next_id
                    faiss_index = current_index_size + i
                    
                    # Ensure metadata is flat - no nested 'metadata' key
                    flat_meta = {
                        'added_at': datetime.now().isoformat(),
                        'vector_id': vector_id
                    }
                    
                    # Add all keys from meta directly to flat_meta
                    for key, value in meta.items():
                        if key != 'metadata':  # Skip any nested metadata key
                            flat_meta[key] = value
                    
                    self.id_to_metadata[vector_id] = flat_meta
                    self.index_to_id[faiss_index] = vector_id
                    vector_ids.append(vector_id)
                    self.next_id += 1
                
                # Optimize index if needed
                self.optimized_index.optimize_for_current_size()
                
                # Save atomically
                self._save_atomic()
                
                logging.info(f"Added {len(vectors)} vectors to optimized FAISS index")
                return vector_ids
                
            except Exception as e:
                raise FAISSError(f"Failed to add vectors: {e}")
    
    def search(self, query_vector: List[float], k: int = 5, 
               filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Thread-safe search for similar vectors with optimization"""
        with self._read_lock():
            if self.optimized_index.index.ntotal == 0:
                return []
            
            try:
                # Normalize query vector
                query_array = np.array([query_vector], dtype=np.float32)
                
                # Check dimension compatibility
                if not self.validate_dimension(query_array.shape[1]):
                    raise FAISSError(
                        f"Query vector dimension {query_array.shape[1]} doesn't match index dimension {self.get_current_dimension()}. "
                        f"Use check_dimension_compatibility() to see migration options."
                    )
                
                normalized_query = self._normalize_vectors(query_array)
                
                # Search using optimized index
                search_k = min(k * 2, self.optimized_index.index.ntotal)  # Get more results for filtering
                scores, indices = self.optimized_index.search(normalized_query, search_k)
                
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx == -1:  # FAISS returns -1 for empty slots
                        continue
                    
                    # Get vector ID from index mapping
                    vector_id = self.index_to_id.get(idx)
                    if vector_id is None:
                        continue
                    
                    # Get metadata using vector ID with consistent snapshot
                    if vector_id in self.id_to_metadata:
                        metadata = self.id_to_metadata[vector_id]
                        
                        # Safely handle None metadata
                        if metadata is None:
                            metadata = {}
                        else:
                            metadata = metadata.copy()
                        
                        # Skip deleted vectors
                        if metadata.get('deleted', False):
                            continue
                        
                        metadata['similarity_score'] = float(score)
                        
                        # Apply filters if provided
                        if filter_metadata:
                            if not self._matches_filter(metadata, filter_metadata):
                                continue
                        
                        results.append(metadata)
                        
                        if len(results) >= k:
                            break
                
                return results
                
            except Exception as e:
                raise FAISSError(f"Search failed: {e}")
    
    def search_with_metadata(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Thread-safe search with enhanced metadata format for query engine"""
        with self._read_lock():
            if self.optimized_index.index.ntotal == 0:
                return []
            
            try:
                # Normalize query vector
                query_array = np.array([query_vector], dtype=np.float32)
                
                # Check dimension compatibility
                if not self.validate_dimension(query_array.shape[1]):
                    raise FAISSError(
                        f"Query vector dimension {query_array.shape[1]} doesn't match index dimension {self.get_current_dimension()}. "
                        f"Use check_dimension_compatibility() to see migration options."
                    )
                
                normalized_query = self._normalize_vectors(query_array)
                
                # Search using optimized index
                scores, indices = self.optimized_index.search(normalized_query, k)
                
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx == -1:
                        continue
                    
                    vector_id = self.index_to_id.get(idx)
                    if vector_id is None:
                        # Handle orphaned vectors
                        result = {
                            'faiss_index': int(idx),
                            'similarity_score': float(score),
                            'score': float(score),
                            'vector_id': f'orphan_{idx}',
                            'doc_id': 'unknown',
                            'text': 'Content not available (orphaned vector)',
                            'chunk_id': f'chunk_{idx}',
                        }
                        results.append(result)
                        continue
                    
                    if vector_id in self.id_to_metadata:
                        metadata = self.id_to_metadata[vector_id]
                        
                        if metadata is None:
                            metadata = {}
                        
                        if metadata.get('deleted', False):
                            continue
                        
                        # FIXED: Return all metadata fields at top level, not nested
                        result = metadata.copy()  # Start with all existing metadata
                        
                        # Add/override with search-specific fields
                        result.update({
                            'faiss_index': int(idx),
                            'similarity_score': float(score),
                            'score': float(score),
                            'vector_id': str(vector_id),
                            # Ensure key fields exist even if not in metadata
                            'doc_id': result.get('doc_id', 'unknown'),
                            'text': result.get('text', result.get('content', '')),
                            'content': result.get('content', result.get('text', '')),
                            'chunk_id': result.get('chunk_id', f'chunk_{vector_id}'),
                        })
                        
                        # Debug log to verify output structure
                        if logging.getLogger().isEnabledFor(logging.DEBUG) and len(results) == 0:
                            logging.debug(f"Search result keys: {list(result.keys())}")
                            if 'metadata' in result:
                                logging.warning("Found nested 'metadata' key in search result!")
                        
                        results.append(result)
                
                return results
                
            except Exception as e:
                raise FAISSError(f"Search with metadata failed: {e}")
    
    def _matches_filter(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches the given filters"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True
    
    def get_vector_metadata(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific vector"""
        with self._read_lock():
            return self.id_to_metadata.get(vector_id)
    
    def update_metadata(self, vector_id: int, updates: Dict[str, Any]):
        """Update metadata for a vector"""
        with self._write_lock_context():
            if vector_id in self.id_to_metadata:
                self.id_to_metadata[vector_id].update(updates)
                self._save_atomic()
    
    def delete_vectors(self, vector_ids: List[int]):
        """Thread-safe vector deletion with efficient cleanup"""
        with self._write_lock_context():
            try:
                # Mark vectors as deleted
                for vector_id in vector_ids:
                    if vector_id in self.id_to_metadata:
                        self.id_to_metadata[vector_id]['deleted'] = True
                        self.id_to_metadata[vector_id]['deleted_at'] = datetime.now().isoformat()
                        self.deleted_indices.add(vector_id)
                
                # Save metadata
                self._save_atomic()
                
                # Schedule efficient cleanup if threshold reached
                total_vectors = len(self.id_to_metadata)
                deletion_ratio = len(self.deleted_indices) / max(total_vectors, 1)
                
                if deletion_ratio > 0.15:  # 15% threshold for efficient rebuild
                    self._efficient_rebuild_index()
                
                logging.info(f"Deleted {len(vector_ids)} vectors")
                
            except Exception as e:
                logging.error(f"Failed to delete vectors: {e}")
                raise FAISSError(f"Failed to delete vectors: {e}")
    
    def find_vectors_by_doc_path(self, doc_path: str) -> List[int]:
        """Find all vector IDs that match a given doc_path"""
        with self._read_lock():
            matching_vectors = []
            
            for vector_id, metadata in self.id_to_metadata.items():
                # Safely handle None metadata
                if metadata is None:
                    metadata = {}
                
                if metadata.get('deleted', False):
                    continue
                    
                # Check if doc_path matches
                if metadata.get('doc_path') == doc_path:
                    matching_vectors.append(vector_id)
            
            return matching_vectors

    def delete_vectors_by_doc_path(self, doc_path: str) -> int:
        """Delete all vectors associated with a doc_path"""
        vectors_to_delete = self.find_vectors_by_doc_path(doc_path)
        
        if vectors_to_delete:
            self.delete_vectors(vectors_to_delete)
            logging.info(f"Deleted {len(vectors_to_delete)} vectors for doc_path: {doc_path}")
            return len(vectors_to_delete)
        
        return 0
    
    def save_index(self):
        """Save the FAISS index and metadata"""
        with self._write_lock_context():
            self._save_atomic()
            logging.info("Saved optimized FAISS index and metadata")
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the index"""
        with self._read_lock():
            active_count = sum(1 for meta in self.id_to_metadata.values() 
                              if meta is not None and not meta.get('deleted', False))
            
            base_info = {
                'ntotal': self.optimized_index.index.ntotal if self.optimized_index.index else 0,
                'dimension': self.dimension,
                'active_vectors': active_count,
                'deleted_vectors': len(self.deleted_indices),
                'index_path': str(self.index_path),
                'metadata_path': str(self.metadata_path)
            }
            
            # Add optimized index stats
            if self.optimized_index:
                base_info.update(self.optimized_index.get_index_stats())
            
            return base_info
    
    def backup_index(self, backup_path: str):
        """Create a backup of the index"""
        with self._read_lock():
            backup_path = Path(backup_path)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup FAISS index
            if self.index_path.exists():
                backup_index_path = backup_path / f"index_{timestamp}.faiss"
                faiss.write_index(self.optimized_index.index, str(backup_index_path))
            
            # Backup metadata
            if self.metadata_path.exists():
                backup_metadata_path = backup_path / f"metadata_{timestamp}.pkl"
                with open(self.metadata_path, 'rb') as src, open(backup_metadata_path, 'wb') as dst:
                    dst.write(src.read())
            
            logging.info(f"Optimized index backed up to {backup_path}")
            return str(backup_path)
    
    def restore_index(self, backup_path: str):
        """Restore index from backup"""
        with self._write_lock_context():
            backup_path = Path(backup_path)
            
            # Find latest backup files
            index_backups = list(backup_path.glob("index_*.faiss"))
            metadata_backups = list(backup_path.glob("metadata_*.pkl"))
            
            if not index_backups or not metadata_backups:
                raise StorageError("No backup files found")
            
            latest_index = max(index_backups, key=lambda x: x.stat().st_mtime)
            latest_metadata = max(metadata_backups, key=lambda x: x.stat().st_mtime)
            
            # Restore files
            shutil.copy2(latest_index, self.index_path)
            shutil.copy2(latest_metadata, self.metadata_path)
            
            # Reload
            self._initialize_index()
            
            logging.info(f"Optimized index restored from {backup_path}")
    
    def clear_index(self):
        """Clear all vectors from the index"""
        with self._write_lock_context():
            self._create_new_index()
            self._save_atomic()
            logging.info("Optimized index cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the index"""
        with self._read_lock():
            stats = self.get_index_info()
            
            # Add more detailed stats
            if self.id_to_metadata:
                creation_times = [
                    meta.get('added_at') for meta in self.id_to_metadata.values()
                    if meta and not meta.get('deleted', False) and meta.get('added_at')
                ]
                
                if creation_times:
                    stats.update({
                        'oldest_vector': min(creation_times),
                        'newest_vector': max(creation_times),
                        'total_metadata_entries': len(self.id_to_metadata)
                    })
            
            return stats
    
    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all vector metadata (for API endpoints)"""
        with self._read_lock():
            # Return all metadata including deleted vectors for admin purposes
            return dict(self.id_to_metadata)
    
    def get_metadata(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific vector ID"""
        with self._read_lock():
            try:
                # Convert string ID to int if needed
                if isinstance(vector_id, str):
                    vector_id = int(vector_id)
                return self.id_to_metadata.get(vector_id)
            except (ValueError, TypeError):
                return None