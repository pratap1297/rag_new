"""
Debug and Monitoring Tools for RAG Ingestion Pipeline
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class IngestionDebugger:
    """Interactive debugger for ingestion pipeline"""
    
    def __init__(self, ingestion_engine, faiss_store, metadata_store):
        self.ingestion_engine = ingestion_engine
        self.faiss_store = faiss_store
        self.metadata_store = metadata_store
    
    def trace_ingestion(self, file_path: str, save_trace: bool = True) -> Dict[str, Any]:
        """Trace the complete ingestion process step by step"""
        trace = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }
        
        print(f"\n🔍 TRACING INGESTION: {file_path}")
        print("="*60)
        
        # Step 1: File validation
        step1 = self._trace_step("File Validation", lambda: self._validate_file(file_path))
        trace['steps'].append(step1)
        
        # Step 2: Text extraction
        step2 = self._trace_step("Text Extraction", lambda: self._extract_text(file_path))
        trace['steps'].append(step2)
        extracted_text = step2['result'].get('text', '')
        
        # Step 3: Chunking
        step3 = self._trace_step("Chunking", lambda: self._chunk_text(extracted_text))
        trace['steps'].append(step3)
        chunks = step3['result'].get('chunks', [])
        
        # Step 4: Embedding
        step4 = self._trace_step("Embedding Generation", lambda: self._generate_embeddings(chunks))
        trace['steps'].append(step4)
        embeddings = step4['result'].get('embeddings', [])
        
        # Step 5: Vector storage
        step5 = self._trace_step("Vector Storage", lambda: self._store_vectors(embeddings, chunks))
        trace['steps'].append(step5)
        
        # Save trace if requested
        if save_trace:
            trace_file = f"ingestion_trace_{Path(file_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(trace_file, 'w') as f:
                json.dump(trace, f, indent=2)
            print(f"\n💾 Trace saved to: {trace_file}")
        
        return trace
    
    def _trace_step(self, step_name: str, func) -> Dict[str, Any]:
        """Execute and trace a single step"""
        print(f"\n▶️  {step_name}...")
        start_time = datetime.now()
        
        try:
            result = func()
            duration = (datetime.now() - start_time).total_seconds()
            print(f"✅ {step_name} completed in {duration:.3f}s")
            
            return {
                'step': step_name,
                'status': 'success',
                'duration': duration,
                'result': result
            }
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"❌ {step_name} failed: {str(e)}")
            
            return {
                'step': step_name,
                'status': 'failed',
                'duration': duration,
                'error': str(e)
            }
    
    def _validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate file exists and is readable"""
        path = Path(file_path)
        return {
            'exists': path.exists(),
            'size': path.stat().st_size if path.exists() else 0,
            'extension': path.suffix,
            'readable': path.is_file() if path.exists() else False
        }
    
    def _extract_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from file"""
        # This is a simplified version - actual extraction depends on file type
        text = Path(file_path).read_text(encoding='utf-8')
        return {
            'text': text,
            'length': len(text),
            'lines': len(text.splitlines()),
            'words': len(text.split())
        }
    
    def _chunk_text(self, text: str) -> Dict[str, Any]:
        """Chunk text using the configured chunker"""
        chunks = self.ingestion_engine.chunker.chunk_text(text, {})
        return {
            'chunks': chunks,
            'count': len(chunks),
            'avg_size': sum(len(c['text']) for c in chunks) / len(chunks) if chunks else 0,
            'sizes': [len(c['text']) for c in chunks]
        }
    
    def _generate_embeddings(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Generate embeddings for chunks"""
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.ingestion_engine.embedder.embed_texts(texts)
        return {
            'embeddings': embeddings,
            'count': len(embeddings),
            'dimension': len(embeddings[0]) if embeddings else 0
        }
    
    def _store_vectors(self, embeddings: List, chunks: List[Dict]) -> Dict[str, Any]:
        """Store vectors in FAISS"""
        metadata_list = [{'text': chunk['text'], 'chunk_index': i} 
                        for i, chunk in enumerate(chunks)]
        vector_ids = self.faiss_store.add_vectors(embeddings, metadata_list)
        return {
            'vector_ids': vector_ids,
            'count': len(vector_ids)
        }
    
    def analyze_document_coverage(self, doc_id: str) -> Dict[str, Any]:
        """Analyze how well a document is covered in the vector store"""
        print(f"\n📊 ANALYZING DOCUMENT COVERAGE: {doc_id}")
        print("="*60)
        
        # Find all vectors for this document
        vector_ids = self.faiss_store.find_vectors_by_doc_path(doc_id)
        print(f"Found {len(vector_ids)} vectors for document")
        
        if not vector_ids:
            return {'error': 'No vectors found for document'}
        
        # Analyze chunks
        chunks_data = []
        total_text_length = 0
        
        for vector_id in vector_ids:
            metadata = self.faiss_store.get_vector_metadata(vector_id)
            if metadata:
                chunk_text = metadata.get('text', '')
                chunks_data.append({
                    'vector_id': vector_id,
                    'chunk_index': metadata.get('chunk_index', -1),
                    'text_length': len(chunk_text),
                    'text_preview': chunk_text[:100] + '...' if len(chunk_text) > 100 else chunk_text
                })
                total_text_length += len(chunk_text)
        
        # Sort by chunk index
        chunks_data.sort(key=lambda x: x['chunk_index'])
        
        # Check for gaps
        chunk_indices = [c['chunk_index'] for c in chunks_data]
        expected_indices = list(range(max(chunk_indices) + 1))
        missing_indices = set(expected_indices) - set(chunk_indices)
        
        analysis = {
            'doc_id': doc_id,
            'total_vectors': len(vector_ids),
            'total_text_length': total_text_length,
            'avg_chunk_size': total_text_length / len(chunks_data) if chunks_data else 0,
            'missing_chunk_indices': list(missing_indices),
            'chunks': chunks_data
        }
        
        # Print summary
        print(f"\n📈 Coverage Summary:")
        print(f"  - Total vectors: {analysis['total_vectors']}")
        print(f"  - Total text: {analysis['total_text_length']:,} characters")
        print(f"  - Average chunk: {analysis['avg_chunk_size']:.0f} characters")
        
        if missing_indices:
            print(f"  ⚠️  Missing chunks: {missing_indices}")
        else:
            print(f"  ✅ No missing chunks detected")
        
        return analysis

