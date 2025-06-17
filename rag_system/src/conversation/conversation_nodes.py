"""
LangGraph Conversation Nodes
Individual processing nodes for the conversation flow
"""
import logging
from typing import Dict, Any, List
import re
from datetime import datetime

from .conversation_state import ConversationState, ConversationPhase, MessageType, Message, SearchResult

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
        
        if not state.messages or state.turn_count == 0:
            # First interaction - provide greeting
            greeting = "Hello! I'm your AI assistant. I can help you find information, answer questions, and have a conversation about various topics. What would you like to know?"
            
            state.add_message(MessageType.ASSISTANT, greeting)
            state.current_phase = ConversationPhase.UNDERSTANDING
        
        return state
    
    def understand_intent(self, state: ConversationState) -> ConversationState:
        """Analyze user intent and extract key information"""
        self.logger.info("Processing intent understanding node")
        
        if not state.messages:
            return state
        
        # Get latest user message
        user_messages = [msg for msg in state.messages if msg.type == MessageType.USER]
        if not user_messages:
            return state
        
        latest_message = user_messages[-1]
        user_input = latest_message.content
        
        # Skip processing if empty message (initial greeting scenario)
        if not user_input.strip():
            self.logger.info("Empty user input detected, skipping intent analysis")
            return state
        
        # Store original query
        state.original_query = user_input
        state.processed_query = user_input
        
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
            state.user_intent = "goodbye"
            state.current_phase = ConversationPhase.ENDING
        elif "greeting" in detected_intents and state.turn_count <= 2:
            state.user_intent = "greeting"
            state.current_phase = ConversationPhase.GREETING
        elif "help" in detected_intents:
            state.user_intent = "help"
            state.current_phase = ConversationPhase.RESPONDING
        else:
            # For any other query (including general statements), treat as information seeking
            # This ensures we always try to search the knowledge base first
            state.user_intent = "information_seeking"
            state.current_phase = ConversationPhase.SEARCHING
        
        # Extract keywords
        keywords = self._extract_keywords(user_input)
        state.query_keywords = keywords
        
        # Set confidence based on intent clarity
        state.confidence_score = 0.8 if detected_intents else 0.5
        
        # Update topics discussed
        if keywords:
            state.topics_discussed.extend(keywords[:3])  # Add top 3 keywords
            # Keep only recent topics
            state.topics_discussed = state.topics_discussed[-10:]
        
        self.logger.info(f"Intent: {state.user_intent}, Keywords: {keywords}")
        return state
    
    def search_knowledge(self, state: ConversationState) -> ConversationState:
        """Search for relevant information using the query engine"""
        self.logger.info("Processing knowledge search node")
        
        if not state.processed_query or not self.query_engine:
            state.has_errors = True
            state.error_messages.append("No query to search or query engine unavailable")
            # Set up for response generation even when query engine is unavailable
            state.current_phase = ConversationPhase.RESPONDING
            state.requires_clarification = False
            state.search_results = []
            state.context_chunks = []
            return state
        
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
                state.generated_response = search_result['response']
                state.relevant_sources = search_result.get('sources', [])
                state.context_chunks = []
                state.search_results = []
                
                # Store the original search result for later use
                state.original_search_result = search_result
                
                # Process sources if available
                sources = search_result.get('sources', [])
                if sources:
                    for source in sources:
                        search_res = SearchResult(
                            content=source.get('text', ''),
                            score=source.get('similarity_score', source.get('score', 0)),
                            source=source.get('metadata', {}).get('filename', 'unknown'),
                            metadata=source.get('metadata', {})
                        )
                        state.search_results.append(search_res)
                        
                        # Add to context chunks
                        if search_res.content:
                            state.context_chunks.append(search_res.content)
                
                state.current_phase = ConversationPhase.RESPONDING
                self.logger.info(f"Using query engine response with {len(state.search_results)} sources from original result")
            else:
                # No valid search result
                self.logger.info("No valid search result received, will generate fallback response")
                state.current_phase = ConversationPhase.RESPONDING
                state.requires_clarification = False
                state.search_results = []
                state.context_chunks = []
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            state.has_errors = True
            state.error_messages.append(f"Search error: {str(e)}")
            state.current_phase = ConversationPhase.RESPONDING
        
        return state
    
    def generate_response(self, state: ConversationState) -> ConversationState:
        """Generate response using LLM with retrieved context"""
        self.logger.info("Processing response generation node")
        
        if not self.llm_client:
            state.generated_response = "I apologize, but I'm currently unable to generate responses. Please try again later."
            return state
        
        try:
            if state.user_intent == "goodbye":
                response = "Goodbye! It was nice chatting with you. Feel free to come back anytime if you have more questions!"
                state.generated_response = response
                state.add_message(MessageType.ASSISTANT, response)
                return state
            
            elif state.user_intent == "greeting":
                response = "Hello! I'm here to help you find information and answer your questions. What would you like to know about?"
                state.generated_response = response
                state.add_message(MessageType.ASSISTANT, response)
                state.current_phase = ConversationPhase.UNDERSTANDING
                return state
            
            elif state.user_intent == "help":
                response = self._generate_help_response(state)
                state.generated_response = response
                state.add_message(MessageType.ASSISTANT, response)
                return state
            
            elif state.user_intent == "general":
                # For general queries, provide a helpful general response
                response = self._generate_general_response(state)
                state.generated_response = response
                state.add_message(MessageType.ASSISTANT, response)
                return state
            
            # Use pre-generated response from search or generate new one
            if hasattr(state, 'generated_response') and state.generated_response:
                # Use the response already generated by the query engine
                response = state.generated_response
                state.response_confidence = 0.9 if state.context_chunks else 0.7
            else:
                # Generate contextual response using retrieved information
                response = self._generate_contextual_response(state)
                state.generated_response = response
                state.response_confidence = 0.8 if state.context_chunks else 0.6
            
            # Add response to conversation
            state.add_message(MessageType.ASSISTANT, response)
            
            # Generate follow-up suggestions
            state.suggested_questions = self._generate_follow_up_questions(state)
            state.related_topics = self._extract_related_topics(state)
            
            # Keep in responding phase - don't force to follow-up
            state.current_phase = ConversationPhase.RESPONDING
            
            self.logger.info("Response generated successfully")
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            state.has_errors = True
            state.error_messages.append(f"Response generation error: {str(e)}")
            
            # Fallback response
            state.generated_response = "I apologize, but I encountered an issue while generating a response. Could you please rephrase your question?"
            state.add_message(MessageType.ASSISTANT, state.generated_response)
        
        return state
    
    def handle_clarification(self, state: ConversationState) -> ConversationState:
        """Handle requests for clarification"""
        self.logger.info("Processing clarification node")
        
        if state.clarification_questions:
            clarification = state.clarification_questions[0]
            state.generated_response = clarification
            state.add_message(MessageType.ASSISTANT, clarification)
            
            # Reset for next turn and stay in clarifying phase
            state.requires_clarification = False
            state.current_phase = ConversationPhase.CLARIFYING
        else:
            # Fallback response if no clarification questions
            fallback = "I'm not sure I understand. Could you please rephrase your question or provide more details?"
            state.generated_response = fallback
            state.add_message(MessageType.ASSISTANT, fallback)
            state.current_phase = ConversationPhase.CLARIFYING
        
        return state
    
    def check_conversation_end(self, state: ConversationState) -> ConversationState:
        """Check if conversation should end"""
        self.logger.info("Checking conversation end condition")
        
        # Handle case where state might be wrapped by LangGraph
        try:
            current_phase = getattr(state, 'current_phase', ConversationPhase.UNDERSTANDING)
            
            # Only end conversation if explicitly requested (goodbye intent) or natural ending conditions
            if (state.user_intent == "goodbye" or 
                (hasattr(state, 'should_end_conversation') and state.should_end_conversation())):
                if current_phase != ConversationPhase.ENDING:
                    farewell = "Thank you for the conversation! Is there anything else I can help you with before we end?"
                    if hasattr(state, 'add_message'):
                        state.add_message(MessageType.ASSISTANT, farewell)
                    state.current_phase = ConversationPhase.ENDING
            else:
                # Continue conversation - reset to understanding phase for next turn
                state.current_phase = ConversationPhase.UNDERSTANDING
        except Exception as e:
            self.logger.error(f"Error in check_conversation_end: {e}")
            # Fallback - continue conversation rather than end it
            state.current_phase = ConversationPhase.UNDERSTANDING
        
        return state
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]  # Return top 10 keywords
    
    def _enhance_query_with_context(self, state: ConversationState) -> str:
        """Enhance query with conversation context"""
        enhanced_query = state.processed_query
        
        # Add context from recent conversation
        if state.topics_discussed:
            recent_topics = state.topics_discussed[-3:]
            enhanced_query += f" Context: {', '.join(recent_topics)}"
        
        return enhanced_query
    
    def _generate_contextual_response(self, state: ConversationState) -> str:
        """Generate response using LLM with context"""
        if not state.context_chunks:
            # No context available, generate general response
            prompt = f"""
You are a helpful AI assistant. The user asked: "{state.original_query}"

Please provide a helpful response. If you don't have specific information, acknowledge this and offer to help in other ways.

Response:"""
        else:
            # Use retrieved context
            context = "\n\n".join(state.context_chunks[:3])  # Use top 3 chunks
            
            prompt = f"""
You are a helpful AI assistant. Based on the following context, answer the user's question.

Context:
{context}

User Question: {state.original_query}

Please provide a comprehensive answer based on the context. If the context doesn't fully answer the question, say so and provide what information you can.

Response:"""
        
        try:
            response = self.llm_client.generate(prompt, max_tokens=500, temperature=0.7)
            return response.strip()
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Could you please try rephrasing your question?"
    
    def _generate_help_response(self, state: ConversationState) -> str:
        """Generate help response"""
        return """
I'm here to help! Here's what I can do:

• Answer questions about various topics
• Search for information in the knowledge base
• Provide explanations and clarifications
• Help you find relevant documents and sources
• Have conversations about topics you're interested in

Just ask me anything, and I'll do my best to help! You can ask questions like:
- "What is [topic]?"
- "Tell me about [subject]"
- "How does [process] work?"
- "Find information about [query]"

What would you like to know?
"""
    
    def _generate_general_response(self, state: ConversationState) -> str:
        """Generate general response for unclear queries or when no search results found"""
        if not self.llm_client:
            return "I understand you have a question, but I'm having trouble accessing my response system right now. Could you please try rephrasing your question or ask something more specific?"
        
        try:
            # Check if this is because no search results were found
            if hasattr(state, 'search_results') and state.search_results == []:
                prompt = f"""
You are a helpful AI assistant. The user asked: "{state.original_query}"

I searched for information about this topic but couldn't find specific details in my knowledge base. Please provide a helpful response that:
1. Acknowledges that I don't have specific information on this topic
2. Provides any general knowledge you might have about the topic
3. Suggests ways I could help them find the information they need
4. Offers to help with related topics

Response:"""
            else:
                prompt = f"""
You are a helpful AI assistant. The user said: "{state.original_query}"

This seems like a general query or statement. Please provide a helpful, conversational response that:
1. Acknowledges what the user said
2. Offers to help with more specific information if needed
3. Suggests related topics they might be interested in
4. Keeps the conversation flowing naturally

Response:"""
            
            response = self.llm_client.generate(prompt, max_tokens=300, temperature=0.7)
            return response.strip()
        except Exception as e:
            self.logger.error(f"General response generation failed: {e}")
            return "I understand you're asking about something, but I'd like to help you better. Could you provide more specific details about what you're looking for?"
    
    def _generate_follow_up_questions(self, state: ConversationState) -> List[str]:
        """Generate relevant follow-up questions"""
        follow_ups = []
        
        if state.query_keywords:
            for keyword in state.query_keywords[:2]:
                follow_ups.append(f"Would you like to know more about {keyword}?")
                follow_ups.append(f"How does {keyword} relate to your work?")
        
        # Generic follow-ups
        follow_ups.extend([
            "Is there a specific aspect you'd like me to elaborate on?",
            "Do you have any related questions?",
            "Would you like me to find more information on this topic?"
        ])
        
        return follow_ups[:3]  # Return top 3
    
    def _extract_related_topics(self, state: ConversationState) -> List[str]:
        """Extract related topics from search results"""
        related = []
        
        for result in state.search_results[:3]:
            # Extract potential topics from metadata
            metadata = result.metadata
            if metadata.get('category'):
                related.append(metadata['category'])
            if metadata.get('tags'):
                related.extend(metadata['tags'][:2])
        
        return list(set(related))[:5]  # Return unique topics, max 5 