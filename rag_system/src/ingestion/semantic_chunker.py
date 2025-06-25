"""
Semantic Chunker
Advanced chunking based on semantic similarity and document structure
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available. Semantic chunking will use fallback.")

try:
    from ..core.error_handling import ChunkingError
    from ..core.resource_manager import get_global_app
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.error_handling import ChunkingError
    from core.resource_manager import get_global_app

@dataclass
class ChunkBoundary:
    """Represents a potential chunk boundary with its score"""
    position: int
    score: float
    sentence_text: str
    boundary_type: str  # 'paragraph', 'sentence', 'semantic'

class SemanticChunker:
    """Advanced chunker that uses semantic similarity to determine optimal boundaries"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 similarity_threshold: float = 0.5,
                 model_name: str = "all-MiniLM-L6-v2",
                 enable_smart_overlap: bool = True):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap  # Default overlap
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name
        self.enable_smart_overlap = enable_smart_overlap
        self.model = None
        self.enabled = SENTENCE_TRANSFORMERS_AVAILABLE
        
        # Content type detection patterns
        self._init_content_patterns()
        
        if self.enabled:
            self._initialize_model()
        else:
            logging.warning("Semantic chunking disabled - using fallback chunking")
    
    def _init_content_patterns(self):
        """Initialize patterns for content type detection"""
        # Code indicators
        self.code_patterns = {
            'keywords': ['def ', 'class ', 'function', 'import ', 'from ', 'return ', 'if ', 'else:', 'elif ', 'for ', 'while ', 'try:', 'except:', 'finally:'],
            'symbols': ['{', '}', ';', '->', '=>', '==', '!=', '<=', '>=', '&&', '||', '++', '--'],
            'brackets': ['()', '[]', '{}'],
            'indentation': r'^\s{4,}|\t+',  # 4+ spaces or tabs
            'comments': ['#', '//', '/*', '*/', '<!--', '-->']
        }
        
        # Structured data indicators
        self.structured_patterns = {
            'json': ['{', '}', '":', '",', '[', ']'],
            'xml': ['<', '>', '</', '/>', '<?', '?>'],
            'csv': [',', '"', '\n'],
            'yaml': [':', '-', '|', '>'],
            'markdown': ['#', '##', '###', '**', '*', '`', '```', '---'],
            'tables': ['|', '+', '-', '=']
        }
        
        # Technical documentation indicators
        self.technical_patterns = {
            'api': ['GET', 'POST', 'PUT', 'DELETE', 'HTTP', 'API', 'endpoint', 'request', 'response'],
            'config': ['config', 'setting', 'parameter', 'option', 'value', 'default'],
            'database': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN', 'TABLE'],
            'math': ['=', '+', '-', '*', '/', '^', '∑', '∫', '∂', '≤', '≥', '≠', '±']
        }
    
    def _calculate_dynamic_overlap(self, text: str, chunk_size: int) -> int:
        """Calculate overlap based on content type and characteristics"""
        if not self.enable_smart_overlap:
            return self.chunk_overlap
        
        # Detect content type
        content_type = self._detect_content_type(text)
        
        # Calculate base overlap based on content type
        if content_type == 'code':
            # Less overlap for code - preserve function/class boundaries
            base_overlap = min(50, chunk_size // 10)
        elif content_type == 'structured_data':
            # More overlap for structured data - preserve context
            base_overlap = min(300, chunk_size // 3)
        elif content_type == 'technical':
            # Medium overlap for technical docs - preserve procedure context
            base_overlap = min(250, chunk_size // 4)
        elif content_type == 'list':
            # Minimal overlap for lists - avoid breaking items
            base_overlap = min(100, chunk_size // 8)
        elif content_type == 'dialogue':
            # Medium overlap for dialogue - preserve conversation flow
            base_overlap = min(200, chunk_size // 5)
        else:
            # Default overlap for prose
            base_overlap = self.chunk_overlap
        
        # Adjust based on content characteristics
        adjusted_overlap = self._adjust_overlap_by_characteristics(text, base_overlap, chunk_size)
        
        # Ensure overlap doesn't exceed reasonable bounds
        max_overlap = min(chunk_size // 2, 500)  # Max 50% of chunk size or 500 chars
        min_overlap = 20  # Minimum overlap
        
        final_overlap = max(min_overlap, min(adjusted_overlap, max_overlap))
        
        logging.debug(f"Smart overlap: content_type={content_type}, base={base_overlap}, adjusted={adjusted_overlap}, final={final_overlap}")
        
        return final_overlap
    
    def _detect_content_type(self, text: str) -> str:
        """Detect the primary content type of the text"""
        text_lower = text.lower()
        text_sample = text[:1000]  # Analyze first 1000 chars for efficiency
        
        # Count indicators for each content type
        scores = {
            'code': self._score_code_content(text_sample),
            'structured_data': self._score_structured_content(text_sample),
            'technical': self._score_technical_content(text_lower),
            'list': self._score_list_content(text_sample),
            'dialogue': self._score_dialogue_content(text_sample),
            'prose': 1.0  # Default baseline
        }
        
        # Return the content type with highest score
        max_score = max(scores.values())
        if max_score > 1.5:  # Threshold for confident detection
            return max(scores, key=scores.get)
        
        return 'prose'  # Default to prose if no clear pattern
    
    def _score_code_content(self, text: str) -> float:
        """Score text for code content indicators"""
        score = 0.0
        
        # Check for code keywords
        keyword_count = sum(1 for keyword in self.code_patterns['keywords'] if keyword in text)
        score += keyword_count * 0.3
        
        # Check for code symbols
        symbol_count = sum(1 for symbol in self.code_patterns['symbols'] if symbol in text)
        score += symbol_count * 0.2
        
        # Check for indentation patterns
        lines = text.split('\n')
        indented_lines = sum(1 for line in lines if re.match(self.code_patterns['indentation'], line))
        if lines:
            score += (indented_lines / len(lines)) * 2.0
        
        # Check for comments
        comment_count = sum(1 for comment in self.code_patterns['comments'] if comment in text)
        score += comment_count * 0.4
        
        # Check for bracket usage
        bracket_density = sum(text.count(bracket) for bracket in ['(', ')', '[', ']', '{', '}']) / len(text)
        score += bracket_density * 10
        
        return score
    
    def _score_structured_content(self, text: str) -> float:
        """Score text for structured data indicators"""
        score = 0.0
        
        # JSON indicators
        json_score = sum(text.count(indicator) for indicator in self.structured_patterns['json'])
        score += json_score * 0.1
        
        # XML indicators
        xml_score = sum(text.count(indicator) for indicator in self.structured_patterns['xml'])
        score += xml_score * 0.1
        
        # CSV indicators
        if ',' in text and '\n' in text:
            lines = text.split('\n')
            csv_like_lines = sum(1 for line in lines if line.count(',') >= 2)
            if lines:
                score += (csv_like_lines / len(lines)) * 3.0
        
        # YAML indicators
        yaml_score = sum(text.count(indicator) for indicator in self.structured_patterns['yaml'])
        score += yaml_score * 0.1
        
        # Markdown indicators
        markdown_score = sum(text.count(indicator) for indicator in self.structured_patterns['markdown'])
        score += markdown_score * 0.05
        
        # Table indicators
        table_score = sum(text.count(indicator) for indicator in self.structured_patterns['tables'])
        score += table_score * 0.1
        
        return score
    
    def _score_technical_content(self, text: str) -> float:
        """Score text for technical documentation indicators"""
        score = 0.0
        
        # API documentation
        api_count = sum(1 for term in self.technical_patterns['api'] if term.lower() in text)
        score += api_count * 0.2
        
        # Configuration content
        config_count = sum(1 for term in self.technical_patterns['config'] if term.lower() in text)
        score += config_count * 0.15
        
        # Database content
        db_count = sum(1 for term in self.technical_patterns['database'] if term.upper() in text.upper())
        score += db_count * 0.25
        
        # Mathematical content
        math_count = sum(1 for symbol in self.technical_patterns['math'] if symbol in text)
        score += math_count * 0.1
        
        return score
    
    def _score_list_content(self, text: str) -> float:
        """Score text for list-like content"""
        lines = text.split('\n')
        if not lines:
            return 0.0
        
        # Count lines that start with list indicators
        list_indicators = ['•', '-', '*', '+', '○', '▪', '▫']
        numbered_pattern = r'^\s*\d+[\.\)]\s+'
        
        list_lines = 0
        for line in lines:
            line_stripped = line.strip()
            if any(line_stripped.startswith(indicator) for indicator in list_indicators):
                list_lines += 1
            elif re.match(numbered_pattern, line):
                list_lines += 1
        
        # Return ratio of list lines to total lines
        return (list_lines / len(lines)) * 4.0
    
    def _score_dialogue_content(self, text: str) -> float:
        """Score text for dialogue/conversation content"""
        score = 0.0
        
        # Look for dialogue indicators
        dialogue_patterns = ['"', "'", ':', 'said', 'asked', 'replied', 'answered']
        
        for pattern in dialogue_patterns:
            score += text.count(pattern) * 0.1
        
        # Look for speaker indicators (Name: or "Name said")
        lines = text.split('\n')
        speaker_lines = sum(1 for line in lines if re.match(r'^[A-Z][a-z]+\s*:', line.strip()))
        if lines:
            score += (speaker_lines / len(lines)) * 3.0
        
        return score
    
    def _adjust_overlap_by_characteristics(self, text: str, base_overlap: int, chunk_size: int) -> int:
        """Adjust overlap based on additional text characteristics"""
        adjustment_factor = 1.0
        
        # Sentence length analysis
        sentences = self._split_into_sentences(text[:500])  # Sample for efficiency
        if sentences:
            avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
            
            if avg_sentence_length > 150:
                # Long sentences - increase overlap to preserve context
                adjustment_factor *= 1.3
            elif avg_sentence_length < 50:
                # Short sentences - can reduce overlap
                adjustment_factor *= 0.8
        
        # Paragraph density
        paragraph_count = text.count('\n\n') + 1
        text_length = len(text)
        if text_length > 0:
            paragraph_density = paragraph_count / (text_length / 1000)  # Paragraphs per 1000 chars
            
            if paragraph_density > 3:
                # High paragraph density - reduce overlap
                adjustment_factor *= 0.9
            elif paragraph_density < 1:
                # Low paragraph density - increase overlap
                adjustment_factor *= 1.2
        
        # Punctuation density (complexity indicator)
        punctuation_chars = '.,;:!?'
        punctuation_count = sum(text.count(p) for p in punctuation_chars)
        if text_length > 0:
            punctuation_density = punctuation_count / text_length
            
            if punctuation_density > 0.05:
                # High punctuation - complex text, increase overlap
                adjustment_factor *= 1.1
        
        # Apply adjustment
        adjusted_overlap = int(base_overlap * adjustment_factor)
        
        return adjusted_overlap
    
    def _is_code(self, text: str) -> bool:
        """Legacy method for backward compatibility"""
        return self._detect_content_type(text) == 'code'
    
    def _is_structured_data(self, text: str) -> bool:
        """Legacy method for backward compatibility"""
        return self._detect_content_type(text) == 'structured_data'
    
    def _initialize_model(self):
        """Initialize the sentence transformer model with memory management"""
        try:
            # Try new memory manager first
            try:
                from ..core.model_memory_manager import get_model_memory_manager
                memory_manager = get_model_memory_manager()
                
                # Create unique model ID
                model_id = f"semantic_chunker_{self.model_name.replace('/', '_')}"
                
                def load_model():
                    logging.info(f"Loading sentence transformer: {self.model_name}")
                    return SentenceTransformer(self.model_name)
                
                # Get model through memory manager
                self.model = memory_manager.get_model(model_id, load_model)
                logging.info(f"Semantic chunker initialized with memory-managed model: {self.model_name}")
                return
                
            except ImportError:
                # Fallback to existing resource manager
                pass
            
            # Fallback to existing resource management
            app = get_global_app()
            
            # Load model through managed model loader
            self.model = app.model_loader.load_model(
                f"semantic_chunker_{self.model_name}",
                SentenceTransformer,
                self.model_name
            )
            
            logging.info(f"Initialized managed semantic chunker model: {self.model_name}")
        except Exception as e:
            logging.error(f"Failed to initialize semantic chunker model: {e}")
            self.enabled = False
            raise ChunkingError(f"Failed to initialize semantic chunker model: {e}")
    
    def cleanup(self):
        """Clean up model resources"""
        try:
            if self.model:
                # Try memory manager cleanup first
                try:
                    from ..core.model_memory_manager import get_model_memory_manager
                    memory_manager = get_model_memory_manager()
                    model_id = f"semantic_chunker_{self.model_name.replace('/', '_')}"
                    memory_manager.unload_model(model_id)
                    self.model = None
                    logging.info(f"Cleaned up semantic chunker model via memory manager: {self.model_name}")
                    return
                except ImportError:
                    pass
                
                # Fallback to existing cleanup
                app = get_global_app()
                app.model_loader.unload_model(f"semantic_chunker_{self.model_name}")
                self.model = None
                logging.info(f"Cleaned up semantic chunker model: {self.model_name}")
        except Exception as e:
            logging.error(f"Error cleaning up semantic chunker: {e}")
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        try:
            self.cleanup()
        except:
            pass
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text using semantic similarity analysis
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text.strip():
            return []
        
        if not self.enabled:
            return self._fallback_chunking(text, metadata)
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            
            # Split into sentences
            sentences = self._split_into_sentences(cleaned_text)
            if len(sentences) <= 1:
                return self._create_single_chunk(cleaned_text, metadata)
            
            # Find semantic boundaries
            boundaries = self._find_semantic_boundaries(sentences)
            
            # Create chunks based on boundaries
            chunks = self._create_chunks_from_boundaries(sentences, boundaries, metadata)
            
            logging.info(f"Semantic chunking created {len(chunks)} chunks from {len(sentences)} sentences")
            return chunks
            
        except Exception as e:
            logging.error(f"Semantic chunking failed: {e}, falling back to simple chunking")
            return self._fallback_chunking(text, metadata)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved detection"""
        # Enhanced sentence splitting patterns
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])'
        
        # Split by sentence endings
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter very short sentences
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _find_semantic_boundaries(self, sentences: List[str]) -> List[ChunkBoundary]:
        """Find optimal chunk boundaries based on semantic similarity"""
        if len(sentences) <= 2:
            return []
        
        try:
            # Generate embeddings for all sentences
            embeddings = self.model.encode(sentences)
            
            # Calculate similarity between consecutive sentences
            similarities = []
            for i in range(len(embeddings) - 1):
                similarity = np.dot(embeddings[i], embeddings[i + 1]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
                )
                similarities.append(similarity)
            
            # Find boundaries where similarity drops significantly
            boundaries = []
            for i, similarity in enumerate(similarities):
                if similarity < self.similarity_threshold:
                    boundary = ChunkBoundary(
                        position=i + 1,  # Position after current sentence
                        score=1.0 - similarity,  # Higher score = better boundary
                        sentence_text=sentences[i + 1] if i + 1 < len(sentences) else "",
                        boundary_type='semantic'
                    )
                    boundaries.append(boundary)
            
            # Add paragraph boundaries (double newlines in original text)
            paragraph_boundaries = self._find_paragraph_boundaries(sentences)
            boundaries.extend(paragraph_boundaries)
            
            # Sort boundaries by position
            boundaries.sort(key=lambda x: x.position)
            
            return boundaries
            
        except Exception as e:
            logging.error(f"Failed to find semantic boundaries: {e}")
            return []
    
    def _find_paragraph_boundaries(self, sentences: List[str]) -> List[ChunkBoundary]:
        """Find paragraph boundaries in the text"""
        boundaries = []
        
        for i, sentence in enumerate(sentences):
            # Look for sentences that start with common paragraph indicators
            if (sentence.strip().startswith(('•', '-', '*', '1.', '2.', '3.')) or
                re.match(r'^\d+\.', sentence.strip()) or
                sentence.strip().startswith(('Chapter', 'Section', 'Part'))):
                
                boundary = ChunkBoundary(
                    position=i,
                    score=0.8,  # High score for structural boundaries
                    sentence_text=sentence,
                    boundary_type='paragraph'
                )
                boundaries.append(boundary)
        
        return boundaries
    
    def _create_chunks_from_boundaries(self, sentences: List[str], 
                                     boundaries: List[ChunkBoundary],
                                     metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create chunks based on identified boundaries"""
        if not boundaries:
            # No good boundaries found, use size-based chunking
            return self._create_size_based_chunks(sentences, metadata)
        
        chunks = []
        current_chunk_start = 0
        full_text = ' '.join(sentences)  # Get full text for smart overlap
        
        for boundary in boundaries:
            # Check if chunk would be too large
            chunk_text = ' '.join(sentences[current_chunk_start:boundary.position])
            
            if len(chunk_text) >= self.chunk_size:
                # Create chunk up to this boundary
                chunk = self._create_chunk_object(
                    text=chunk_text,
                    sentences=sentences[current_chunk_start:boundary.position],
                    chunk_index=len(chunks),
                    boundary_info=boundary,
                    metadata=metadata
                )
                chunks.append(chunk)
                current_chunk_start = max(0, boundary.position - self._calculate_overlap_sentences(sentences, boundary.position, full_text))
        
        # Create final chunk if there are remaining sentences
        if current_chunk_start < len(sentences):
            final_text = ' '.join(sentences[current_chunk_start:])
            if final_text.strip():
                chunk = self._create_chunk_object(
                    text=final_text,
                    sentences=sentences[current_chunk_start:],
                    chunk_index=len(chunks),
                    boundary_info=None,
                    metadata=metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_size_based_chunks(self, sentences: List[str], 
                                metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fallback to size-based chunking when no good boundaries found"""
        chunks = []
        current_chunk = []
        current_length = 0
        full_text = ' '.join(sentences)  # Get full text for smart overlap
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = self._create_chunk_object(
                    text=chunk_text,
                    sentences=current_chunk,
                    chunk_index=len(chunks),
                    boundary_info=None,
                    metadata=metadata
                )
                chunks.append(chunk)
                
                # Start new chunk with smart overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk, full_text)
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = self._create_chunk_object(
                text=chunk_text,
                sentences=current_chunk,
                chunk_index=len(chunks),
                boundary_info=None,
                metadata=metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_overlap_sentences(self, sentences: List[str], position: int, text_context: str = "") -> int:
        """Calculate how many sentences to include for overlap using smart overlap"""
        # Use smart overlap calculation
        if text_context:
            dynamic_overlap = self._calculate_dynamic_overlap(text_context, self.chunk_size)
        else:
            # Fallback to analyzing sentences around position
            context_sentences = sentences[max(0, position-5):position+5]
            context_text = ' '.join(context_sentences)
            dynamic_overlap = self._calculate_dynamic_overlap(context_text, self.chunk_size)
        
        overlap_chars = 0
        overlap_sentences = 0
        
        for i in range(position - 1, -1, -1):
            sentence_length = len(sentences[i])
            if overlap_chars + sentence_length <= dynamic_overlap:
                overlap_chars += sentence_length
                overlap_sentences += 1
            else:
                break
        
        return overlap_sentences
    
    def _get_overlap_sentences(self, sentences: List[str], full_text: str = "") -> List[str]:
        """Get sentences for overlap from the end of current chunk using smart overlap"""
        # Calculate dynamic overlap
        context_text = full_text if full_text else ' '.join(sentences)
        dynamic_overlap = self._calculate_dynamic_overlap(context_text, self.chunk_size)
        
        overlap_chars = 0
        overlap_sentences = []
        
        for sentence in reversed(sentences):
            if overlap_chars + len(sentence) <= dynamic_overlap:
                overlap_chars += len(sentence)
                overlap_sentences.insert(0, sentence)
            else:
                break
        
        return overlap_sentences
    
    def _create_chunk_object(self, text: str, sentences: List[str], 
                           chunk_index: int, boundary_info: Optional[ChunkBoundary],
                           metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a standardized chunk object"""
        chunk = {
            'text': text.strip(),
            'chunk_index': chunk_index,
            'chunk_size': len(text),
            'sentence_count': len(sentences),
            'chunking_method': 'semantic',
            'metadata': metadata or {}
        }
        
        if boundary_info:
            chunk['boundary_type'] = boundary_info.boundary_type
            chunk['boundary_score'] = boundary_info.score
        
        return chunk
    
    def _create_single_chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create a single chunk when text is short"""
        return [{
            'text': text.strip(),
            'chunk_index': 0,
            'chunk_size': len(text),
            'sentence_count': 1,
            'chunking_method': 'single',
            'total_chunks': 1,
            'metadata': metadata or {}
        }]
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        
        return text.strip()
    
    def _fallback_chunking(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fallback to simple character-based chunking"""
        from .chunker import Chunker
        
        fallback_chunker = Chunker(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        chunks = fallback_chunker.chunk_text(text, metadata)
        
        # Update chunking method
        for chunk in chunks:
            chunk['chunking_method'] = 'fallback'
        
        return chunks
    
    def get_chunker_info(self) -> Dict[str, Any]:
        """Get information about the chunker configuration"""
        return {
            'chunker_type': 'semantic',
            'model_name': self.model_name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'similarity_threshold': self.similarity_threshold,
            'enabled': self.enabled,
            'model_available': SENTENCE_TRANSFORMERS_AVAILABLE,
            'smart_overlap_enabled': self.enable_smart_overlap,
            'features': {
                'content_type_detection': True,
                'dynamic_overlap_calculation': True,
                'characteristic_analysis': True,
                'supported_content_types': ['code', 'structured_data', 'technical', 'list', 'dialogue', 'prose']
            }
        }

def create_semantic_chunker(config_manager) -> SemanticChunker:
    """Factory function to create semantic chunker based on configuration"""
    config = config_manager.get_config()
    
    return SemanticChunker(
        chunk_size=config.ingestion.chunk_size,
        chunk_overlap=config.ingestion.chunk_overlap,
        similarity_threshold=0.5,  # Can be made configurable
        model_name="all-MiniLM-L6-v2",  # Lightweight model for chunking
        enable_smart_overlap=True
    ) 