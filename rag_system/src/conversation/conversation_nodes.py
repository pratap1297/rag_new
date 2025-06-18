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
            search_result = None
            
            # For contextual queries, try multiple search strategies
            if state.get('is_contextual', False):
                self.logger.info("Handling contextual query with multiple search strategies")
                
                # Strategy 1: Try with enhanced query
                self.logger.info(f"Search strategy 1: Enhanced query: '{state['processed_query']}'")
                search_result = self.query_engine.process_query(
                    state['processed_query'],
                    top_k=5
                )
                
                # Strategy 2: If no good results, try with original query
                if not search_result or not search_result.get('sources') or len(search_result.get('sources', [])) < 2:
                    self.logger.info(f"Search strategy 2: Original query: '{state['original_query']}'")
                    search_result = self.query_engine.process_query(
                        state['original_query'],
                        top_k=5
                    )
                
                # Strategy 3: If still no results, try searching for the main topic
                if not search_result or not search_result.get('sources'):
                    # Extract main topic (e.g., "building A" from "tell me more about building A")
                    topic_match = re.search(r'about\s+(.+)', state['original_query'].lower())
                    if topic_match:
                        topic = topic_match.group(1).strip()
                        self.logger.info(f"Search strategy 3: Main topic: '{topic}'")
                        search_result = self.query_engine.process_query(topic, top_k=5)
                    
                    # Also try with stored topic entities
                    if (not search_result or not search_result.get('sources')) and state.get('topic_entities'):
                        for entity in state['topic_entities'][::-1]:  # Try most recent first
                            self.logger.info(f"Search strategy 4: Topic entity: '{entity}'")
                            search_result = self.query_engine.process_query(entity, top_k=5)
                            if search_result and search_result.get('sources'):
                                break
            else:
                # Non-contextual query - proceed as normal
                self.logger.info(f"Non-contextual search: '{state['processed_query']}'")
                search_result = self.query_engine.process_query(
                    state['processed_query'],
                    top_k=5
                )
            
            # Process search results
            if search_result and search_result.get('sources'):
                sources = search_result.get('sources', [])
                search_results = []
                context_chunks = []
                
                self.logger.info(f"Processing {len(sources)} sources from search result")
                
                for i, source in enumerate(sources):
                    self.logger.info(f"Source {i+1}: filename={source.get('metadata', {}).get('filename', 'Unknown')}")
                    self.logger.info(f"Source {i+1}: text preview={source.get('text', '')[:100]}...")
                    
                    search_res = SearchResult(
                        content=source.get('text', ''),
                        score=source.get('similarity_score', source.get('score', 0)),
                        source=source.get('metadata', {}).get('filename', 'unknown'),
                        metadata=source.get('metadata', {})
                    )
                    search_results.append(search_res)
                    
                    # Add to context chunks
                    if search_res['content']:
                        context_chunks.append(search_res['content'])
                
                new_state['search_results'] = search_results
                new_state['context_chunks'] = context_chunks
                new_state['relevant_sources'] = sources
                
                # Store the query engine response separately (if available)
                new_state['query_engine_response'] = search_result.get('response', '')
                
                new_state['current_phase'] = ConversationPhase.RESPONDING
                self.logger.info(f"Found {len(search_results)} relevant sources")
            else:
                # No results found
                self.logger.info("No search results found")
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
        self.logger.info("Processing response generation node")
        
        new_state = state.copy()
        
        if not self.llm_client:
            response = "I apologize, but I'm currently unable to generate responses. Please try again later."
            return add_message_to_state(new_state, MessageType.ASSISTANT, response)
        
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
            
            # Generate follow-up questions and related topics
            new_state['suggested_questions'] = self._generate_follow_up_questions(state)
            new_state['related_topics'] = self._extract_related_topics(state)
            
            # Set response confidence
            new_state['response_confidence'] = 0.8 if state.get('search_results') else 0.6
            
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
        
        # First, check if we have a direct answer from the query engine
        # This is important for queries that need specific data correlation
        if state.get('query_engine_response') and state['query_engine_response'].strip():
            query_response = state['query_engine_response'].strip()
            
            # Check if the query engine provided a substantive answer
            # If the response is longer than 50 chars and contains useful content, use it
            if len(query_response) > 50 and not query_response.lower().startswith('i don\'t have'):
                self.logger.info("Using query engine's direct answer")
                return query_response
        
        # Check if this is a contextual query that needs conversation awareness
        if state.get('is_contextual', False):
            self.logger.info("Generating context-aware response")
            
            # Build conversation history for context
            conversation_context = self._build_conversation_context(state)
            
            # If we have search results, use them with conversation context
            if state.get('search_results') and state['search_results']:
                # Get search results context
                context_text = "\n\n".join([result['content'] for result in state['search_results'][:3]])
                
                prompt = f"""You are having a conversation with a user. Here is the recent conversation:

    {conversation_context}

    The user's latest question is: "{state['original_query']}"

    Based on the following information from the knowledge base, provide a helpful response:

    {context_text}

    Important instructions:
    - This is a follow-up question in an ongoing conversation
    - Consider what has already been discussed and provide NEW or ADDITIONAL information
    - If the user is asking for "more" information, provide details that weren't mentioned before
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
        
        # For non-contextual queries, check if we have a query engine response
        if state.get('query_engine_response') and state['query_engine_response'].strip():
            self.logger.info("Using query engine response (non-contextual query)")
            return state['query_engine_response']
        
        # If no query engine response, try to generate from search results
        if state.get('search_results') and state['search_results']:
            self.logger.info("Generating response from search results")
            
            # Check if this is a complex query requiring data correlation
            if self._is_complex_correlation_query(state['original_query']):
                # For complex queries, use a more structured prompt
                context_text = "\n\n".join([result['content'] for result in state['search_results']])
                
                prompt = f"""You need to answer a complex query that requires correlating information from multiple sources.

    Query: "{state['original_query']}"

    Available Information:
    {context_text}

    Instructions:
    1. Identify all the pieces of information needed to answer the query
    2. Extract relevant data from the provided context
    3. Connect the information logically
    4. Provide a clear, concise final answer

    If you can find all the required information, format your response with "The final answer is:" followed by the specific details requested.

    Response:"""
                
                try:
                    if self.llm_client:
                        response = self.llm_client.generate(prompt, max_tokens=500, temperature=0.1)  # Lower temperature for factual queries
                        return response.strip()
                except Exception as e:
                    self.logger.error(f"LLM generation failed: {e}")
            else:
                # Standard response generation
                context_text = "\n".join([result['content'][:500] for result in state['search_results'][:3]])
                
                prompt = f"""Based on the following information, provide a helpful response to the user's query: "{state['original_query']}"

    Context:
    {context_text}

    Please provide a clear, informative response based on the context provided."""
                
                try:
                    if self.llm_client:
                        response = self.llm_client.generate(prompt)
                        return response.strip()
                except Exception as e:
                    self.logger.error(f"LLM generation failed: {e}")
        
        # Final fallback response
        self.logger.info("Using general response fallback")
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
        if 'tell me more' in state['original_query'].lower():
            return f"I've shared the information I have about {topic} from the knowledge base. I don't have additional details beyond what was already provided. Is there something specific about {topic} you'd like to know more about?"
        else:
            return f"I couldn't find additional information about {state['original_query']} in the knowledge base. Could you please be more specific about what aspect you'd like to know?"
    
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
        """Generate follow-up questions based on the conversation"""
        
        if not state.get('topics_discussed'):
            return []
        
        recent_topics = state['topics_discussed'][-2:]
        questions = []
        
        for topic in recent_topics:
            questions.append(f"Would you like to know more about {topic}?")
            questions.append(f"How does {topic} relate to your specific needs?")
        
        return questions[:3]  # Return max 3 questions
    
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