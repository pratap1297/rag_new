#!/usr/bin/env python3
"""
Comprehensive Test Suite for Adaptive Batch Sizing
Tests all aspects of the adaptive batch sizing functionality
"""

import unittest
import sys
import os
import time
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion.embedder import Embedder, BaseEmbedder, SentenceTransformerEmbedder, CohereEmbedder, AzureEmbedder

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestAdaptiveBatchSizing(unittest.TestCase):
    """Test suite for adaptive batch sizing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_texts_short = [
            "Short text 1",
            "Short text 2", 
            "Short text 3",
            "Short text 4",
            "Short text 5"
        ]
        
        self.test_texts_mixed = [
            "Short",
            "This is a medium length text that contains more information.",
            "Very short",
            "This is a much longer text that contains detailed information about machine learning algorithms, including various approaches to supervised and unsupervised learning, neural networks, and deep learning techniques.",
            "Brief"
        ]
        
        self.test_texts_long = [
            "This is a very long text that simulates a comprehensive document. " * 50,
            "Short text",
            "Another very long text with detailed information about artificial intelligence and machine learning. " * 40
        ]
        
        # Mock psutil for consistent testing
        self.psutil_patcher = patch('psutil.virtual_memory')
        self.mock_virtual_memory = self.psutil_patcher.start()
        
        # Mock memory info (8GB available)
        mock_memory = MagicMock()
        mock_memory.available = 8 * 1024 * 1024 * 1024  # 8GB
        self.mock_virtual_memory.return_value = mock_memory
    
    def tearDown(self):
        """Clean up after tests"""
        self.psutil_patcher.stop()
    
    def test_calculate_optimal_batch_size_basic(self):
        """Test basic optimal batch size calculation"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        # Test with short texts
        text_lengths = [len(text) for text in self.test_texts_short]
        optimal_size = embedder.calculate_optimal_batch_size(text_lengths)
        
        self.assertIsInstance(optimal_size, int)
        self.assertGreater(optimal_size, 0)
        self.assertLessEqual(optimal_size, 64)  # Should not exceed 2x configured size
    
    def test_calculate_optimal_batch_size_empty_list(self):
        """Test optimal batch size calculation with empty text list"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        optimal_size = embedder.calculate_optimal_batch_size([])
        
        self.assertIsInstance(optimal_size, int)
        self.assertGreater(optimal_size, 0)
        self.assertLessEqual(optimal_size, 32)
    
    def test_calculate_optimal_batch_size_mixed_lengths(self):
        """Test optimal batch size calculation with mixed text lengths"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        text_lengths = [len(text) for text in self.test_texts_mixed]
        optimal_size = embedder.calculate_optimal_batch_size(text_lengths)
        
        self.assertIsInstance(optimal_size, int)
        self.assertGreater(optimal_size, 0)
        
        # Should be smaller due to very long text
        avg_length = np.mean(text_lengths)
        max_length = max(text_lengths)
        if max_length > avg_length * 3:
            self.assertLessEqual(optimal_size, 32)
    
    def test_calculate_optimal_batch_size_very_long_texts(self):
        """Test optimal batch size calculation with very long texts"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        text_lengths = [len(text) for text in self.test_texts_long]
        optimal_size = embedder.calculate_optimal_batch_size(text_lengths)
        
        self.assertIsInstance(optimal_size, int)
        self.assertGreater(optimal_size, 0)
        
        # Should be reduced due to very long texts
        avg_length = np.mean(text_lengths)
        max_length = max(text_lengths)
        if max_length > avg_length * 3:
            self.assertLessEqual(optimal_size, 32)
    
    def test_calculate_optimal_batch_size_memory_constraints(self):
        """Test optimal batch size calculation under memory constraints"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        # Mock very low memory
        mock_memory = MagicMock()
        mock_memory.available = 100 * 1024 * 1024  # 100MB
        self.mock_virtual_memory.return_value = mock_memory
        
        text_lengths = [len(text) for text in self.test_texts_short]
        optimal_size = embedder.calculate_optimal_batch_size(text_lengths)
        
        self.assertIsInstance(optimal_size, int)
        self.assertGreater(optimal_size, 0)
        self.assertLess(optimal_size, 32)  # Should be smaller due to memory constraint
    
    def test_calculate_optimal_batch_size_psutil_unavailable(self):
        """Test optimal batch size calculation when psutil is unavailable"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        # Mock ImportError for psutil
        with patch('psutil.virtual_memory', side_effect=ImportError("psutil not available")):
            text_lengths = [len(text) for text in self.test_texts_short]
            optimal_size = embedder.calculate_optimal_batch_size(text_lengths)
            
            self.assertIsInstance(optimal_size, int)
            self.assertGreater(optimal_size, 0)
            self.assertLessEqual(optimal_size, 32)
    
    def test_calculate_optimal_batch_size_exception_handling(self):
        """Test optimal batch size calculation with exception handling"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        # Mock exception in psutil
        with patch('psutil.virtual_memory', side_effect=Exception("Test exception")):
            text_lengths = [len(text) for text in self.test_texts_short]
            optimal_size = embedder.calculate_optimal_batch_size(text_lengths)
            
            self.assertIsInstance(optimal_size, int)
            self.assertGreater(optimal_size, 0)
            self.assertLessEqual(optimal_size, 32)
    
    @patch('ingestion.embedder.SentenceTransformerEmbedder._load_model')
    def test_embed_texts_with_adaptive_batching(self, mock_load_model):
        """Test embed_texts method with adaptive batching"""
        # Mock the model to avoid actual loading
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1] * 384] * 5)  # 384-dim embeddings
        mock_model.get_sentence_embedding_dimension.return_value = 384
        
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        embedder.embedder.model = mock_model
        
        # Test with short texts
        embeddings = embedder.embed_texts(self.test_texts_short)
        
        self.assertEqual(len(embeddings), len(self.test_texts_short))
        self.assertEqual(len(embeddings[0]), 384)  # Check embedding dimension
        
        # Verify that encode was called (indicating batching worked)
        mock_model.encode.assert_called()
    
    @patch('ingestion.embedder.SentenceTransformerEmbedder._load_model')
    def test_embed_texts_empty_list(self, mock_load_model):
        """Test embed_texts method with empty text list"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        embeddings = embedder.embed_texts([])
        
        self.assertEqual(embeddings, [])
    
    @patch('ingestion.embedder.SentenceTransformerEmbedder._load_model')
    def test_embed_texts_single_text(self, mock_load_model):
        """Test embed_texts method with single text"""
        # Mock the model
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1] * 384])
        mock_model.get_sentence_embedding_dimension.return_value = 384
        
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        embedder.embedder.model = mock_model
        
        embeddings = embedder.embed_texts(["Single text"])
        
        self.assertEqual(len(embeddings), 1)
        self.assertEqual(len(embeddings[0]), 384)
    
    def test_sentence_transformer_embedder_dynamic_batch_size(self):
        """Test SentenceTransformerEmbedder with dynamic batch size"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = SentenceTransformerEmbedder(batch_size=32)
            
            # Mock the model
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384] * 3)
            mock_model.get_sentence_embedding_dimension.return_value = 384
            embedder.model = mock_model
            
            # Test with custom batch size
            texts = ["Text 1", "Text 2", "Text 3"]
            embeddings = embedder.embed_texts(texts, batch_size=2)
            
            self.assertEqual(len(embeddings), 3)
            mock_model.encode.assert_called()
    
    def test_cohere_embedder_dynamic_batch_size(self):
        """Test CohereEmbedder with dynamic batch size"""
        with patch('ingestion.embedder.CohereEmbedder._load_client'):
            embedder = CohereEmbedder(batch_size=96)
            
            # Mock the client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.embeddings = [[0.1] * 1024] * 3
            mock_client.embed.return_value = mock_response
            embedder.client = mock_client
            embedder._dimension = 1024
            
            # Test with custom batch size
            texts = ["Text 1", "Text 2", "Text 3"]
            embeddings = embedder.embed_texts(texts, batch_size=2)
            
            self.assertEqual(len(embeddings), 3)
            mock_client.embed.assert_called()
    
    def test_azure_embedder_dynamic_batch_size(self):
        """Test AzureEmbedder with dynamic batch size"""
        with patch('ingestion.embedder.AzureEmbedder._load_client'):
            embedder = AzureEmbedder(batch_size=96)
            
            # Mock the client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_item = MagicMock()
            mock_item.embedding = [0.1] * 1024
            mock_response.data = [mock_item] * 3
            mock_client.embed.return_value = mock_response
            embedder.client = mock_client
            embedder._dimension = 1024
            
            # Test with custom batch size
            texts = ["Text 1", "Text 2", "Text 3"]
            embeddings = embedder.embed_texts(texts, batch_size=2)
            
            self.assertEqual(len(embeddings), 3)
            mock_client.embed.assert_called()
    
    def test_base_embedder_interface(self):
        """Test that BaseEmbedder interface includes batch_size parameter"""
        # Check that the abstract method signature includes batch_size
        import inspect
        sig = inspect.signature(BaseEmbedder.embed_texts)
        self.assertIn('batch_size', sig.parameters)
        self.assertEqual(sig.parameters['batch_size'].default, None)
    
    def test_embed_text_method(self):
        """Test the embed_text method for single text"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = Embedder(provider="sentence-transformers", batch_size=32)
            
            # Mock the model
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384])
            mock_model.get_sentence_embedding_dimension.return_value = 384
            embedder.embedder.model = mock_model
            
            embedding = embedder.embed_text("Single text")
            
            self.assertEqual(len(embedding), 384)
            self.assertIsInstance(embedding, list)
    
    def test_similarity_calculation(self):
        """Test similarity calculation between two texts"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = Embedder(provider="sentence-transformers", batch_size=32)
            
            # Mock the model
            mock_model = MagicMock()
            # Create normalized embeddings for similarity test
            emb1 = np.array([1.0, 0.0, 0.0])
            emb2 = np.array([0.0, 1.0, 0.0])
            mock_model.encode.return_value = np.array([emb1, emb2])
            mock_model.get_sentence_embedding_dimension.return_value = 3
            embedder.embedder.model = mock_model
            
            similarity = embedder.similarity("Text 1", "Text 2")
            
            self.assertIsInstance(similarity, float)
            self.assertGreaterEqual(similarity, 0.0)
            self.assertLessEqual(similarity, 1.0)
    
    def test_similarity_with_zero_vectors(self):
        """Test similarity calculation with zero vectors"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = Embedder(provider="sentence-transformers", batch_size=32)
            
            # Mock the model
            mock_model = MagicMock()
            # Create zero embeddings
            emb1 = np.array([0.0, 0.0, 0.0])
            emb2 = np.array([0.0, 0.0, 0.0])
            mock_model.encode.return_value = np.array([emb1, emb2])
            mock_model.get_sentence_embedding_dimension.return_value = 3
            embedder.embedder.model = mock_model
            
            similarity = embedder.similarity("Text 1", "Text 2")
            
            self.assertEqual(similarity, 0.0)
    
    def test_memory_usage_logging(self):
        """Test that memory usage is properly logged"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = Embedder(provider="sentence-transformers", batch_size=32)
            
            # Mock the model
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            embedder.embedder.model = mock_model
            
            # Capture log output
            with self.assertLogs(level='DEBUG') as log:
                text_lengths = [len(text) for text in self.test_texts_short]
                optimal_size = embedder.calculate_optimal_batch_size(text_lengths)
                
                # Check that memory information is logged
                log_found = False
                for record in log.records:
                    if "Optimal batch size:" in record.message and "available_memory:" in record.message:
                        log_found = True
                        break
                
                self.assertTrue(log_found, "Memory usage should be logged")
    
    def test_batch_processing_logging(self):
        """Test that batch processing is properly logged"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = Embedder(provider="sentence-transformers", batch_size=32)
            
            # Mock the model
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384] * 5)
            mock_model.get_sentence_embedding_dimension.return_value = 384
            embedder.embedder.model = mock_model
            
            # Capture log output
            with self.assertLogs(level='DEBUG') as log:
                embeddings = embedder.embed_texts(self.test_texts_short)
                
                # Check that batch processing is logged
                log_found = False
                for record in log.records:
                    if "Processed batch" in record.message and "batch_size:" in record.message:
                        log_found = True
                        break
                
                self.assertTrue(log_found, "Batch processing should be logged")
    
    def test_performance_characteristics(self):
        """Test performance characteristics of adaptive batching"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = Embedder(provider="sentence-transformers", batch_size=32)
            
            # Mock the model
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384] * 10)
            mock_model.get_sentence_embedding_dimension.return_value = 384
            embedder.embedder.model = mock_model
            
            # Test with different text sizes
            short_texts = ["Short"] * 10
            long_texts = ["Very long text " * 100] * 10
            
            # Time the processing
            start_time = time.time()
            embeddings_short = embedder.embed_texts(short_texts)
            short_time = time.time() - start_time
            
            start_time = time.time()
            embeddings_long = embedder.embed_texts(long_texts)
            long_time = time.time() - start_time
            
            # Both should complete successfully
            self.assertEqual(len(embeddings_short), 10)
            self.assertEqual(len(embeddings_long), 10)
            
            # Long texts might take more time (but should still work)
            self.assertGreater(short_time, 0)
            self.assertGreater(long_time, 0)
    
    def test_error_handling_in_embed_texts(self):
        """Test error handling in embed_texts method"""
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder = Embedder(provider="sentence-transformers", batch_size=32)
            
            # Mock the model to raise an exception
            mock_model = MagicMock()
            mock_model.encode.side_effect = Exception("Test error")
            mock_model.get_sentence_embedding_dimension.return_value = 384
            embedder.embedder.model = mock_model
            
            # Should raise an EmbeddingError
            with self.assertRaises(Exception):
                embedder.embed_texts(self.test_texts_short)
    
    def test_embedder_initialization_with_different_providers(self):
        """Test embedder initialization with different providers"""
        # Test sentence-transformers
        with patch('ingestion.embedder.SentenceTransformerEmbedder._load_model'):
            embedder_st = Embedder(provider="sentence-transformers")
            self.assertIsInstance(embedder_st.embedder, SentenceTransformerEmbedder)
        
        # Test Cohere (with mocked client)
        with patch('ingestion.embedder.CohereEmbedder._load_client'):
            embedder_cohere = Embedder(provider="cohere")
            self.assertIsInstance(embedder_cohere.embedder, CohereEmbedder)
        
        # Test Azure (with mocked client)
        with patch('ingestion.embedder.AzureEmbedder._load_client'):
            embedder_azure = Embedder(provider="azure")
            self.assertIsInstance(embedder_azure.embedder, AzureEmbedder)
    
    def test_unsupported_provider(self):
        """Test error handling for unsupported provider"""
        with self.assertRaises(Exception):
            Embedder(provider="unsupported_provider")

