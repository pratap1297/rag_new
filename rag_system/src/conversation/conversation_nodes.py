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
        new_state['processed_query'] = user_input
        
        # Extract intent patterns
        intent_patterns = {
            "greeting": [r"\b(hello|hi|hey|good morning|good afternoon)\b"],
            "question": [r"\b(what|how|when|where|why|who)\b", r"\?"],
            "search": [r"\b(find|search|look for|show me)\b"],
            "comparison": [r"\b(compare|versus|vs|difference|better)\b"],
            "explanation": [r"\b(explain|tell me about|describe)\b"],
            "help": [r"\b(help|assist|support)\b"],
            "goodbye": [r"\b(bye|goodbye|see you|farewell)\b"]
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
        elif "help" in detected_intents:
            new_state['user_intent'] = "help"
            new_state['current_phase'] = ConversationPhase.RESPONDING
        else:
            # For any other query (including general statements), treat as information seeking
            # This ensures we always try to search the knowledge base first
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
        return new_state
    
    def search_knowledge(self, state: ConversationState) -> ConversationState:
        """Search for relevant information using the query engine"""
        self.logger.info("Processing knowledge search node")
        
        new_state = state.copy()
        
        if not state['processed_query'] or not self.query_engine:
            new_state['has_errors'] = True
            new_state['error_messages'] = state['error_messages'] + ["No query to search or query engine unavailable"]
            # Set up for response generation even when query engine is unavailable
            new_state['current_phase'] = ConversationPhase.RESPONDING
            new_state['requires_clarification'] = False
            new_state['search_results'] = []
            new_state['context_chunks'] = []
            return new_state
        
        try:
            # Enhance query with conversation context
            enhanced_query = self._enhance_query_with_context(state)
            
            # Perform search using query engine
            search_result = self.query_engine.process_query(
                enhanced_query,
                top_k=5
            )
            
            # Debug: Log what we got from the search
            self.logger.info(f"Search result keys: {list(search_result.keys()) if search_result else 'None'}")
            if search_result:
                sources_count = len(search_result.get('sources', [])) if search_result.get('sources') else 0
                self.logger.info(f"Sources count: {sources_count}")
            
            # Process search results - check if we have a valid search result
            if search_result and 'response' in search_result:
                # Use the response from the query engine directly
                new_state['generated_response'] = search_result['response']
                new_state['relevant_sources'] = search_result.get('sources', [])
                new_state['context_chunks'] = []
                new_state['search_results'] = []
                
                # Store the original search result for later use
                new_state['original_search_result'] = search_result
                
                # Process sources if available
                sources = search_result.get('sources', [])
                if sources:
                    search_results = []
                    context_chunks = []
                    for source in sources:
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
                
                new_state['current_phase'] = ConversationPhase.RESPONDING
                self.logger.info(f"Using query engine response with {len(new_state['search_results'])} sources from original result")
            else:
                # No valid search result
                self.logger.info("No valid search result received, will generate fallback response")
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
                # Use existing response from search if available, otherwise generate new one
                if state.get('generated_response'):
                    response = state['generated_response']
                else:
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
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'how', 'what', 'when', 'where', 'why', 'who'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        return keywords[:10]  # Return top 10 keywords
    
    def _enhance_query_with_context(self, state: ConversationState) -> str:
        """Enhance query with conversation context"""
        base_query = state['processed_query']
        
        # Add context from recent topics
        if state['topics_discussed']:
            recent_topics = state['topics_discussed'][-3:]
            context = f"Context: {', '.join(recent_topics)}. Query: {base_query}"
            return context
        
        return base_query
    
    def _generate_contextual_response(self, state: ConversationState) -> str:
        """Generate response based on search results and context"""
        
        if state.get('search_results') and state['search_results']:
            # Use search results to generate response
            context_text = "\n".join([result['content'][:500] for result in state['search_results'][:3]])
            
            prompt = f"""Based on the following information, provide a helpful response to the user's query: "{state['original_query']}"

Context:
{context_text}

Please provide a clear, informative response based on the context provided."""
            
            try:
                if self.llm_client:
                    response = self.llm_client.generate_response(prompt)
                    return response
            except Exception as e:
                self.logger.error(f"LLM generation failed: {e}")
        
        # Fallback response when no search results or LLM fails
        return self._generate_general_response(state)
    
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
        """Extract related topics from search results"""
        
        if not state.get('search_results'):
            return []
        
        # Simple topic extraction from search results
        topics = set()
        for result in state['search_results'][:3]:
            # Extract potential topics from content
            content_words = re.findall(r'\b[A-Z][a-z]+\b', result['content'])
            topics.update(content_words[:2])  # Add up to 2 topics per result
        
        return list(topics)[:5]  # Return max 5 related topics 