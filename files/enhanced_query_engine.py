# Enhanced Query Engine with Proper Linking
from datetime import datetime
from typing import Dict, List, Any


class EnhancedQueryEngine:
    """Query engine with proper vector-metadata linking"""
    
    def __init__(self, faiss_store, embedder, llm_client, metadata_store, config_manager):
        self.faiss_store = faiss_store
        self.embedder = embedder
        self.llm_client = llm_client
        self.metadata_store = metadata_store
        self.config = config_manager.get_config()
    
    def process_query(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Process query with proper metadata linking"""
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)
            
            # Search FAISS with metadata
            search_results = self.faiss_store.search_with_metadata(
                query_vector=query_embedding, 
                k=max_results
            )
            
            # Enrich results with full metadata
            enriched_results = []
            for result in search_results:
                vector_id = result.get('vector_id')
                if vector_id:
                    # Get full metadata using vector ID
                    metadata = self.metadata_store.get_metadata_by_vector_id(vector_id)
                    if metadata:
                        enriched_result = {
                            **result,
                            "content": metadata.get('content', ''),
                            "doc_id": metadata.get('doc_id', 'unknown'),
                            "filename": metadata.get('filename', 'unknown'),
                            "chunk_id": metadata.get('chunk_id', 'unknown'),
                            "page_number": metadata.get('page_number'),
                            "chunk_index": metadata.get('chunk_index')
                        }
                        enriched_results.append(enriched_result)
            
            # Generate LLM response
            response = self._generate_response(query, enriched_results)
            
            return {
                "query": query,
                "response": response,
                "results": enriched_results,
                "total_results": len(enriched_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "query": query,
                "response": f"Error processing query: {e}",
                "results": [],
                "total_results": 0,
                "error": str(e)
            }
    
    def _generate_response(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate response with proper source attribution"""
        if not results:
            return "I couldn't find any relevant information to answer your question."
        
        # Build context with proper source attribution
        context_parts = []
        for i, result in enumerate(results[:3], 1):
            content = result.get('content', '')[:300]
            filename = result.get('filename', 'unknown')
            doc_id = result.get('doc_id', 'unknown')
            
            context_parts.append(
                f"Source {i} (Document: {filename}, ID: {doc_id}): {content}"
            )
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""Based on the following sources, answer the user's question. 
        Always cite which document(s) you're referencing in your answer.

Sources:
{context}

Question: {query}

Answer:"""
        
        try:
            return self.llm_client.generate(prompt)
        except Exception as e:
            return f"I found relevant information but couldn't generate a response: {e}"
