"""
LangGraph Conversation Nodes
Individual processing nodes for the conversation flow
"""
import logging
from typing import Dict, Any, List
import re
from datetime import datetime

from .conversation_state import (
    ConversationState, ConversationPhase, MessageType, Message, SearchResult,
    add_message_to_state, get_conversation_history, should_end_conversation
)

class ConversationNodes:
    """Collection of LangGraph nodes for conversation processing"""
    
    def __init__(self, container=None):
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # Get system components
        if container:
            self.query_engine = container.get('query_engine')
            self.embedder = container.get('embedder') 
            self.llm_client = container.get('llm_client')
        else:
            self.query_engine = None
            self.embedder = None
            self.llm_client = None
    
    def greet_user(self, state: ConversationState) -> ConversationState:
        """Initial greeting and conversation setup"""
        self.logger.info("Processing greeting node")
        
        if not state['messages'] or state['turn_count'] == 0:
            # First interaction - provide greeting
            greeting = "Hello! I'm your AI assistant. I can help you find information, answer questions, and have a conversation about various topics. What would you like to know?"
            
            new_state = add_message_to_state(state, MessageType.ASSISTANT, greeting)
            new_state['current_phase'] = ConversationPhase.UNDERSTANDING
            return new_state
        
        return state
    
    def understand_intent(self, state: ConversationState) -> ConversationState:
        """Analyze user intent and extract key information"""
        self.logger.info("Processing intent understanding node")
        
        if not state['messages']:
            return state
        
        # Get latest user message
        user_messages = [msg for msg in state['messages'] if msg['type'] == MessageType.USER]
        if not user_messages:
            return state
        
        latest_message = user_messages[-1]
        user_input = latest_message['content']
        
        # Skip processing if empty message (initial greeting scenario)
        if not user_input.strip():
            self.logger.info("Empty user input detected, skipping intent analysis")
            return state
        
        # Create new state with updated values
        new_state = state.copy()
        new_state['original_query'] = user_input
        
        # Check if this is a contextual query that needs context
        if self._is_contextual_query(user_input, state):
            # Enhance query with conversation context
            enhanced_query = self._build_contextual_query(user_input, state)
            new_state['processed_query'] = enhanced_query
            new_state['is_contextual'] = True
            self.logger.info(f"Contextual query detected. Enhanced: '{enhanced_query}'")
        else:
            new_state['processed_query'] = user_input
            new_state['is_contextual'] = False
        
        # Track topic entities
        if 'building' in user_input.lower():
            match = re.search(r'building\s+([a-zA-Z0-9]+)', user_input, re.IGNORECASE)
            if match:
                new_state['current_topic'] = f"Building {match.group(1).upper()}"
                topic_entities = new_state.get('topic_entities', [])
                topic_entities.append(f"Building {match.group(1).upper()}")
                new_state['topic_entities'] = topic_entities[-5:]  # Keep last 5 entities
        
        # Extract intent patterns
        intent_patterns = {
            "greeting": [r"\b(hello|hi|hey|good morning|good afternoon)\b"],
            "question": [r"\b(what|how|when|where|why|who)\b", r"\?"],
            "search": [r"\b(find|search|look for|show me)\b"],
            "comparison": [r"\b(compare|versus|vs|difference|better)\b"],
            "explanation": [r"\b(explain|tell me about|describe)\b"],
            "help": [r"\b(help|assist|support)\b"],
            "goodbye": [r"\b(bye|goodbye|see you|farewell)\b"],
            "clarification": [r"\b(what was|repeat|again|previous)\b"],
            "follow_up": [r"\b(more|also|additionally|furthermore|tell me more)\b"]
        }
        
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input.lower()):
                    detected_intents.append(intent)
                    break
        
        # Determine primary intent
        if "goodbye" in detected_intents:
            new_state['user_intent'] = "goodbye"
            new_state['current_phase'] = ConversationPhase.ENDING
        elif "greeting" in detected_intents and state['turn_count'] <= 2:
            new_state['user_intent'] = "greeting"
            new_state['current_phase'] = ConversationPhase.GREETING
        elif "clarification" in detected_intents:
            new_state['user_intent'] = "clarification"
            new_state['current_phase'] = ConversationPhase.SEARCHING
        elif "help" in detected_intents:
            new_state['user_intent'] = "help"
            new_state['current_phase'] = ConversationPhase.RESPONDING
        else:
            # For any other query (including general statements), treat as information seeking
            new_state['user_intent'] = "information_seeking"
            new_state['current_phase'] = ConversationPhase.SEARCHING
        
        # Extract keywords
        keywords = self._extract_keywords(user_input)
        new_state['query_keywords'] = keywords
        
        # Set confidence based on intent clarity
        new_state['confidence_score'] = 0.8 if detected_intents else 0.5
        
        # Update topics discussed
        if keywords:
            new_topics = new_state['topics_discussed'] + keywords[:3]  # Add top 3 keywords
            new_state['topics_discussed'] = new_topics[-10:]  # Keep only recent topics
        
        self.logger.info(f"Intent: {new_state['user_intent']}, Keywords: {keywords}")
        self.logger.info(f"Current phase after intent: {new_state['current_phase']}")
        self.logger.info(f"Is contextual: {new_state.get('is_contextual', False)}")
        return new_state
    
    def search_knowledge(self, state: ConversationState) -> ConversationState:
        """Search for relevant information using the query engine"""
        self.logger.info("Processing knowledge search node")
        
        new_state = state.copy()
        
        if not state['processed_query'] or not self.query_engine:
            new_state['has_errors'] = True
            new_state['error_messages'] = state['error_messages'] + ["No query to search or query engine unavailable"]
            new_state['current_phase'] = ConversationPhase.RESPONDING
            new_state['requires_clarification'] = False
            new_state['search_results'] = []
            new_state['context_chunks'] = []
            return new_state

        try:
            # Create conversation context with bypass threshold for conversation queries
            conversation_context = {
                'bypass_threshold': True,  # Bypass similarity threshold for conversation consistency
                'is_contextual': state.get('is_contextual', False),
                'conversation_history': state.get('messages', [])
            }
            
            # For contextual queries, try multiple search strategies
            if state.get('is_contextual', False):
                self.logger.info("Handling contextual query with multiple search strategies")
                
                # Strategy 1: Try with enhanced query
                self.logger.info(f"Search strategy 1: Enhanced query: '{state['processed_query']}'")
                search_result = self.query_engine.process_query(
                    state['processed_query'],
                    top_k=5,
                    conversation_context=conversation_context
                )
                
                # Strategy 2: If no good results, try with original query
                if not search_result or not search_result.get('sources') or len(search_result.get('sources', [])) < 2:
                    self.logger.info(f"Search strategy 2: Original query: '{state['original_query']}'")
                    search_result = self.query_engine.process_query(
                        state['original_query'],
                        top_k=5,
                        conversation_context=conversation_context
                    )
                
                # Strategy 3: If still no results, try searching for the main topic
                if not search_result or not search_result.get('sources'):
                    # Extract main topic (e.g., "building A" from "tell me more about building A")
                    topic_match = re.search(r'about\s+(.+)', state['original_query'].lower())
                    if topic_match:
                        topic = topic_match.group(1).strip()
                        self.logger.info(f"Search strategy 3: Main topic: '{topic}'")
                        search_result = self.query_engine.process_query(
                            topic, 
                            top_k=5,
                            conversation_context=conversation_context
                        )
                    
                    # Also try with stored topic entities
                    if (not search_result or not search_result.get('sources')) and state.get('topic_entities'):
                        for entity in state['topic_entities'][::-1]:  # Try most recent first
                            self.logger.info(f"Search strategy 4: Topic entity: '{entity}'")
                            search_result = self.query_engine.process_query(
                                entity, 
                                top_k=5,
                                conversation_context=conversation_context
                            )
                            if search_result and search_result.get('sources'):
                                break
            else:
                # Non-contextual query - proceed as normal with bypass
                self.logger.info(f"Non-contextual search: '{state['processed_query']}'")
                search_result = self.query_engine.process_query(
                    state['processed_query'],
                    top_k=5,
                    conversation_context=conversation_context
                )
            
            # Log the search result structure for debugging
            self.logger.info(f"Search result type: {type(search_result)}")
            self.logger.info(f"Search result keys: {list(search_result.keys()) if isinstance(search_result, dict) else 'Not a dict'}")
            
            # The query engine returns a dict with 'response' and 'sources'
            if search_result and isinstance(search_result, dict):
                # Check if we have sources
                sources = search_result.get('sources', [])
                
                if sources:
                    search_results = []
                    context_chunks = []
                    
                    self.logger.info(f"Processing {len(sources)} sources from search result")
                    
                    for i, source in enumerate(sources):
                        # The source format from query_engine includes these fields
                        search_res = SearchResult(
                            content=source.get('text', ''),  # Note: query_engine uses 'text' field
                            score=source.get('similarity_score', source.get('score', 0)),
                            source=source.get('source', source.get('metadata', {}).get('filename', 'unknown')),
                            metadata=source.get('metadata', {})
                        )
                        search_results.append(search_res)
                        
                        # Add to context chunks
                        if search_res['content']:
                            context_chunks.append(search_res['content'])
                    
                    new_state['search_results'] = search_results
                    new_state['context_chunks'] = context_chunks
                    new_state['relevant_sources'] = sources
                    
                    # Store the query engine response if available
                    response = search_result.get('response', '')
                    new_state['query_engine_response'] = response if isinstance(response, str) else ''
                    
                    self.logger.info(f"Found {len(search_results)} relevant sources")
                else:
                    # No sources found, but we might have a response
                    self.logger.info("No sources found in search result")
                    new_state['search_results'] = []
                    new_state['context_chunks'] = []
                    response = search_result.get('response', '')
                    new_state['query_engine_response'] = response if isinstance(response, str) else ''
                
                new_state['current_phase'] = ConversationPhase.RESPONDING
            else:
                # Invalid search result format
                self.logger.warning(f"Invalid search result format: {type(search_result)}")
                new_state['current_phase'] = ConversationPhase.RESPONDING
                new_state['requires_clarification'] = False
                new_state['search_results'] = []
                new_state['context_chunks'] = []
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            new_state['has_errors'] = True
            new_state['error_messages'] = state['error_messages'] + [f"Search error: {str(e)}"]
            new_state['current_phase'] = ConversationPhase.RESPONDING
        
        return new_state
    
    def generate_response(self, state: ConversationState) -> ConversationState:
        """Generate response using LLM with retrieved context"""
        self.logger.info("🎯 GENERATE_RESPONSE METHOD CALLED 🎯")
        self.logger.info("Processing response generation node")
        
        new_state = state.copy()
        
        if not self.llm_client:
            # Even without LLM client, we can still provide a response using search results with source info
            if state.get('search_results') and state['search_results']:
                # Use the first search result with source attribution
                first_result = state['search_results'][0]
                source = first_result.get('source', 'Unknown source')
                content = first_result['content'][:300]
                response = f"Based on information from {source}: {content}..."
                self.logger.info("Generated response using search results without LLM")
            else:
                response = "I apologize, but I couldn't find relevant information to answer your question."
                self.logger.info("No search results available for response generation")
            
            # Preserve all search-related data when adding the response
            response_state = add_message_to_state(new_state, MessageType.ASSISTANT, response)
            # Ensure search_results are preserved in the response state
            if state.get('search_results'):
                response_state['search_results'] = state['search_results']
            if state.get('context_chunks'):
                response_state['context_chunks'] = state['context_chunks']
            if state.get('query_engine_response'):
                response_state['query_engine_response'] = state['query_engine_response']
            
            return response_state
        
        try:
            if state['user_intent'] == "goodbye":
                response = self._generate_farewell_response(state)
            elif state['user_intent'] == "greeting":
                response = self._generate_greeting_response(state)
            elif state['user_intent'] == "help":
                response = self._generate_help_response(state)
            else:
                # Generate contextual response based on search results
                response = self._generate_contextual_response(state)
            
            # Add response to conversation
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, response)
            
            # Set the conversation phase to RESPONDING to indicate we've generated a response
            new_state['current_phase'] = ConversationPhase.RESPONDING
            
            # Only generate follow-up questions and related topics occasionally to reduce LLM calls
            # Use turn count to determine when to generate suggestions (every 3 turns)
            if state.get('turn_count', 0) % 3 == 0:
                self.logger.info("🚀 Generating follow-up questions")
                new_state['suggested_questions'] = self._generate_follow_up_questions(state)
                self.logger.info(f"🎯 Generated {len(new_state['suggested_questions'])} suggested questions")
                new_state['related_topics'] = self._extract_related_topics(state)
            else:
                # Reuse previous suggestions if available
                new_state['suggested_questions'] = state.get('suggested_questions', [])
                new_state['related_topics'] = state.get('related_topics', [])
            
            # Set response confidence
            new_state['response_confidence'] = 0.8 if state.get('search_results') else 0.6
            
            # Log source information for debugging
            if state.get('search_results'):
                sources = [r.get('source', 'Unknown') for r in state['search_results'][:3]]
                self.logger.info(f"Response generated using sources: {sources}")
            else:
                self.logger.info("Response generated without search results")
            
            self.logger.info("Response generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            error_response = "I apologize, but I encountered an error generating a response. Please try rephrasing your question."
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, error_response)
            new_state['has_errors'] = True
            new_state['error_messages'] = state['error_messages'] + [str(e)]
        
        return new_state
    
    def handle_clarification(self, state: ConversationState) -> ConversationState:
        """Handle requests for clarification"""
        self.logger.info("Processing clarification node")
        
        clarification = "I'd like to help you better. Could you provide more specific details about what you're looking for?"
        
        if state.get('clarification_questions'):
            clarification = f"{clarification} For example: {', '.join(state['clarification_questions'][:2])}"
        
        new_state = add_message_to_state(state, MessageType.ASSISTANT, clarification)
        new_state['current_phase'] = ConversationPhase.CLARIFYING
        return new_state
    
    def check_conversation_end(self, state: ConversationState) -> ConversationState:
        """Check if conversation should end"""
        self.logger.info("Processing conversation end check")
        
        new_state = state.copy()
        
        if should_end_conversation(state):
            farewell = "Thank you for our conversation! Feel free to ask if you have any other questions."
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, farewell)
            new_state['current_phase'] = ConversationPhase.ENDING
        
        return new_state
    
    def _is_contextual_query(self, query: str, state: ConversationState) -> bool:
        """Determine if a query needs context from previous messages"""
        query_lower = query.lower()
        
        # Patterns that indicate contextual queries
        contextual_patterns = [
            r'^(tell me more|more about|what about|how about)',
            r'^(more information|additional information|additional details)',
            r'^(just|only|specifically)',
            r'^(list|show|give me)',
            r'(that|this|those|these|it|them)',
            r'^(for floor|on floor|in floor)',
            r'^(yes|no|correct|right)',
            r'(previous|earlier|before)',
            r'^(and |also |additionally)',
            r'^(what else|anything else)',
            r'^(continue|go on)'
        ]
        
        for pattern in contextual_patterns:
            if re.search(pattern, query_lower):
                self.logger.info(f"Contextual pattern matched: {pattern}")
                return True
        
        # Check if query is very short and likely refers to previous context
        if len(query.split()) <= 4 and state['turn_count'] > 1:
            self.logger.info("Short query detected with conversation history - treating as contextual")
            return True
            
        # If we have previous messages, always consider some level of context
        if state.get('messages') and len(state.get('messages', [])) > 2:
            self.logger.info("Conversation has history - treating with partial context")
            # Not fully contextual but we'll maintain some conversation awareness
            return True
        
        return False
    
    def _build_contextual_query(self, current_query: str, state: ConversationState) -> str:
        """Build a query that includes context from previous messages"""
        self.logger.info(f"Building contextual query from: '{current_query}'")
        
        # Get recent conversation history
        recent_messages = state['messages'][-4:]  # Last 2 exchanges
        
        # Extract the main topic from recent messages
        context_parts = []
        previous_topics = []
        
        for msg in recent_messages:
            if msg['type'] == MessageType.USER:
                # Store the actual content for context
                previous_topics.append(msg['content'])
                
                # Look for specific topics mentioned
                if 'building' in msg['content'].lower():
                    match = re.search(r'building\s+([a-zA-Z0-9]+)', msg['content'], re.IGNORECASE)
                    if match:
                        context_parts.append(f"Building {match.group(1).upper()}")
                
                if 'access point' in msg['content'].lower() or 'ap' in msg['content'].lower():
                    context_parts.append("access points")
                    
            elif msg['type'] == MessageType.ASSISTANT:
                # Extract topics from assistant responses too
                if 'cisco' in msg['content'].lower():
                    context_parts.append("Cisco access points")
                if '3802' in msg['content']:
                    context_parts.append("Cisco 3802I 3802E")
                if '1562' in msg['content']:
                    context_parts.append("Cisco 1562E")
        
        # For "tell me more" type queries, we need to enhance differently
        if re.search(r'^(tell me more|more about|what else)', current_query.lower()):
            # Find what topic they're asking more about
            topic_match = re.search(r'about\s+(.+)', current_query.lower())
            if topic_match:
                topic = topic_match.group(1).strip()
                # If they're asking about a topic we've discussed, search for more details
                if context_parts:
                    # Create a comprehensive search query
                    enhanced = f"{topic} {' '.join(context_parts)} details specifications features"
                else:
                    enhanced = f"{topic} detailed information"
            else:
                # General "tell me more" - use all context
                enhanced = f"additional information about {' '.join(context_parts)}"
        elif current_query.lower().startswith(('just list', 'only list', 'list')):
            # Handle list requests with context
            context_str = " ".join(set(context_parts))  # Remove duplicates
            if 'floor' in current_query.lower() and any('building' in part.lower() for part in context_parts):
                # "Just list for Floor 1" -> "Building A Floor 1 access points list"
                enhanced = f"{context_str} {current_query}"
            else:
                enhanced = f"{current_query} for {context_str}"
        elif len(current_query.split()) <= 4 and context_parts:
            # Short query - add full context
            context_str = " ".join(set(context_parts))
            enhanced = f"{current_query} {context_str}"
        else:
            # Other contextual queries
            context_str = " ".join(set(context_parts))  # Remove duplicates
            enhanced = f"{current_query} (context: {context_str})"
        
        self.logger.info(f"Enhanced query to: '{enhanced}'")
        return enhanced
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'how', 'what', 'when', 'where', 'why', 'who', 'tell', 'me', 'about', 'more'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        return keywords[:10]  # Return top 10 keywords
    
    def _generate_contextual_response(self, state: ConversationState) -> str:
        """Generate response based on search results and context"""
        
        # First check if we have a response from the query engine
        query_engine_response = state.get('query_engine_response')
        if query_engine_response and isinstance(query_engine_response, str) and query_engine_response.strip():
            self.logger.info("Using query engine response directly")
            return query_engine_response
        
        # Check if this is a contextual query that needs conversation awareness
        if state.get('is_contextual', False):
            self.logger.info("Generating context-aware response")
            
            # Build conversation history for context
            conversation_context = self._build_conversation_context(state)
            
            # If we have search results, use them with conversation context
            if state.get('search_results') and state['search_results']:
                # Enhanced search results context with source information
                context_parts = []
                for i, result in enumerate(state['search_results'][:3], 1):
                    content = result.get('content', '')[:400] if result.get('content') else ''
                    source = result.get('source', 'Unknown')
                    score = result.get('score', 0)
                    
                    context_parts.append(f"Source {i} ({source}, relevance: {score:.2f}):\n{content}")
                
                context_text = "\n\n".join(context_parts)
                
                original_query = state.get('original_query', '')
                prompt = f"""You are having a conversation with a user. Here is the recent conversation:

{conversation_context}

The user's latest question is: "{original_query}"

Based on the following information from the knowledge base, provide a helpful response:

{context_text}

Important instructions:
- This is a follow-up question in an ongoing conversation
- Consider what has already been discussed and provide NEW or ADDITIONAL information
- If the user is asking for "more" information, provide details that weren't mentioned before
- Reference specific sources when mentioning facts or data (e.g., "According to the Facility_Managers_2024.xlsx file...")
- If information comes from a specific document, mention it by name
- If the information requested isn't available in the knowledge base, acknowledge this clearly
- Be conversational and reference the previous discussion naturally

Response:"""
                
                try:
                    if self.llm_client:
                        response = self.llm_client.generate(prompt, max_tokens=500, temperature=0.7)
                        return response.strip()
                except Exception as e:
                    self.logger.error(f"LLM generation failed: {e}")
            else:
                # No search results for contextual query
                return self._generate_no_results_contextual_response(state)
        
        # If no query engine response, generate from search results
        if state.get('search_results') and state['search_results']:
            self.logger.info("Generating response from search results")
            
            # Check if this is a complex query requiring data correlation
            if self._is_complex_correlation_query(state['original_query']):
                # For complex queries, use enhanced context with source attribution
                context_parts = []
                for i, result in enumerate(state['search_results'], 1):
                    content = result['content'][:500]
                    source = result.get('source', 'Unknown')
                    score = result.get('score', 0)
                    
                    context_parts.append(f"Source {i} ({source}, relevance: {score:.2f}):\n{content}")
                
                context_text = "\n\n".join(context_parts)
                
                prompt = f"""You need to answer a complex query that requires correlating information from multiple sources.

Query: "{state['original_query']}"

Available Information from Multiple Sources:
{context_text}

Instructions:
1. Identify all the pieces of information needed to answer the query
2. Extract relevant data from the provided sources, noting which source each piece comes from
3. Connect the information logically across sources
4. Reference specific sources in your answer (e.g., "According to Source 1 (filename.xlsx)...")
5. Provide a clear, concise final answer with source attribution

If you can find all the required information, format your response with "The final answer is:" followed by the specific details requested with source references.

Response:"""
                
                try:
                    if self.llm_client:
                        response = self.llm_client.generate(prompt, max_tokens=500, temperature=0.1)  # Lower temperature for factual queries
                        return response.strip()
                except Exception as e:
                    self.logger.error(f"LLM generation failed: {e}")
            else:
                # Enhanced response generation with source information
                context_parts = []
                for i, result in enumerate(state['search_results'][:3], 1):
                    content = result['content'][:400]
                    source = result.get('source', 'Unknown')
                    score = result.get('score', 0)
                    
                    # Include source context for better responses
                    context_parts.append(f"Source {i} ({source}, relevance: {score:.2f}):\n{content}")
                
                context_text = "\n\n".join(context_parts)
                
                prompt = f"""Based on the following information from multiple sources, provide a helpful response to the user's query: "{state['original_query']}"

Available Information:
{context_text}

Instructions:
- Use the source information to provide accurate, well-attributed responses
- Reference specific sources when mentioning facts or data
- If information comes from a specific document (like an Excel file), mention it
- Provide a comprehensive answer that utilizes information from all relevant sources

Please provide a clear, informative response based on the context provided."""
                
                try:
                    if self.llm_client:
                        response = self.llm_client.generate(prompt, max_tokens=500, temperature=0.7)
                        return response.strip()
                except Exception as e:
                    self.logger.error(f"LLM generation failed: {e}")
        
        # Fallback response
        return self._generate_general_response(state)
    
    def _build_conversation_context(self, state: ConversationState) -> str:
        """Build a summary of the conversation for context"""
        recent_messages = state['messages'][-6:]  # Last 3 exchanges
        
        context_lines = []
        for msg in recent_messages:
            role = "User" if msg['type'] == MessageType.USER else "Assistant"
            # Truncate long messages
            content = msg['content']
            if len(content) > 200:
                content = content[:200] + "..."
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def _generate_no_results_contextual_response(self, state: ConversationState) -> str:
        """Generate response when no results found for contextual query"""
        # Get the topic from conversation
        topic = state.get('current_topic', 'that topic')
        
        # Check what the user is asking for
        original_query = state.get('original_query', '')
        if original_query and 'tell me more' in original_query.lower():
            return f"I've shared the information I have about {topic} from the knowledge base. I don't have additional details beyond what was already provided. Is there something specific about {topic} you'd like to know more about?"
        else:
            return f"I couldn't find additional information about {original_query} in the knowledge base. Could you please be more specific about what aspect you'd like to know?"
    
    def _generate_greeting_response(self, state: ConversationState) -> str:
        """Generate greeting response"""
        greetings = [
            "Hello! How can I help you today?",
            "Hi there! What would you like to know?",
            "Greetings! I'm here to assist you with any questions you might have.",
            "Hello! Feel free to ask me anything you'd like to know about."
        ]
        
        # Simple selection based on turn count
        return greetings[state['turn_count'] % len(greetings)]
    
    def _generate_farewell_response(self, state: ConversationState) -> str:
        """Generate farewell response"""
        farewells = [
            "Goodbye! It was great talking with you.",
            "Thank you for the conversation! Have a wonderful day!",
            "Farewell! Feel free to come back anytime you have questions.",
            "Goodbye! I hope I was able to help you today."
        ]
        
        return farewells[state['turn_count'] % len(farewells)]
    
    def _generate_help_response(self, state: ConversationState) -> str:
        """Generate help response"""
        return """I'm here to help you with various tasks! Here's what I can do:

• Answer questions about topics in my knowledge base
• Help you find specific information
• Provide explanations and clarifications
• Have conversations about various subjects

Just ask me anything you'd like to know, and I'll do my best to provide a helpful response!"""
    
    def _generate_general_response(self, state: ConversationState) -> str:
        """Generate general response when no specific context is available"""
        
        query = state['original_query']
        
        if not query:
            return "I'd be happy to help! Could you please tell me what you'd like to know about?"
        
        # Generate a helpful response acknowledging the query
        return f"""I understand you're asking about "{query}". While I don't have specific information readily available on this topic right now, I'd be happy to help you in other ways. 

Could you provide more details about what specifically you'd like to know? This would help me give you a more targeted response."""
    
    def _generate_follow_up_questions(self, state: ConversationState) -> List[str]:
        """Generate intelligent follow-up questions using LLM and search context"""
        
        self.logger.info("🔥 FOLLOW-UP QUESTIONS METHOD CALLED 🔥")
        
        # Check if we should skip LLM generation to reduce API calls
        # Only generate new questions every few turns or when we have new search results
        turn_count = state.get('turn_count', 0)
        has_new_search_results = len(state.get('search_results', [])) > 0
        
        # If we have previous suggestions and it's not time to refresh, reuse them
        if (state.get('suggested_questions') and 
            len(state.get('suggested_questions', [])) >= 2 and 
            turn_count % 3 != 0 and 
            not has_new_search_results):
            self.logger.info("Reusing existing suggested questions to reduce LLM calls")
            return state.get('suggested_questions')
        
        try:
            self.logger.info("Starting follow-up question generation")
            
            # If no LLM client, return basic fallback questions
            if not self.llm_client:
                self.logger.warning("No LLM client available, using fallback questions")
                return self._generate_fallback_follow_up_questions(state)
            
            # Get context from search results and conversation
            context_info = self._build_suggestion_context(state)
            self.logger.info(f"Built context info with length: {len(context_info)}")
            
            if not context_info:
                self.logger.warning("No context info available, using fallback questions")
                return self._generate_fallback_follow_up_questions(state)
            
            # Create a focused prompt for generating relevant follow-up questions
            prompt = f"""Based on the user's question and the information found, generate 3-4 intelligent follow-up questions that would be genuinely helpful.

User's Question: "{state.get('original_query', '')}"

Information Found:
{context_info[:1000]}

Generate follow-up questions that:
1. Explore specific details mentioned in the information
2. Ask about practical applications or next steps
3. Clarify relationships between entities/concepts

Make the questions specific, actionable, and based on the actual content found. Avoid generic questions.

Format as a simple list:
- Question 1
- Question 2
- Question 3"""

            self.logger.info("Sending prompt to LLM for follow-up questions")
            response = self.llm_client.generate(prompt, max_tokens=200, temperature=0.7)
            self.logger.info(f"LLM response length: {len(response)}")
            
            # Parse the questions from the response
            questions = self._parse_follow_up_questions(response)
            self.logger.info(f"Parsed {len(questions)} questions from LLM response")
            
            if questions:
                self.logger.info(f"Generated {len(questions)} contextual follow-up questions")
                return questions
            else:
                self.logger.warning("Failed to parse LLM-generated questions, using fallback")
                return self._generate_fallback_follow_up_questions(state)
                
        except Exception as e:
            self.logger.error(f"Error generating follow-up questions: {e}")
            return self._generate_fallback_follow_up_questions(state)
    
    def _extract_related_topics(self, state: ConversationState) -> List[str]:
        """Extract related topics from search results and conversation context"""
        
        related_topics = []
        
        # Extract topics from search results
        if state.get('search_results'):
            for result in state['search_results'][:3]:  # Top 3 results
                content = result.get('content', '')
                
                # Extract specific topics based on content patterns
                if 'building' in content.lower():
                    # Extract building references
                    building_matches = re.findall(r'building\s+([a-zA-Z0-9]+)', content, re.IGNORECASE)
                    for match in building_matches:
                        related_topics.append(f"Building {match.upper()}")
                
                if 'cisco' in content.lower():
                    # Extract Cisco model references
                    cisco_matches = re.findall(r'cisco\s+(\w+)', content, re.IGNORECASE)
                    for match in cisco_matches:
                        if match not in ['access', 'point', 'points']:
                            related_topics.append(f"Cisco {match}")
                
                if 'access point' in content.lower() or 'ap' in content.lower():
                    related_topics.append("Access Points")
                
                if 'employee' in content.lower():
                    related_topics.append("Employee Records")
                
                if 'incident' in content.lower():
                    related_topics.append("Incidents")
                
                if 'certification' in content.lower():
                    related_topics.append("Certifications")
                
                if 'manager' in content.lower():
                    related_topics.append("Management")
        
        # Extract topics from current query
        query = state.get('original_query', '').lower()
        if 'antenna' in query:
            related_topics.append("External Antennas")
        if 'model' in query:
            related_topics.append("Equipment Models")
        if 'specification' in query:
            related_topics.append("Technical Specifications")
        
        # Add topics from conversation history
        if state.get('topics_discussed'):
            related_topics.extend(state['topics_discussed'][-3:])  # Last 3 topics
        
        # Remove duplicates and limit to 5 topics
        unique_topics = []
        seen = set()
        for topic in related_topics:
            if topic.lower() not in seen:
                unique_topics.append(topic)
                seen.add(topic.lower())
        
        return unique_topics[:5]
    
    def _build_suggestion_context(self, state: ConversationState) -> str:
        """Build context information for generating suggestions"""
        context_parts = []
        
        # Add enhanced search results context with metadata
        if state.get('search_results'):
            context_parts.append("=== SEARCH RESULTS ===")
            for i, result in enumerate(state['search_results'][:3], 1):
                content_preview = result.get('content', '')[:250]
                source = result.get('source', 'Unknown')
                score = result.get('score', 0)
                metadata = result.get('metadata', {})
                
                context_parts.append(f"Result {i} (Score: {score:.2f}, Source: {source}):")
                context_parts.append(content_preview + "...")
                
                # Include relevant metadata for better context
                if metadata:
                    meta_info = []
                    if metadata.get('doc_path'):
                        meta_info.append(f"Document: {metadata['doc_path']}")
                    if metadata.get('filename'):
                        meta_info.append(f"File: {metadata['filename']}")
                    if metadata.get('chunk_index') is not None:
                        meta_info.append(f"Section: {metadata['chunk_index']}")
                    
                    if meta_info:
                        context_parts.append(f"Metadata: {', '.join(meta_info)}")
                
                context_parts.append("")
        
        # Add conversation context if available
        if state.get('messages') and len(state['messages']) > 1:
            context_parts.append("=== CONVERSATION CONTEXT ===")
            recent_messages = state['messages'][-4:]  # Last 2 exchanges
            for msg in recent_messages:
                role = "User" if msg['type'] == MessageType.USER else "Assistant"
                content = msg['content'][:150]
                context_parts.append(f"{role}: {content}...")
            context_parts.append("")
        
        # Add any entities or topics mentioned
        if state.get('extracted_entities'):
            context_parts.append("=== ENTITIES MENTIONED ===")
            context_parts.append(", ".join(state['extracted_entities'][:5]))
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _parse_follow_up_questions(self, response: str) -> List[str]:
        """Parse follow-up questions from LLM response"""
        questions = []
        
        # Split by lines and look for questions
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith('=') or line.startswith('#'):
                continue
            
            # Remove list markers
            line = re.sub(r'^[-•*\d.]+\s*', '', line)
            
            # Check if it's a question
            if line.endswith('?') and len(line) > 10:
                # Clean up the question
                question = line.strip()
                if question and question not in questions:
                    questions.append(question)
        
        return questions[:4]  # Return max 4 questions
    
    def _generate_fallback_follow_up_questions(self, state: ConversationState) -> List[str]:
        """Generate fallback questions when LLM approach fails"""
        original_query = state.get('original_query', '').lower()
        questions = []
        
        # Generate based on query type and search results
        if 'who is' in original_query or 'who are' in original_query:
            if state.get('search_results'):
                # Extract name from query for more specific questions
                name_match = re.search(r'who is\s+([^?]+)', original_query, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                    # Generate smart questions based on what we found in search results
                    content_analysis = ""
                    for result in state['search_results'][:2]:
                        content_analysis += result.get('content', '')[:300]
                    
                    questions = []
                    if 'manager' in content_analysis.lower() or 'floor' in content_analysis.lower():
                        questions.append(f"What specific responsibilities does {name} have as a manager?")
                        questions.append(f"Which team members report to {name}?")
                    if 'building' in content_analysis.lower():
                        questions.append(f"What other staff work in the same building as {name}?")
                    if 'contact' in content_analysis.lower() or 'phone' in content_analysis.lower():
                        questions.append(f"What's the best way to reach {name} for urgent matters?")
                    if 'certification' in content_analysis.lower():
                        questions.append(f"What other certifications or qualifications does {name} have?")
                    
                    # Fill with generic questions if we don't have enough specific ones
                    if len(questions) < 3:
                        questions.extend([
                            f"What projects is {name} currently working on?",
                            f"Who are {name}'s key contacts and collaborators?",
                            f"What is {name}'s availability and working schedule?"
                        ])
                    
                    questions = questions[:4]  # Limit to 4 questions
                else:
                    questions = [
                        "What is their role and main responsibilities?",
                        "What team or department are they part of?",
                        "How can I contact them?",
                        "What are their key qualifications?"
                    ]
            else:
                questions = [
                    "Can you provide more details about this person?",
                    "What specific information are you looking for?",
                    "Would you like me to search for related contacts?",
                    "Is there a particular context or department you're interested in?"
                ]
        
        elif 'what is' in original_query or 'what are' in original_query:
            if state.get('search_results'):
                questions = [
                    "What are the specific technical details?",
                    "How is this used in practice?",
                    "What are the key features or specifications?",
                    "Are there different types or variations?"
                ]
            else:
                questions = [
                    "Can you be more specific about what aspect you're interested in?",
                    "What particular details would be most helpful?",
                    "Is there a specific context or use case you're considering?",
                    "Would you like me to search for related information?"
                ]
        
        elif 'how' in original_query:
            if state.get('search_results'):
                questions = [
                    "What are the specific step-by-step instructions?",
                    "What tools or resources are needed?",
                    "Are there any prerequisites or requirements?",
                    "What are common challenges or troubleshooting tips?"
                ]
            else:
                questions = [
                    "What specific aspect of the process interests you most?",
                    "Are you looking for general guidance or specific instructions?",
                    "What's your current level of experience with this?",
                    "Would you like me to find detailed documentation?"
                ]
        
        else:
            # Generic questions based on whether we have results
            if state.get('search_results'):
                questions = [
                    "Would you like more detailed information about this topic?",
                    "Are there specific aspects you'd like me to elaborate on?",
                    "How does this relate to your specific needs or project?",
                    "Would you like to explore related topics or concepts?"
                ]
            else:
                questions = [
                    "Can you provide more specific details about what you're looking for?",
                    "What particular aspect would be most helpful to know about?",
                    "Is there additional context that might help me find better information?",
                    "Would you like me to search for related topics?"
                ]
        
        return questions[:4]  # Return max 4 questions
    
    def _is_complex_correlation_query(self, query: str) -> bool:
        """Determine if a query requires complex data correlation"""
        query_lower = query.lower()
        
        # Patterns that indicate complex correlation queries
        complex_patterns = [
            r'find.+then.+identify',  # Find X then identify Y
            r'find.+and.+list',        # Find X and list Y
            r'identify.+associated.+with',  # Identify X associated with Y
            r'match.+with.+from',      # Match X with Y from Z
            r'correlate',              # Explicit correlation request
            r'cross-reference',        # Cross-reference request
            r'link.+to.+and',         # Link X to Y and Z
            r'which.+has.+and.+also'  # Which X has Y and also Z
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check for multi-step queries
        if all(word in query_lower for word in ['find', 'then', 'list']):
            return True
        
        # Check for queries asking for multiple related pieces of information
        if query_lower.count('and') >= 2 and any(word in query_lower for word in ['identify', 'list', 'find']):
            return True
        
        return False