class IngestionMonitor:
    """Monitor and visualize ingestion performance"""
    
    def __init__(self):
        self.metrics = []
    
    def record_ingestion(self, file_path: str, result: Dict[str, Any], duration: float):
        """Record ingestion metrics"""
        metric = {
            'timestamp': datetime.now().isoformat(),
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'file_size': Path(file_path).stat().st_size if Path(file_path).exists() else 0,
            'chunks_created': result.get('chunks_created', 0),
            'vectors_stored': result.get('vectors_stored', 0),
            'duration': duration,
            'success': result.get('status') == 'success'
        }
        self.metrics.append(metric)
    
    def generate_report(self, save_path: Optional[str] = None) -> pd.DataFrame:
        """Generate performance report"""
        if not self.metrics:
            print("No metrics recorded yet")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.metrics)
        
        # Calculate additional metrics
        df['chunks_per_kb'] = df['chunks_created'] / (df['file_size'] / 1024)
        df['ingestion_speed_kb_per_sec'] = (df['file_size'] / 1024) / df['duration']
        
        # Summary statistics
        print("\n📊 INGESTION PERFORMANCE REPORT")
        print("="*60)
        print(f"Total files processed: {len(df)}")
        print(f"Success rate: {df['success'].mean():.1%}")
        print(f"Average ingestion time: {df['duration'].mean():.2f} seconds")
        print(f"Average chunks per file: {df['chunks_created'].mean():.1f}")
        print(f"Average ingestion speed: {df['ingestion_speed_kb_per_sec'].mean():.1f} KB/sec")
        
        if save_path:
            df.to_csv(save_path, index=False)
            print(f"\n💾 Report saved to: {save_path}")
        
        return df
    
    def visualize_performance(self, df: pd.DataFrame = None):
        """Create performance visualizations"""
        if df is None:
            df = pd.DataFrame(self.metrics)
        
        if df.empty:
            print("No data to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Ingestion time by file size
        axes[0, 0].scatter(df['file_size']/1024, df['duration'])
        axes[0, 0].set_xlabel('File Size (KB)')
        axes[0, 0].set_ylabel('Ingestion Time (seconds)')
        axes[0, 0].set_title('Ingestion Time vs File Size')
        
        # 2. Chunks created distribution
        axes[0, 1].hist(df['chunks_created'], bins=20)
        axes[0, 1].set_xlabel('Number of Chunks')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].set_title('Distribution of Chunks Created')
        
        # 3. Success rate over time
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        success_rate = df.groupby(df['timestamp'].dt.date)['success'].mean()
        axes[1, 0].plot(success_rate.index, success_rate.values)
        axes[1, 0].set_xlabel('Date')
        axes[1, 0].set_ylabel('Success Rate')
        axes[1, 0].set_title('Success Rate Over Time')
        
        # 4. Ingestion speed distribution
        axes[1, 1].hist(df['ingestion_speed_kb_per_sec'], bins=20)
        axes[1, 1].set_xlabel('Ingestion Speed (KB/sec)')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_title('Ingestion Speed Distribution')
        
        plt.tight_layout()
        plt.savefig('ingestion_performance.png')
        plt.show()
        print("\n📈 Performance visualization saved to: ingestion_performance.png")

