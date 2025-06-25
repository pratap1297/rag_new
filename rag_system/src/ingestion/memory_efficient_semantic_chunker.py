"""
Memory Efficient Semantic Chunker
Fixes critical memory leak issues with ML models staying in memory
"""
import gc
from typing import Optional, List, Dict, Any
import threading
import time
import logging
import numpy as np
from pathlib import Path

from ..core.model_memory_manager import get_model_memory_manager

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class MemoryEfficientSemanticChunker:
    """Semantic chunker with efficient memory management"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200,
                 model_name: str = "all-MiniLM-L6-v2", similarity_threshold: float = 0.5,
                 min_chunk_size: int = 100, max_chunk_size: int = 2000):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Create unique model ID
        self.model_id = f"semantic_chunker_{model_name.replace('/', '_')}"
        
        # Get memory manager
        self._memory_manager = get_model_memory_manager()
        
        # Model will be loaded lazily
        self._model = None
        self._model_dimension = None
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self._stats = {
            'chunks_created': 0,
            'model_loads': 0,
            'fallback_uses': 0,
            'last_used': None
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Memory-efficient semantic chunker initialized - Model: {model_name}")
    
    def _get_model(self):
        """Get model with lazy loading and memory management"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers not available for semantic chunking")
        
        try:
            def load_model():
                self.logger.info(f"Loading sentence transformer: {self.model_name}")
                
                # Configure model loading for memory efficiency
                model_kwargs = {}
                if TORCH_AVAILABLE:
                    # Use CPU by default to save GPU memory
                    model_kwargs['device'] = 'cpu'
                
                model = SentenceTransformer(self.model_name, **model_kwargs)
                
                # Get model dimension
                self._model_dimension = model.get_sentence_embedding_dimension()
                
                self._stats['model_loads'] += 1
                return model
            
            # Get model through memory manager
            model = self._memory_manager.get_model(
                self.model_id,
                load_model
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model {self.model_name}: {e}")
            raise
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Chunk text using semantic similarity with memory efficiency"""
        if not text.strip():
            return []
        
        self._stats['last_used'] = time.time()
        
        try:
            # Get model (will be loaded if needed)
            with self._lock:
                model = self._get_model()
            
            # Process text efficiently
            chunks = self._process_text_semantic(text, model, metadata)
            
            self._stats['chunks_created'] += len(chunks)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Semantic chunking failed: {e}")
            # Fallback to simple chunking
            self._stats['fallback_uses'] += 1
            return self._simple_chunk_fallback(text, metadata)
    
    def _process_text_semantic(self, text: str, model, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process text with semantic chunking"""
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= 1:
            return [{
                'text': text,
                'chunk_index': 0,
                'metadata': metadata or {},
                'method': 'semantic_single'
            }]
        
        # For very long texts, use a hybrid approach
        if len(sentences) > 500:
            return self._hybrid_chunking(sentences, model, metadata)
        
        # Calculate embeddings in memory-efficient batches
        embeddings = self._get_embeddings_batched(model, sentences)
        
        # Find semantic boundaries
        boundaries = self._find_semantic_boundaries(sentences, embeddings)
        
        # Create chunks with proper overlap
        chunks = self._create_semantic_chunks(sentences, boundaries, metadata)
        
        # Clean up embeddings from memory
        del embeddings
        gc.collect()
        
        return chunks
    
    def _hybrid_chunking(self, sentences: List[str], model, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Hybrid chunking for very long texts to save memory"""
        # First, do rough chunking by character count
        rough_chunks = self._rough_chunk_by_size(sentences)
        
        all_chunks = []
        
        for i, rough_chunk in enumerate(rough_chunks):
            if len(rough_chunk) <= 50:  # Small enough for semantic processing
                # Calculate embeddings for this chunk
                embeddings = self._get_embeddings_batched(model, rough_chunk, batch_size=16)
                boundaries = self._find_semantic_boundaries(rough_chunk, embeddings)
                semantic_chunks = self._create_semantic_chunks(rough_chunk, boundaries, metadata)
                
                # Update chunk indices
                for chunk in semantic_chunks:
                    chunk['chunk_index'] = len(all_chunks)
                    chunk['parent_chunk'] = i
                    all_chunks.append(chunk)
                
                # Clean up
                del embeddings
                gc.collect()
            else:
                # Too large, use simple chunking
                simple_chunks = self._simple_chunk_sentences(rough_chunk, metadata)
                for chunk in simple_chunks:
                    chunk['chunk_index'] = len(all_chunks)
                    chunk['parent_chunk'] = i
                    chunk['method'] = 'hybrid_simple'
                    all_chunks.append(chunk)
        
        return all_chunks
    
    def _rough_chunk_by_size(self, sentences: List[str]) -> List[List[str]]:
        """Create rough chunks by character count"""
        chunks = []
        current_chunk = []
        current_size = 0
        target_size = self.chunk_size * 0.8  # Leave room for semantic adjustment
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > target_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _get_embeddings_batched(self, model, sentences: List[str], 
                                batch_size: int = 32) -> np.ndarray:
        """Get embeddings in batches to save memory"""
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]
            
            try:
                # Get embeddings for batch
                batch_embeddings = model.encode(
                    batch, 
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                
                all_embeddings.append(batch_embeddings)
                
                # Allow garbage collection between large batches
                if i % (batch_size * 4) == 0:
                    gc.collect()
                    
            except Exception as e:
                self.logger.error(f"Failed to encode batch {i//batch_size}: {e}")
                # Create zero embeddings as fallback
                fallback_embeddings = np.zeros((len(batch), self._model_dimension or 384))
                all_embeddings.append(fallback_embeddings)
        
        # Concatenate all embeddings
        if all_embeddings:
            return np.vstack(all_embeddings)
        else:
            return np.array([])
    
    def _find_semantic_boundaries(self, sentences: List[str], embeddings: np.ndarray) -> List[int]:
        """Find semantic boundaries using cosine similarity"""
        if len(embeddings) <= 1:
            return [0, len(sentences)]
        
        boundaries = [0]  # Always start with 0
        
        # Calculate similarities between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            similarity = np.dot(embeddings[i], embeddings[i + 1])
            similarities.append(similarity)
        
        # Find boundary points where similarity drops significantly
        if similarities:
            # Use adaptive threshold based on similarity distribution
            mean_similarity = np.mean(similarities)
            std_similarity = np.std(similarities)
            adaptive_threshold = max(
                self.similarity_threshold,
                mean_similarity - std_similarity * 0.5
            )
            
            current_chunk_size = 0
            
            for i, similarity in enumerate(similarities):
                sentence_length = len(sentences[i])
                current_chunk_size += sentence_length
                
                # Check for semantic boundary or size constraint
                is_semantic_boundary = similarity < adaptive_threshold
                is_size_boundary = current_chunk_size > self.chunk_size
                is_min_size_met = current_chunk_size > self.min_chunk_size
                
                if (is_semantic_boundary or is_size_boundary) and is_min_size_met:
                    boundaries.append(i + 1)
                    current_chunk_size = 0
                elif current_chunk_size > self.max_chunk_size:
                    # Force boundary at max size
                    boundaries.append(i + 1)
                    current_chunk_size = 0
        
        # Always end with the total length
        if boundaries[-1] != len(sentences):
            boundaries.append(len(sentences))
        
        return boundaries
    
    def _create_semantic_chunks(self, sentences: List[str], boundaries: List[int], 
                               metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks with proper overlap"""
        chunks = []
        
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            
            # Add overlap from previous chunk
            if i > 0 and self.chunk_overlap > 0:
                overlap_sentences = self._calculate_overlap_sentences(
                    sentences, boundaries[i - 1], start_idx
                )
                start_idx = max(0, start_idx - overlap_sentences)
            
            # Extract chunk text
            chunk_sentences = sentences[start_idx:end_idx]
            chunk_text = ' '.join(chunk_sentences)
            
            if chunk_text.strip():
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata.update({
                    'sentence_count': len(chunk_sentences),
                    'start_sentence': start_idx,
                    'end_sentence': end_idx,
                    'method': 'semantic'
                })
                
                chunks.append({
                    'text': chunk_text,
                    'chunk_index': i,
                    'metadata': chunk_metadata
                })
        
        return chunks
    
    def _calculate_overlap_sentences(self, sentences: List[str], prev_start: int, current_start: int) -> int:
        """Calculate how many sentences to include for overlap"""
        if current_start <= prev_start:
            return 0
        
        overlap_chars = 0
        overlap_sentences = 0
        
        # Count backwards from current start
        for i in range(current_start - 1, prev_start - 1, -1):
            sentence_length = len(sentences[i])
            if overlap_chars + sentence_length <= self.chunk_overlap:
                overlap_chars += sentence_length
                overlap_sentences += 1
            else:
                break
        
        return overlap_sentences
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences efficiently"""
        # Simple sentence splitting - can be enhanced with NLTK if available
        import re
        
        # Split on sentence endings
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter very short sentences
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _simple_chunk_fallback(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to simple chunking when semantic chunking fails"""
        chunks = []
        words = text.split()
        
        # Calculate words per chunk
        words_per_chunk = self.chunk_size // 6  # Rough estimate: 6 chars per word
        overlap_words = self.chunk_overlap // 6
        
        for i in range(0, len(words), words_per_chunk - overlap_words):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata.update({
                    'method': 'simple_fallback',
                    'word_count': len(chunk_words)
                })
                
                chunks.append({
                    'text': chunk_text,
                    'chunk_index': len(chunks),
                    'metadata': chunk_metadata
                })
        
        return chunks
    
    def _simple_chunk_sentences(self, sentences: List[str], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simple chunking by combining sentences up to size limit"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata.update({
                    'sentence_count': len(current_chunk),
                    'method': 'simple'
                })
                
                chunks.append({
                    'text': chunk_text,
                    'chunk_index': len(chunks),
                    'metadata': chunk_metadata
                })
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_sentences = self._get_overlap_sentences(current_chunk)
                    current_chunk = overlap_sentences + [sentence]
                    current_size = sum(len(s) for s in current_chunk)
                else:
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata.update({
                'sentence_count': len(current_chunk),
                'method': 'simple'
            })
            
            chunks.append({
                'text': chunk_text,
                'chunk_index': len(chunks),
                'metadata': chunk_metadata
            })
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap from the end of current chunk"""
        if not sentences or self.chunk_overlap <= 0:
            return []
        
        overlap_sentences = []
        overlap_size = 0
        
        # Take sentences from the end
        for sentence in reversed(sentences):
            if overlap_size + len(sentence) <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_size += len(sentence)
            else:
                break
        
        return overlap_sentences
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chunker statistics"""
        return {
            'model_name': self.model_name,
            'model_id': self.model_id,
            'chunks_created': self._stats['chunks_created'],
            'model_loads': self._stats['model_loads'],
            'fallback_uses': self._stats['fallback_uses'],
            'last_used': self._stats['last_used'],
            'config': {
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'similarity_threshold': self.similarity_threshold,
                'min_chunk_size': self.min_chunk_size,
                'max_chunk_size': self.max_chunk_size
            }
        }
    
    def cleanup(self):
        """Manual cleanup of resources"""
        # Model will be cleaned up by memory manager
        self._model = None
        gc.collect()
        self.logger.debug(f"Semantic chunker {self.model_id} cleaned up")
    
    def __del__(self):
        """Cleanup when chunker is deleted"""
        try:
            self.cleanup()
        except Exception:
            pass


class ChunkerFactory:
    """Factory for creating chunkers with proper resource management"""
    
    _instances: Dict[str, Any] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_chunker(cls, chunker_type: str = "semantic", **kwargs) -> Any:
        """Get or create a chunker instance"""
        with cls._lock:
            # Create unique key for configuration
            config_key = str(sorted(kwargs.items()))
            chunker_id = f"{chunker_type}_{hash(config_key)}"
            
            if chunker_id not in cls._instances:
                if chunker_type == "semantic":
                    cls._instances[chunker_id] = MemoryEfficientSemanticChunker(**kwargs)
                elif chunker_type == "simple":
                    # Import here to avoid circular imports
                    from .chunker import Chunker
                    cls._instances[chunker_id] = Chunker(**kwargs)
                else:
                    raise ValueError(f"Unknown chunker type: {chunker_type}")
                
                logging.getLogger(__name__).info(f"Created new chunker: {chunker_id}")
            
            return cls._instances[chunker_id]
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get statistics for all chunkers"""
        with cls._lock:
            stats = {
                'total_instances': len(cls._instances),
                'chunkers': {}
            }
            
            for chunker_id, chunker in cls._instances.items():
                if hasattr(chunker, 'get_stats'):
                    stats['chunkers'][chunker_id] = chunker.get_stats()
                else:
                    stats['chunkers'][chunker_id] = {'type': type(chunker).__name__}
            
            return stats
    
    @classmethod
    def cleanup(cls):
        """Clean up all chunker instances"""
        with cls._lock:
            for chunker in cls._instances.values():
                if hasattr(chunker, 'cleanup'):
                    try:
                        chunker.cleanup()
                    except Exception as e:
                        logging.getLogger(__name__).error(f"Error cleaning up chunker: {e}")
            
            cls._instances.clear()
            gc.collect()
            logging.getLogger(__name__).info("All chunkers cleaned up")
    
    @classmethod
    def force_cleanup(cls):
        """Force cleanup with memory manager"""
        cls.cleanup()
        
        # Also cleanup model memory manager
        memory_manager = get_model_memory_manager()
        memory_manager.force_cleanup() 