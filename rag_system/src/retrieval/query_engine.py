"""
Query Engine - Enhanced with Conversation Context
Main engine for processing user queries and generating responses
"""
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import math
from pathlib import Path

try:
    from ..core.error_handling import RetrievalError
except ImportError:
    from rag_system.src.core.error_handling import RetrievalError

class QueryEngine:
    """Main query processing engine with conversation awareness"""
    
    def __init__(self, faiss_store, embedder, llm_client, metadata_store, config_manager, reranker=None, query_enhancer=None):
        self.faiss_store = faiss_store
        self.embedder = embedder
        self.llm_client = llm_client
        self.metadata_store = metadata_store
        self.config = config_manager.get_config()
        self.reranker = reranker
        self.query_enhancer = query_enhancer
        
        # Source diversity configuration
        self.enable_source_diversity = getattr(self.config.retrieval, 'enable_source_diversity', True)
        self.diversity_weight = getattr(self.config.retrieval, 'diversity_weight', 0.3)
        self.max_chunks_per_doc = getattr(self.config.retrieval, 'max_chunks_per_doc', 3)
        self.min_source_types = getattr(self.config.retrieval, 'min_source_types', 2)
        
        logging.info(f"Query engine initialized with reranker: {reranker is not None}, query enhancer: {query_enhancer is not None}")
        logging.info(f"Source diversity enabled: {self.enable_source_diversity}, weight: {self.diversity_weight}")
    
    def process_query(self, query: str, filters: Dict[str, Any] = None, 
                     top_k: int = None, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query and return response with sources
        
        Args:
            query: The user's query
            filters: Optional filters for search
            top_k: Number of top results to return
            conversation_context: Optional conversation context containing:
                - conversation_history: List of recent messages
                - current_topic: Current topic being discussed
                - is_contextual: Whether this is a follow-up query
                - original_query: The original unenhanced query (for contextual queries)
        """
        top_k = top_k or self.config.retrieval.top_k
        
        try:
            # Handle conversation context if provided
            if conversation_context and conversation_context.get('is_contextual', False):
                logging.info(f"Processing contextual query with conversation awareness")
                # For contextual queries, we might need to adjust the search strategy
                # but keep the original query for response generation
                original_query = conversation_context.get('original_query', query)
            else:
                original_query = query
            
            # Enhance query if enhancer is available
            enhanced_query = None
            query_variants = [(query, 1.0)]  # Default: original query with max confidence
            
            if self.query_enhancer:
                try:
                    enhanced_query = self.query_enhancer.enhance_query(query)
                    query_variants = self.query_enhancer.get_all_query_variants(enhanced_query)
                    logging.info(f"Query enhanced: {len(query_variants)} variants generated")
                except Exception as e:
                    logging.warning(f"Query enhancement failed, using original query: {e}")
            
            # Search with multiple query variants and track performance
            all_results = []
            best_variant = None
            best_variant_score = 0
            variant_performance = []
            
            for query_text, confidence in query_variants[:3]:  # Use top 3 variants
                # Generate query embedding
                query_embedding = self.embedder.embed_text(query_text)
                
                # Search for similar chunks (get more results for diversity)
                search_k = max(top_k * 3, 20) if self.enable_source_diversity else top_k
                search_results = self.faiss_store.search_with_metadata(
                    query_vector=query_embedding,
                    k=search_k
                )
                
                # Calculate variant performance score
                if search_results:
                    variant_avg_score = sum(r.get('similarity_score', 0) for r in search_results) / len(search_results)
                    variant_performance.append({
                        'query_text': query_text,
                        'confidence': confidence,
                        'avg_score': variant_avg_score,
                        'result_count': len(search_results)
                    })
                    
                    # Track best performing variant
                    if variant_avg_score > best_variant_score:
                        best_variant = query_text
                        best_variant_score = variant_avg_score
                
                # Add confidence weighting to results
                for result in search_results:
                    result['query_confidence'] = confidence
                    result['query_variant'] = query_text
                    # Adjust similarity score by query confidence
                    original_score = result.get('similarity_score', 0)
                    result['weighted_score'] = original_score * confidence
                
                all_results.extend(search_results)
            
            # Log variant performance for debugging
            if variant_performance:
                logging.info(f"Query variant performance: {variant_performance}")
                logging.info(f"Best variant: '{best_variant}' (score: {best_variant_score:.3f})")
            
            # Determine which query to use for LLM context
            # Use best variant if it's significantly better than original query
            query_for_llm = original_query
            if best_variant and best_variant_score > 0.7:
                # Check if best variant is significantly better than original
                original_variant_score = next(
                    (v['avg_score'] for v in variant_performance if v['query_text'] == original_query), 
                    0.0
                )
                
                # If original query not in variants, use a reasonable baseline
                if original_variant_score == 0.0:
                    # Use the lowest score as baseline for comparison
                    min_score = min(v['avg_score'] for v in variant_performance) if variant_performance else 0.0
                    original_variant_score = min_score * 0.8  # Assume original would be slightly worse
                
                if best_variant_score > original_variant_score * 1.2:  # 20% better threshold
                    query_for_llm = best_variant
                    logging.info(f"Using enhanced query for LLM: '{best_variant}' (score: {best_variant_score:.3f} vs original: {original_variant_score:.3f})")
                else:
                    logging.info(f"Keeping original query for LLM (enhanced not significantly better)")
            else:
                logging.info(f"Best variant score too low ({best_variant_score:.3f}), using original query")
            
            # Deduplicate and merge results
            search_results = self._merge_search_results(all_results)
            
            if not search_results:
                return self._create_empty_response(original_query)
            
            # Filter by similarity threshold (with bypass option for conversation context)
            bypass_threshold = (conversation_context and 
                               conversation_context.get('bypass_threshold', False))
            
            if bypass_threshold:
                logging.info("Bypassing similarity threshold for conversation context")
                filtered_results = search_results
            else:
                filtered_results = [
                    result for result in search_results
                    if result.get('similarity_score', 0) >= self.config.retrieval.similarity_threshold
                ]
            
            if not filtered_results:
                return self._create_empty_response(original_query)
            
            # Apply reranking if enabled and available
            if self.reranker and self.config.retrieval.enable_reranking:
                logging.info(f"Applying reranking to {len(filtered_results)} results")
                reranked_results = self.reranker.rerank(
                    query=query, 
                    documents=filtered_results, 
                    top_k=self.config.retrieval.rerank_top_k
                )
                pre_diversity_results = reranked_results
            else:
                # Take more results for diversity processing
                pre_diversity_results = filtered_results
            
            # Apply source diversity scoring and selection
            if self.enable_source_diversity:
                top_results = self._apply_source_diversity_scoring(pre_diversity_results, top_k)
            else:
                top_results = pre_diversity_results[:top_k]
            
            # Generate response using LLM with conversation context
            response = self._generate_llm_response(
                query_for_llm, 
                top_results, 
                conversation_context
            )
            
            # Calculate confidence score (now includes diversity metrics)
            confidence = self._calculate_confidence(top_results)
            
            # Calculate diversity metrics
            diversity_metrics = self._calculate_diversity_metrics(top_results)
            
            # Prepare response with enhancement info
            response_data = {
                'query': original_query,
                'response': response,
                'confidence_score': confidence,
                'confidence_level': 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low',
                'sources': self._format_sources(top_results),
                'total_sources': len(top_results),
                'diversity_metrics': diversity_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add query enhancement information if available
            if enhanced_query:
                response_data['query_enhancement'] = {
                    'intent_type': enhanced_query.intent.query_type.value,
                    'intent_confidence': enhanced_query.intent.confidence,
                    'keywords': enhanced_query.keywords,
                    'expanded_queries': enhanced_query.expanded_queries,
                    'reformulated_queries': enhanced_query.reformulated_queries,
                    'total_variants': len(query_variants),
                    'variant_performance': variant_performance,
                    'best_variant': best_variant,
                    'best_variant_score': best_variant_score,
                    'query_used_for_llm': query_for_llm,
                    'enhanced_query_used': query_for_llm != original_query
                }
            
            # Add debugging logging as suggested in con_sug.md
            logging.info(f"Query engine returning: response length={len(response)}, sources count={len(top_results)}")
            
            # Log query enhancement effectiveness
            if enhanced_query and variant_performance:
                logging.info(f"Query enhancement summary: {len(variant_performance)} variants tested, "
                           f"best score: {best_variant_score:.3f}, "
                           f"enhanced query used: {query_for_llm != original_query}")
            
            return response_data
            
        except Exception as e:
            raise RetrievalError(f"Query processing failed: {e}", details={'query': query})
    
    def _generate_llm_response(self, query: str, sources: List[Dict[str, Any]], 
                              conversation_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using LLM with retrieved sources and conversation context"""
        
        # Build context from sources with meaningful labels
        context_parts = []
        for i, source in enumerate(sources[:5]):  # Use top 5 sources
            text = source.get('text', '')
            source_label = self._get_source_label(source, i + 1)
            context_parts.append(f"{source_label}: {text}")
        
        context = "\n\n".join(context_parts)
        
        # Build conversation history if provided
        conversation_history = ""
        if conversation_context and conversation_context.get('conversation_history'):
            history_lines = []
            for msg in conversation_context['conversation_history'][-6:]:  # Last 3 exchanges
                role = msg.get('role', 'User')
                content = msg.get('content', '')
                if len(content) > 200:
                    content = content[:200] + "..."
                history_lines.append(f"{role}: {content}")
            conversation_history = "\n".join(history_lines)
        
        # Check if this is a contextual query
        is_contextual = conversation_context and conversation_context.get('is_contextual', False)
        
        # Create appropriate prompt based on context
        if is_contextual and conversation_history:
            # Contextual query with conversation history
            prompt = f"""You are having a conversation with a user. Here is the recent conversation:

{conversation_history}

The user's latest question is: "{query}"

Based on the following context from the knowledge base, provide a helpful response:

Context:
{context}

Important instructions:
- This is a follow-up question in an ongoing conversation
- Consider what has already been discussed and provide NEW or ADDITIONAL information if asked
- If the user is asking for "more" information, focus on details not mentioned before
- If the context doesn't contain additional information beyond what was discussed, acknowledge this
- Be conversational and natural
- When referencing information, mention the source file name when available

Answer:"""
        else:
            # Standard query without conversation context
            prompt = f"""Based on the following context, answer the user's question. If the context doesn't contain enough information to answer the question, say so clearly.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, accurate answer based on the context
- When referencing specific information, mention the source file name when available
- If information comes from multiple sources, acknowledge this

Answer:"""
        
        try:
            return self.llm_client.generate(prompt)
        except Exception as e:
            logging.error(f"LLM generation failed: {e}")
            return "I apologize, but I'm unable to generate a response at the moment due to a technical issue."
    
    def _get_source_label(self, source: Dict[str, Any], fallback_index: int) -> str:
        """Get the best available source label for a source with enhanced original path handling"""
        # Enhanced priority order for source labels with better original path handling
        source_options = [
            source.get('original_filename'),  # Full original filename with path (highest priority)
            source.get('original_name'),      # Just the original filename
            source.get('display_name'),       # Display name without extension
            source.get('file_path'),          # Full file path
            source.get('filename'),           # Filename from source
            source.get('source'),             # Source field
            source.get('doc_id'),             # Document ID
            f"Source {fallback_index}"        # Fallback
        ]
        
        # Return the first non-empty, non-'unknown' option
        for option in source_options:
            if option and option != 'unknown' and option != 'N/A':
                # Clean up the label for display
                if isinstance(option, str):
                    # If it's a full path, show just the filename or a shortened path
                    if '/' in option or '\\' in option:
                        # For full paths, show the last 2-3 path components
                        path_parts = option.replace('\\', '/').split('/')
                        if len(path_parts) > 3:
                            return f".../{'/'.join(path_parts[-3:])}"
                        else:
                            return option
                    else:
                        return option
                return str(option)
        
        return f"Source {fallback_index}"
    
    # ... rest of the existing methods remain the same ...
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for response with enhanced original path information"""
        formatted_sources = []
        
        for i, source in enumerate(sources):
            # Get the best source label
            source_label = self._get_source_label(source, i + 1)
            
            # Extract original path information
            original_path = (
                source.get('original_filename') or 
                source.get('original_path') or
                source.get('file_path') or
                source.get('filename', '')
            )
            
            # Determine if this is a temp file
            is_temp_file = False
            if original_path:
                is_temp_file = (
                    'Temp' in original_path or 
                    'tmp' in original_path.lower() or
                    '/tmp/' in original_path or
                    '\\temp\\' in original_path.lower()
                )
            
            # Get display name
            display_name = source.get('display_name') or Path(original_path).stem if original_path else f"Source {i + 1}"
            
            formatted_source = {
                'text': source.get('text', '')[:200] + "..." if len(source.get('text', '')) > 200 else source.get('text', ''),
                'similarity_score': source.get('similarity_score', 0),
                'rerank_score': source.get('rerank_score'),
                'original_score': source.get('original_score'),
                'metadata': source.get('metadata', {}),
                'source_type': source.get('source_type', 'unknown'),
                'doc_id': source.get('doc_id', 'unknown'),
                'chunk_id': source.get('chunk_id', 'unknown'),
                'source_label': source_label,
                'original_filename': source.get('original_filename'),
                'original_name': source.get('original_name'),
                'display_name': display_name,
                'file_path': source.get('file_path'),
                'filename': source.get('filename'),
                'is_temp_file': is_temp_file,
                'upload_source': source.get('upload_source', 'unknown'),
                'upload_timestamp': source.get('upload_timestamp')
            }
            formatted_sources.append(formatted_source)
        
        return formatted_sources
    
    def _create_empty_response(self, query: str) -> Dict[str, Any]:
        """Create response when no relevant sources found"""
        return {
            'query': query,
            'response': "I couldn't find any relevant information to answer your question. Please try rephrasing your query or check if the information exists in the knowledge base.",
            'confidence_score': 0.0,
            'confidence_level': 'low',
            'sources': [],
            'total_sources': 0,
            'timestamp': datetime.now().isoformat()
        }
    

    def _merge_search_results(self, all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate search results from multiple query variants"""
        if not all_results:
            return []
        
        # Group results by chunk_id to deduplicate
        result_groups = {}
        for result in all_results:
            chunk_id = result.get('chunk_id', 'unknown')
            
            if chunk_id not in result_groups:
                result_groups[chunk_id] = result
            else:
                # Keep result with higher weighted score
                existing = result_groups[chunk_id]
                if result.get('weighted_score', 0) > existing.get('weighted_score', 0):
                    result_groups[chunk_id] = result
        
        # Convert back to list and sort by weighted score
        merged_results = list(result_groups.values())
        merged_results.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        logging.info(f"Merged {len(all_results)} results into {len(merged_results)} unique results")
        return merged_results
    
    def _calculate_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results quality and diversity"""
        if not results:
            return 0.0
        
        # Factor 1: Average similarity scores (50% weight - reduced to make room for diversity)
        similarity_scores = [r.get('similarity_score', 0) for r in results]
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        
        # Factor 2: Enhanced source diversity metrics (30% weight - increased)
        unique_docs = set()
        unique_source_types = set()
        unique_authors = set()
        
        for result in results:
            # FIXED: Access fields directly, not through nested metadata
            doc_id = result.get('doc_id', 'unknown')
            source_type = result.get('source_type', 'unknown')
            author = result.get('author', result.get('creator', 'unknown'))
            
            unique_docs.add(doc_id)
            unique_source_types.add(source_type)
            unique_authors.add(author)
        
        # Document diversity (normalized to expected range)
        doc_diversity = min(len(unique_docs) / max(len(results) // 2, 1), 1.0)
        
        # Source type diversity
        type_diversity = min(len(unique_source_types) / max(self.min_source_types, 1), 1.0)
        
        # Author diversity
        author_diversity = min(len(unique_authors) / max(len(results) // 3, 1), 1.0)
        
        # Combined diversity score
        diversity_score = (doc_diversity * 0.5) + (type_diversity * 0.3) + (author_diversity * 0.2)
        
        # Factor 3: Score consistency - lower variance means higher confidence (15% weight)
        if len(similarity_scores) > 1:
            mean_score = avg_similarity
            variance = sum((score - mean_score) ** 2 for score in similarity_scores) / len(similarity_scores)
            consistency = max(0, 1 - (variance * 2))  # Normalize variance impact
        else:
            consistency = 1.0  # Single result has perfect consistency
        
        # Factor 4: Diversity scoring bonus (5% weight)
        diversity_bonus = 0.0
        if self.enable_source_diversity and results:
            # Check if results have diversity scores (from diversity scoring)
            has_diversity_scores = any('diversity_score' in r for r in results)
            if has_diversity_scores:
                avg_diversity_score = sum(r.get('diversity_score', 0) for r in results) / len(results)
                diversity_bonus = avg_diversity_score * 0.5  # Moderate bonus
        
        # Weighted combination
        confidence = (
            (avg_similarity * 0.5) + 
            (diversity_score * 0.3) + 
            (consistency * 0.15) + 
            (diversity_bonus * 0.05)
        )
        
        # Apply bonus for high-quality results
        high_quality_count = sum(1 for score in similarity_scores if score > 0.8)
        if high_quality_count > 0:
            quality_bonus = min(high_quality_count / len(similarity_scores) * 0.1, 0.1)
            confidence += quality_bonus
        
        # Apply penalty for low diversity (if enabled)
        if self.enable_source_diversity and len(unique_docs) == 1 and len(results) > 2:
            # Penalty for all results from single document
            diversity_penalty = 0.1
            confidence -= diversity_penalty
        
        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))
        
        logging.debug(f"Enhanced confidence calculation: avg_sim={avg_similarity:.3f}, "
                     f"diversity={diversity_score:.3f}, consistency={consistency:.3f}, "
                     f"bonus={diversity_bonus:.3f}, final={confidence:.3f}")
        
        return round(confidence, 2)
    
    def get_similar_queries(self, query: str, limit: int = 5) -> List[str]:
        """Get similar queries from query history"""
        # This would require storing query history
        # For now, return empty list
        return [] 
    
    def _apply_source_diversity_scoring(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Apply comprehensive source diversity scoring and selection"""
        if not results:
            return results
        
        # Step 1: Calculate diversity scores for all results
        scored_results = self._calculate_diversity_scores(results)
        
        # Step 2: Apply diverse source selection algorithm
        diverse_results = self._select_diverse_sources(scored_results, top_k)
        
        logging.info(f"Source diversity applied: {len(results)} -> {len(diverse_results)} results")
        return diverse_results
    
    def _calculate_diversity_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate comprehensive diversity scores for each result"""
        if not results:
            return results
        
        # Analyze source distribution
        doc_counts = Counter()
        source_type_counts = Counter()
        author_counts = Counter()
        date_counts = Counter()
        
        for result in results:
            # FIXED: Access fields directly, not through nested metadata
            doc_id = result.get('doc_id', 'unknown')
            source_type = result.get('source_type', 'unknown')
            author = result.get('author', result.get('creator', 'unknown'))
            date = result.get('created_date', result.get('date', 'unknown'))
            
            doc_counts[doc_id] += 1
            source_type_counts[source_type] += 1
            author_counts[author] += 1
            date_counts[date] += 1
        
        # Calculate diversity scores
        total_results = len(results)
        scored_results = []
        
        for result in results:
            # FIXED: Access fields directly, not through nested metadata
            doc_id = result.get('doc_id', 'unknown')
            source_type = result.get('source_type', 'unknown')
            author = result.get('author', result.get('creator', 'unknown'))
            date = result.get('created_date', result.get('date', 'unknown'))
            
            # Document diversity score (lower is better for diversity)
            doc_frequency = doc_counts[doc_id] / total_results
            doc_diversity_score = 1.0 - doc_frequency
            
            # Source type diversity score
            source_type_frequency = source_type_counts[source_type] / total_results
            source_type_diversity_score = 1.0 - source_type_frequency
            
            # Author diversity score
            author_frequency = author_counts[author] / total_results
            author_diversity_score = 1.0 - author_frequency
            
            # Temporal diversity score
            date_frequency = date_counts[date] / total_results
            temporal_diversity_score = 1.0 - date_frequency
            
            # Content diversity score (based on text similarity)
            content_diversity_score = self._calculate_content_diversity_score(result, results)
            
            # Combined diversity score (weighted average)
            diversity_score = (
                doc_diversity_score * 0.3 +
                source_type_diversity_score * 0.2 +
                author_diversity_score * 0.15 +
                temporal_diversity_score * 0.1 +
                content_diversity_score * 0.25
            )
            
            # Original relevance score
            relevance_score = result.get('rerank_score', result.get('weighted_score', result.get('similarity_score', 0)))
            
            # Combined final score (relevance + diversity)
            final_score = (relevance_score * (1 - self.diversity_weight)) + (diversity_score * self.diversity_weight)
            
            # Add scores to result
            result_copy = result.copy()
            result_copy.update({
                'diversity_score': diversity_score,
                'doc_diversity_score': doc_diversity_score,
                'source_type_diversity_score': source_type_diversity_score,
                'author_diversity_score': author_diversity_score,
                'temporal_diversity_score': temporal_diversity_score,
                'content_diversity_score': content_diversity_score,
                'relevance_score': relevance_score,
                'final_score': final_score
            })
            
            scored_results.append(result_copy)
        
        # Sort by final score (descending)
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored_results
    
    def _calculate_content_diversity_score(self, target_result: Dict[str, Any], all_results: List[Dict[str, Any]]) -> float:
        """Calculate content diversity score based on text similarity with other results"""
        target_text = target_result.get('text', '')
        if not target_text:
            return 0.5  # Neutral score for missing text
        
        # Calculate similarity with other results
        similarities = []
        for other_result in all_results:
            if other_result == target_result:
                continue
            
            other_text = other_result.get('text', '')
            if not other_text:
                continue
            
            # Simple text similarity (could be enhanced with embeddings)
            similarity = self._calculate_text_similarity(target_text, other_text)
            similarities.append(similarity)
        
        if not similarities:
            return 1.0  # Maximum diversity if no other results
        
        # Diversity is inverse of average similarity
        avg_similarity = sum(similarities) / len(similarities)
        content_diversity = 1.0 - avg_similarity
        
        return max(0.0, min(1.0, content_diversity))
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity using word overlap"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _select_diverse_sources(self, scored_results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Select diverse sources using advanced selection algorithm"""
        if not scored_results or top_k <= 0:
            return []
        
        selected = []
        seen_docs = set()
        seen_source_types = set()
        seen_authors = set()
        doc_chunk_counts = defaultdict(int)
        
        # Phase 1: Prioritize diverse sources (ensure at least one from each document/type)
        for result in scored_results:
            if len(selected) >= top_k:
                break
            
            # FIXED: Access fields directly, not through nested metadata
            doc_id = result.get('doc_id', 'unknown')
            source_type = result.get('source_type', 'unknown')
            author = result.get('author', result.get('creator', 'unknown'))
            
            # Check diversity constraints
            should_select = False
            
            # Priority 1: New document
            if doc_id not in seen_docs:
                should_select = True
                seen_docs.add(doc_id)
            
            # Priority 2: New source type
            elif source_type not in seen_source_types:
                should_select = True
                seen_source_types.add(source_type)
            
            # Priority 3: New author
            elif author not in seen_authors:
                should_select = True
                seen_authors.add(author)
            
            # Priority 4: Document under chunk limit
            elif doc_chunk_counts[doc_id] < self.max_chunks_per_doc:
                should_select = True
            
            if should_select:
                selected.append(result)
                doc_chunk_counts[doc_id] += 1
        
        # Phase 2: Fill remaining slots with best remaining results
        remaining_slots = top_k - len(selected)
        if remaining_slots > 0:
            remaining_results = [r for r in scored_results if r not in selected]
            
            # Apply stricter diversity constraints for remaining slots
            for result in remaining_results:
                if remaining_slots <= 0:
                    break
                
                # FIXED: Access fields directly, not through nested metadata
                doc_id = result.get('doc_id', 'unknown')
                
                # Only add if document is under chunk limit
                if doc_chunk_counts[doc_id] < self.max_chunks_per_doc:
                    selected.append(result)
                    doc_chunk_counts[doc_id] += 1
                    remaining_slots -= 1
        
        # Phase 3: Final ranking by combined score
        selected.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return selected[:top_k]
    
    def _prioritize_diverse_sources(self, results: List[Dict], top_k: int) -> List[Dict]:
        """Ensure diverse sources in results (legacy method for backward compatibility)"""
        return self._select_diverse_sources(results, top_k)
    
    def _calculate_diversity_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive diversity metrics for the result set"""
        if not results:
            return {
                'unique_documents': 0,
                'unique_source_types': 0,
                'unique_authors': 0,
                'document_distribution': {},
                'source_type_distribution': {},
                'author_distribution': {},
                'diversity_index': 0.0,
                'coverage_score': 0.0,
                'average_chunks_per_doc': 0.0,
                'max_chunks_from_single_doc': 0
            }
        
        # Count unique elements
        unique_docs = set()
        unique_source_types = set()
        unique_authors = set()
        doc_counts = Counter()
        source_type_counts = Counter()
        author_counts = Counter()
        
        for result in results:
            # FIXED: Access fields directly, not through nested metadata
            doc_id = result.get('doc_id', 'unknown')
            source_type = result.get('source_type', 'unknown')
            author = result.get('author', result.get('creator', 'unknown'))
            
            unique_docs.add(doc_id)
            unique_source_types.add(source_type)
            unique_authors.add(author)
            
            doc_counts[doc_id] += 1
            source_type_counts[source_type] += 1
            author_counts[author] += 1
        
        # Calculate Shannon diversity index
        total_results = len(results)
        diversity_index = 0.0
        
        for count in doc_counts.values():
            if count > 0:
                proportion = count / total_results
                diversity_index -= proportion * math.log2(proportion)
        
        # Normalize diversity index (0-1 scale)
        max_diversity = math.log2(len(unique_docs)) if len(unique_docs) > 1 else 1.0
        normalized_diversity = diversity_index / max_diversity if max_diversity > 0 else 0.0
        
        # Calculate coverage score (how well we cover different sources)
        # Use a reasonable default for expected sources
        expected_sources = max(total_results // 2, 1)
        coverage_score = min(len(unique_docs) / expected_sources, 1.0) if results else 0.0
        
        return {
            'unique_documents': len(unique_docs),
            'unique_source_types': len(unique_source_types),
            'unique_authors': len(unique_authors),
            'document_distribution': dict(doc_counts),
            'source_type_distribution': dict(source_type_counts),
            'author_distribution': dict(author_counts),
            'diversity_index': round(normalized_diversity, 3),
            'coverage_score': round(coverage_score, 3),
            'average_chunks_per_doc': round(total_results / len(unique_docs), 2) if unique_docs else 0.0,
            'max_chunks_from_single_doc': max(doc_counts.values()) if doc_counts else 0
        } 