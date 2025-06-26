"""
Text Embedder
Generate embeddings using multiple providers (sentence-transformers, Cohere)
"""
import logging
import numpy as np
import os
from typing import List, Union, Optional
from abc import ABC, abstractmethod

try:
    from ..core.error_handling import EmbeddingError
except ImportError:
    try:
        from rag_system.src.core.error_handling import EmbeddingError
    except ImportError:
        # Fallback for when running as script
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
        from error_handling import EmbeddingError

class BaseEmbedder(ABC):
    """Base class for embedding providers"""
    
    @abstractmethod
    def embed_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        pass

class SentenceTransformerEmbedder(BaseEmbedder):
    """Sentence Transformers embedder"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 device: str = "cpu", batch_size: int = 32):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logging.info(f"Loaded SentenceTransformer model: {self.model_name}")
        except ImportError:
            raise EmbeddingError("sentence-transformers package not installed")
        except Exception as e:
            raise EmbeddingError(f"Failed to load SentenceTransformer model: {e}")
    
    def embed_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        # Use provided batch_size or fall back to instance batch_size
        effective_batch_size = batch_size or self.batch_size
        
        try:
            all_embeddings = []
            for i in range(0, len(texts), effective_batch_size):
                batch = texts[i:i + effective_batch_size]
                batch_embeddings = self.model.encode(
                    batch,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                all_embeddings.extend(batch_embeddings.tolist())
            return all_embeddings
        except Exception as e:
            raise EmbeddingError(f"Failed to generate SentenceTransformer embeddings: {e}")
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()

class CohereEmbedder(BaseEmbedder):
    """Cohere embedder"""
    
    def __init__(self, model_name: str = "embed-english-v3.0", 
                 api_key: Optional[str] = None, batch_size: int = 96):
        self.model_name = model_name
        self.api_key = api_key or os.getenv('COHERE_API_KEY')
        self.batch_size = batch_size
        self.client = None
        self._dimension = None
        self._load_client()
    
    def _load_client(self):
        """Load the Cohere client"""
        if not self.api_key:
            raise EmbeddingError("Cohere API key not provided. Set COHERE_API_KEY environment variable.")
        
        try:
            import cohere
            self.client = cohere.Client(self.api_key)
            logging.info(f"Loaded Cohere client with model: {self.model_name}")
            
            # Get dimension by testing with a sample text
            test_response = self.client.embed(
                texts=["test"],
                model=self.model_name,
                input_type="search_document"
            )
            self._dimension = len(test_response.embeddings[0])
            logging.info(f"Cohere embedding dimension: {self._dimension}")
            
        except ImportError:
            raise EmbeddingError("cohere package not installed")
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize Cohere client: {e}")
    
    def embed_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        # Use provided batch_size or fall back to instance batch_size
        effective_batch_size = batch_size or self.batch_size
        
        try:
            import time
            all_embeddings = []
            for i in range(0, len(texts), effective_batch_size):
                batch = texts[i:i + effective_batch_size]
                start_time = time.time()
                response = self.client.embed(
                    texts=batch,
                    model=self.model_name,
                    input_type="search_document"
                )
                elapsed = time.time() - start_time
                logging.debug(f"Cohere embedding batch ({len(batch)} texts) took {elapsed:.2f} seconds")
                all_embeddings.extend(response.embeddings)
            return all_embeddings
        except Exception as e:
            logging.error(f"Cohere embedding error: {e}")
            raise EmbeddingError(f"Failed to generate Cohere embeddings: {e}")
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension

class AzureEmbedder(BaseEmbedder):
    """Azure AI Inference embedder"""
    
    def __init__(self, model_name: str = "Cohere-embed-v3-english", 
                 api_key: Optional[str] = None, endpoint: Optional[str] = None, 
                 batch_size: int = 96):
        self.model_name = model_name
        self.api_key = api_key or os.getenv('AZURE_API_KEY')
        self.endpoint = endpoint or os.getenv('AZURE_EMBEDDINGS_ENDPOINT')
        self.batch_size = batch_size
        self.client = None
        self._dimension = None
        self._load_client()
    
    def _load_client(self):
        """Load the Azure AI Inference client"""
        if not self.api_key:
            raise EmbeddingError("Azure API key not provided. Set AZURE_API_KEY environment variable.")
        if not self.endpoint:
            raise EmbeddingError("Azure endpoint not provided. Set AZURE_EMBEDDINGS_ENDPOINT environment variable.")
        
        try:
            from azure.ai.inference import EmbeddingsClient
            from azure.core.credentials import AzureKeyCredential
            
            self.client = EmbeddingsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
            logging.info(f"Loaded Azure AI Inference client with model: {self.model_name}")
            
            # Get dimension by testing with a sample text
            test_response = self.client.embed(
                input=["test"],
                model=self.model_name,
                input_type="document"
            )
            self._dimension = len(test_response.data[0].embedding)
            logging.info(f"Azure embedding dimension: {self._dimension}")
            
        except ImportError:
            raise EmbeddingError("azure-ai-inference package not installed")
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize Azure AI Inference client: {e}")
    
    def embed_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        # Use provided batch_size or fall back to instance batch_size
        effective_batch_size = batch_size or self.batch_size
        
        try:
            import time
            all_embeddings = []
            for i in range(0, len(texts), effective_batch_size):
                batch = texts[i:i + effective_batch_size]
                start_time = time.time()
                response = self.client.embed(
                    input=batch,
                    model=self.model_name,
                    input_type="document"
                )
                elapsed = time.time() - start_time
                logging.debug(f"Azure embedding batch ({len(batch)} texts) took {elapsed:.2f} seconds")
                
                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            return all_embeddings
        except Exception as e:
            logging.error(f"Azure embedding error: {e}")
            raise EmbeddingError(f"Failed to generate Azure embeddings: {e}")
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension

class Embedder:
    """Multi-provider text embedder"""
    
    def __init__(self, provider: str = "cohere", model_name: Optional[str] = None, 
                 api_key: Optional[str] = None, device: str = "cpu", batch_size: int = 32,
                 endpoint: Optional[str] = None):
        self.provider = provider.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.device = device
        self.batch_size = batch_size
        self.endpoint = endpoint
        self.embedder = None
        
        self._initialize_embedder()
        logging.info(f"Embedder initialized with provider: {provider}")
    
    def _initialize_embedder(self):
        """Initialize the appropriate embedder"""
        if self.provider == "cohere":
            model = self.model_name or "embed-english-v3.0"
            self.embedder = CohereEmbedder(
                model_name=model,
                api_key=self.api_key,
                batch_size=self.batch_size
            )
        elif self.provider == "azure":
            model = self.model_name or "Cohere-embed-v3-english"
            self.embedder = AzureEmbedder(
                model_name=model,
                api_key=self.api_key,
                endpoint=self.endpoint,
                batch_size=self.batch_size
            )
        elif self.provider == "sentence-transformers":
            model = self.model_name or "sentence-transformers/all-MiniLM-L6-v2"
            self.embedder = SentenceTransformerEmbedder(
                model_name=model,
                device=self.device,
                batch_size=self.batch_size
            )
        else:
            raise EmbeddingError(f"Unsupported embedding provider: {self.provider}")
    
    def calculate_optimal_batch_size(self, text_lengths: List[int]) -> int:
        """Calculate optimal batch size based on available memory and text characteristics"""
        try:
            import psutil
            
            # Get available memory
            available_memory = psutil.virtual_memory().available
            
            if not text_lengths:
                return min(self.batch_size, 32)  # Default fallback
            
            # Calculate average text length
            avg_text_length = np.mean(text_lengths)
            max_text_length = max(text_lengths)
            
            # Estimate memory usage per text
            # Rough estimate: each character uses ~4 bytes, with overhead for embeddings
            # Embedding dimension affects memory usage significantly
            embedding_dim = self.get_dimension()
            estimated_memory_per_text = (avg_text_length * 4 + embedding_dim * 4) * 3  # 3x overhead for processing
            
            # Use 40% of available memory to be conservative
            max_batch_size = int((available_memory * 0.4) / estimated_memory_per_text)
            
            # Ensure reasonable bounds
            min_batch_size = 1
            max_batch_size = min(max_batch_size, self.batch_size * 2)  # Don't exceed 2x configured batch size
            
            # Adjust based on text length characteristics
            if max_text_length > avg_text_length * 3:
                # If there are very long texts, reduce batch size
                max_batch_size = max_batch_size // 2
            
            optimal_batch_size = max(min_batch_size, min(max_batch_size, self.batch_size))
            
            logging.debug(f"Optimal batch size: {optimal_batch_size} "
                         f"(available_memory: {available_memory/1024/1024:.1f}MB, "
                         f"avg_text_length: {avg_text_length:.1f}, "
                         f"embedding_dim: {embedding_dim})")
            
            return optimal_batch_size
            
        except ImportError:
            logging.warning("psutil not available, using default batch size")
            return min(self.batch_size, 32)
        except Exception as e:
            logging.warning(f"Error calculating optimal batch size: {e}, using default")
            return min(self.batch_size, 32)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with adaptive batch sizing"""
        if not texts:
            return []
        
        # Calculate optimal batch size based on text characteristics
        text_lengths = [len(text) for text in texts]
        optimal_batch_size = self.calculate_optimal_batch_size(text_lengths)
        
        # Use adaptive batch processing
        all_embeddings = []
        for i in range(0, len(texts), optimal_batch_size):
            batch = texts[i:i + optimal_batch_size]
            batch_embeddings = self.embedder.embed_texts(batch, batch_size=optimal_batch_size)
            all_embeddings.extend(batch_embeddings)
            
            logging.debug(f"Processed batch {i//optimal_batch_size + 1}/{(len(texts) + optimal_batch_size - 1)//optimal_batch_size} "
                         f"({len(batch)} texts, batch_size: {optimal_batch_size})")
        
        return all_embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedder.get_dimension()
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        embeddings = self.embed_texts([text1, text2])
        
        # Cosine similarity
        emb1 = np.array(embeddings[0])
        emb2 = np.array(embeddings[1])
        
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2)) 