class TestAdaptiveBatchSizingIntegration(unittest.TestCase):
    """Integration tests for adaptive batch sizing"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Mock psutil for consistent testing
        self.psutil_patcher = patch('psutil.virtual_memory')
        self.mock_virtual_memory = self.psutil_patcher.start()
        
        # Mock memory info
        mock_memory = MagicMock()
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
        self.mock_virtual_memory.return_value = mock_memory
    
    def tearDown(self):
        """Clean up after tests"""
        self.psutil_patcher.stop()
    
    @patch('ingestion.embedder.SentenceTransformerEmbedder._load_model')
    def test_large_scale_processing(self, mock_load_model):
        """Test large-scale text processing with adaptive batching"""
        embedder = Embedder(provider="sentence-transformers", batch_size=64)
        
        # Mock the model
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        
        # Create large dataset
        large_texts = [f"Text number {i} with some content for testing." for i in range(1000)]
        
        # Mock encode to return appropriate number of embeddings
        def mock_encode(texts, **kwargs):
            return np.array([[0.1] * 384] * len(texts))
        
        mock_model.encode.side_effect = mock_encode
        embedder.embedder.model = mock_model
        
        # Process large dataset
        start_time = time.time()
        embeddings = embedder.embed_texts(large_texts)
        processing_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(len(embeddings), 1000)
        self.assertEqual(len(embeddings[0]), 384)
        self.assertGreater(processing_time, 0)
        
        # Verify that encode was called multiple times (indicating batching)
        self.assertGreater(mock_model.encode.call_count, 1)
    
    @patch('ingestion.embedder.SentenceTransformerEmbedder._load_model')
    def test_mixed_workload_processing(self, mock_load_model):
        """Test processing of mixed workload (short and long texts)"""
        embedder = Embedder(provider="sentence-transformers", batch_size=32)
        
        # Mock the model
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        
        # Create mixed workload
        mixed_texts = []
        for i in range(50):
            if i % 3 == 0:
                mixed_texts.append("Short text")
            elif i % 3 == 1:
                mixed_texts.append("Medium length text with more content and context")
            else:
                mixed_texts.append("Very long text " * 50)
        
        # Mock encode
        def mock_encode(texts, **kwargs):
            return np.array([[0.1] * 384] * len(texts))
        
        mock_model.encode.side_effect = mock_encode
        embedder.embedder.model = mock_model
        
        # Process mixed workload
        embeddings = embedder.embed_texts(mixed_texts)
        
        # Verify results
        self.assertEqual(len(embeddings), 50)
        self.assertEqual(len(embeddings[0]), 384)
        
        # Verify that encode was called (indicating batching worked)
        self.assertGreater(mock_model.encode.call_count, 0)

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 