class ChunkAnalyzer:
    """Analyze chunking quality"""
    
    @staticmethod
    def analyze_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze chunk quality metrics"""
        if not chunks:
            return {'error': 'No chunks to analyze'}
        
        # Extract text from chunks
        texts = [chunk.get('text', '') for chunk in chunks]
        
        # Calculate metrics
        lengths = [len(text) for text in texts]
        
        # Check for overlap (simplified - looks for common substrings)
        overlaps = []
        for i in range(len(texts) - 1):
            # Find common substring between consecutive chunks
            common_length = ChunkAnalyzer._find_overlap_length(texts[i], texts[i+1])
            overlaps.append(common_length)
        
        analysis = {
            'total_chunks': len(chunks),
            'size_metrics': {
                'min': min(lengths),
                'max': max(lengths),
                'mean': sum(lengths) / len(lengths),
                'std': pd.Series(lengths).std()
            },
            'overlap_metrics': {
                'avg_overlap': sum(overlaps) / len(overlaps) if overlaps else 0,
                'max_overlap': max(overlaps) if overlaps else 0
            },
            'quality_issues': []
        }
        
        # Identify quality issues
        if analysis['size_metrics']['max'] > 2000:
            analysis['quality_issues'].append("Some chunks exceed 2000 characters")
        
        if analysis['size_metrics']['min'] < 100:
            analysis['quality_issues'].append("Some chunks are very small (< 100 chars)")
        
        if analysis['size_metrics']['std'] > 500:
            analysis['quality_issues'].append("High variance in chunk sizes")
        
        if analysis['overlap_metrics']['avg_overlap'] < 50:
            analysis['quality_issues'].append("Low overlap between chunks might lose context")
        
        return analysis
    
    @staticmethod
    def _find_overlap_length(text1: str, text2: str, max_check: int = 300) -> int:
        """Find overlap length between end of text1 and start of text2"""
        max_overlap = min(len(text1), len(text2), max_check)
        
        for i in range(max_overlap, 0, -1):
            if text1[-i:] == text2[:i]:
                return i
        return 0

# Quick verification function
def quick_verify_ingestion(ingestion_engine, query_engine, test_text: str = None) -> bool:
    """Quick verification of ingestion pipeline"""
    
    if test_text is None:
        test_text = """
        This is a test document for quick verification.
        It contains enough text to create multiple chunks.
        The quick brown fox jumps over the lazy dog.
        We should be able to retrieve this content after ingestion.
        """
    
    print("\n🚀 QUICK INGESTION VERIFICATION")
    print("="*60)
    
    # Create temporary file
    test_file = Path("quick_test.txt")
    test_file.write_text(test_text)
    
    try:
        # Ingest
        print("1. Ingesting test file...")
        result = ingestion_engine.ingest_file(str(test_file))
        print(f"   ✅ Created {result.get('chunks_created', 0)} chunks")
        
        # Query
        print("\n2. Testing retrieval...")
        query = "quick brown fox"
        results = query_engine.search(query, k=3)
        
        # Verify
        found = any('quick brown fox' in r.get('text', '').lower() for r in results)
        
        if found:
            print(f"   ✅ Successfully retrieved content")
            print(f"   Top result score: {results[0].get('similarity_score', 0):.3f}")
            return True
        else:
            print(f"   ❌ Failed to retrieve content")
            return False
            
    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)

# Usage example
if __name__ == "__main__":
    print("Ingestion Debug Tools Ready!")
    print("\nAvailable tools:")
    print("1. IngestionDebugger - Step-by-step tracing")
    print("2. IngestionMonitor - Performance monitoring")
    print("3. ChunkAnalyzer - Chunk quality analysis")
    print("4. quick_verify_ingestion() - Quick pipeline check")
