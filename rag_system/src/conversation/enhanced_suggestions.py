import asyncio
import concurrent.futures
import logging
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import uuid

class EnhancedConversationSuggestions:
    """Enhanced conversation suggestions with better UI integration"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.suggestion_cache = {}  # Cache for quick responses
        
    def generate_enhanced_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response with enhanced suggestions and UI-friendly format"""
        try:
            # Prepare parallel tasks
            tasks = []
            
            # Task 1: Generate follow-up questions
            if state.get('search_results'):
                followup_future = self.executor.submit(
                    self._generate_contextual_followups, state
                )
                tasks.append(('followup_questions', followup_future))
                
                # Task 2: Extract related topics/entities
                topics_future = self.executor.submit(
                    self._extract_explorable_topics, state
                )
                tasks.append(('related_topics', topics_future))
                
                # Task 3: Generate conversation insights
                insights_future = self.executor.submit(
                    self._generate_conversation_insights, state
                )
                tasks.append(('conversation_insights', insights_future))
            
            # Collect results
            results = {}
            for task_name, future in tasks:
                try:
                    results[task_name] = future.result(timeout=8)
                except Exception as e:
                    self.logger.error(f"Task {task_name} failed: {e}")
                    results[task_name] = None
            
            # Format enhanced response
            enhanced_response = self._format_enhanced_response(state, results)
            
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced response: {e}")
            return self._generate_fallback_response(state)
    
    def _generate_contextual_followups(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent follow-up questions with UI integration"""
        if not self.llm_client or not state.get('search_results'):
            return self._generate_fallback_questions(state)
        
        try:
            context_summary = self._summarize_search_results(state['search_results'][:3])
            conversation_history = self._get_conversation_context(state)
            
            prompt = f"""Based on the conversation and search results, generate intelligent follow-up questions.

Current Question: "{state.get('original_query', '')}"

Conversation Context:
{conversation_history}

Information Found:
{context_summary}

Generate 5-6 diverse follow-up questions that:
1. Explore specific details from the results
2. Ask about relationships and connections
3. Seek clarification or deeper understanding
4. Suggest practical actions or next steps
5. Explore related topics not fully covered
6. Consider different perspectives or use cases

For each question, provide:
- The question text (natural and engaging)
- Intent category (details, related, action, clarification, comparison, exploration)
- Context hint (what this explores)
- Estimated response time (quick/medium/detailed)
- Relevance score (0.0-1.0)

Format as JSON array:
[
  {{
    "question": "What are the specific technical requirements for this setup?",
    "intent": "details",
    "context_hint": "Technical specifications and requirements",
    "response_time": "medium",
    "relevance": 0.9,
    "icon": "🔧"
  }}
]"""

            response = self.llm_client.generate(prompt, max_tokens=600, temperature=0.7)
            
            # Parse and validate JSON response
            questions = self._parse_questions_json(response)
            
            # Enhance questions with UI elements
            enhanced_questions = []
            for i, q in enumerate(questions[:6]):
                enhanced_q = {
                    'id': f"q_{uuid.uuid4().hex[:8]}",
                    'question': q.get('question', ''),
                    'intent': q.get('intent', 'details'),
                    'context_hint': q.get('context_hint', ''),
                    'response_time': q.get('response_time', 'medium'),
                    'relevance': float(q.get('relevance', 0.5)),
                    'icon': q.get('icon', self._get_intent_icon(q.get('intent', 'details'))),
                    'priority': self._calculate_question_priority(q, state),
                    'has_quick_answer': self._can_answer_quickly(q, state),
                    'category': self._categorize_question(q),
                    'estimated_tokens': self._estimate_response_length(q, state)
                }
                enhanced_questions.append(enhanced_q)
            
            # Sort by priority and relevance
            enhanced_questions.sort(key=lambda x: (x['priority'], x['relevance']), reverse=True)
            
            return enhanced_questions
            
        except Exception as e:
            self.logger.error(f"Failed to generate contextual follow-ups: {e}")
            return self._generate_fallback_questions(state)
    
    def _extract_explorable_topics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract topics and entities for exploration with UI enhancements"""
        if not self.llm_client or not state.get('search_results'):
            return {'topics': [], 'entities': [], 'technical_terms': [], 'related_areas': []}
        
        try:
            context = "\n".join([r.get('content', '')[:300] for r in state['search_results'][:3]])
            
            prompt = f"""Extract explorable topics and entities from this information for an interactive UI.

Context:
{context}

Original Query: "{state.get('original_query', '')}"

Identify and categorize:
1. Main topics (concepts, processes, systems) - with exploration potential
2. Named entities (people, places, products, organizations) - with context
3. Technical terms that might need explanation - with difficulty level
4. Related areas not fully covered - with connection strength

Format as JSON:
{{
  "topics": [
    {{"name": "Network Security", "type": "concept", "explore_potential": "high", "icon": "🔒"}}
  ],
  "entities": [
    {{"name": "Maria Garcia", "type": "person", "context": "Network Administrator", "explore_potential": "medium", "icon": "👤"}}
  ],
  "technical_terms": [
    {{"term": "VLAN", "difficulty": "medium", "definition_available": true, "icon": "🔧"}}
  ],
  "related_areas": [
    {{"area": "Network Monitoring", "connection": "strong", "explore_potential": "high", "icon": "📊"}}
  ]
}}"""

            response = self.llm_client.generate(prompt, max_tokens=400, temperature=0.3)
            
            # Parse JSON response
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    extracted = json.loads(response[json_start:json_end])
                    
                    # Enhance with UI elements
                    return {
                        'topics': self._enhance_topics(extracted.get('topics', [])[:5]),
                        'entities': self._enhance_entities(extracted.get('entities', [])[:5]),
                        'technical_terms': self._enhance_technical_terms(extracted.get('technical_terms', [])[:4]),
                        'related_areas': self._enhance_related_areas(extracted.get('related_areas', [])[:4])
                    }
            except Exception as e:
                self.logger.warning(f"Failed to parse topics JSON: {e}")
            
            return self._fallback_topic_extraction(state)
            
        except Exception as e:
            self.logger.error(f"Failed to extract topics: {e}")
            return {'topics': [], 'entities': [], 'technical_terms': [], 'related_areas': []}
    
    def _generate_conversation_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate conversation insights and guidance"""
        try:
            insights = {
                'topic_continuity': self._calculate_topic_continuity(state),
                'information_coverage': self._estimate_information_coverage(state),
                'conversation_depth': self._assess_conversation_depth(state),
                'suggested_exploration_path': self._suggest_exploration_path(state),
                'conversation_health': self._assess_conversation_health(state),
                'next_best_actions': self._suggest_next_actions(state)
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate conversation insights: {e}")
            return {}
    
    def _format_enhanced_response(self, state: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Format the enhanced response with all UI elements"""
        response = {
            'response_id': f"resp_{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now().isoformat(),
            'session_id': state.get('session_id', ''),
            'turn_count': state.get('turn_count', 0)
        }
        
        # Main response content
        response['main_response'] = state.get('response', '')
        
        # Enhanced suggestions
        if results.get('followup_questions'):
            response['suggested_questions'] = results['followup_questions']
            response['quick_suggestions'] = [q for q in results['followup_questions'] if q.get('has_quick_answer')]
            response['detailed_suggestions'] = [q for q in results['followup_questions'] if not q.get('has_quick_answer')]
        
        # Exploration topics
        if results.get('related_topics'):
            response['exploration'] = results['related_topics']
            response['exploration_summary'] = self._create_exploration_summary(results['related_topics'])
        
        # Conversation insights
        if results.get('conversation_insights'):
            response['insights'] = results['conversation_insights']
            response['conversation_guidance'] = self._create_conversation_guidance(results['conversation_insights'])
        
        # UI-specific enhancements
        response['ui_elements'] = self._create_ui_elements(state, results)
        response['interaction_hints'] = self._create_interaction_hints(state, results)
        
        return response
    
    def _create_ui_elements(self, state: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Create UI-specific elements for better interaction"""
        ui_elements = {
            'suggestion_buttons': [],
            'topic_chips': [],
            'entity_cards': [],
            'action_buttons': [],
            'exploration_panels': []
        }
        
        # Create suggestion buttons
        if results.get('followup_questions'):
            for q in results['followup_questions'][:4]:  # Top 4 for UI
                ui_elements['suggestion_buttons'].append({
                    'id': q['id'],
                    'text': q['question'],
                    'icon': q.get('icon', '💬'),
                    'variant': self._get_button_variant(q['intent']),
                    'tooltip': q.get('context_hint', ''),
                    'estimated_time': q.get('response_time', 'medium')
                })
        
        # Create topic exploration chips
        if results.get('related_topics', {}).get('topics'):
            for topic in results['related_topics']['topics'][:6]:
                ui_elements['topic_chips'].append({
                    'name': topic.get('name', ''),
                    'icon': topic.get('icon', '🔍'),
                    'explore_potential': topic.get('explore_potential', 'medium'),
                    'click_action': f"explore_topic:{topic.get('name', '')}"
                })
        
        # Create entity cards
        if results.get('related_topics', {}).get('entities'):
            for entity in results['related_topics']['entities'][:4]:
                ui_elements['entity_cards'].append({
                    'name': entity.get('name', ''),
                    'type': entity.get('type', 'unknown'),
                    'context': entity.get('context', ''),
                    'icon': entity.get('icon', '📋'),
                    'explore_action': f"explore_entity:{entity.get('name', '')}"
                })
        
        return ui_elements
    
    def _create_interaction_hints(self, state: Dict[str, Any], results: Dict[str, Any]) -> List[str]:
        """Create helpful interaction hints for the user"""
        hints = []
        
        # Based on conversation state
        if state.get('turn_count', 0) == 1:
            hints.append("💡 Click on suggestion buttons for quick follow-up questions")
            hints.append("🔍 Explore topic chips to dive deeper into related areas")
        
        # Based on search results
        if state.get('search_results'):
            source_count = len(state['search_results'])
            if source_count > 3:
                hints.append(f"📚 Found {source_count} relevant sources - ask for more specific details")
        
        # Based on suggestions available
        if results.get('followup_questions'):
            quick_count = len([q for q in results['followup_questions'] if q.get('has_quick_answer')])
            if quick_count > 0:
                hints.append(f"⚡ {quick_count} questions have quick answers available")
        
        return hints[:3]  # Limit to 3 hints
    
    # Helper methods
    def _get_intent_icon(self, intent: str) -> str:
        """Get icon for question intent"""
        icons = {
            'details': '🔍',
            'related': '🔗',
            'action': '⚡',
            'clarification': '❓',
            'comparison': '⚖️',
            'exploration': '🗺️'
        }
        return icons.get(intent, '💬')
    
    def _get_button_variant(self, intent: str) -> str:
        """Get button variant for UI styling"""
        variants = {
            'details': 'primary',
            'related': 'secondary',
            'action': 'success',
            'clarification': 'info',
            'comparison': 'warning',
            'exploration': 'outline'
        }
        return variants.get(intent, 'secondary')
    
    def _calculate_question_priority(self, question: Dict[str, Any], state: Dict[str, Any]) -> float:
        """Calculate priority score for questions"""
        priority = 0.5
        
        # Intent-based priority
        intent_weights = {
            'clarification': 0.9,
            'details': 0.8,
            'action': 0.7,
            'related': 0.6,
            'comparison': 0.65,
            'exploration': 0.55
        }
        priority = intent_weights.get(question.get('intent', ''), 0.5)
        
        # Relevance boost
        relevance = float(question.get('relevance', 0.5))
        priority += relevance * 0.2
        
        # Query keyword overlap
        query_keywords = set(self._extract_keywords(state.get('original_query', '')))
        question_keywords = set(self._extract_keywords(question.get('question', '')))
        
        if query_keywords and question_keywords:
            overlap = len(query_keywords & question_keywords) / len(query_keywords)
            priority += overlap * 0.15
        
        return min(1.0, priority)
    
    def _can_answer_quickly(self, question: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Determine if question can be answered quickly from current context"""
        # Check if question keywords are in current search results
        question_keywords = set(self._extract_keywords(question.get('question', '').lower()))
        
        result_text = ""
        for result in state.get('search_results', [])[:3]:
            result_text += result.get('content', '').lower() + " "
        
        result_keywords = set(self._extract_keywords(result_text))
        
        # If significant overlap, likely can answer quickly
        if question_keywords and result_keywords:
            overlap_ratio = len(question_keywords & result_keywords) / len(question_keywords)
            return overlap_ratio > 0.6
        
        return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter out common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        return [word for word in words if word not in stop_words]
    
    def _parse_questions_json(self, response: str) -> List[Dict[str, Any]]:
        """Parse JSON questions from LLM response"""
        try:
            # Try to find JSON array
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                questions = json.loads(json_str)
                return questions if isinstance(questions, list) else []
        except Exception as e:
            self.logger.warning(f"Failed to parse questions JSON: {e}")
        
        # Fallback: extract questions from text
        return self._extract_questions_from_text(response)
    
    def _extract_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions from plain text as fallback"""
        questions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if '?' in line and len(line) > 10:
                # Extract question
                question_text = line.split('?')[0] + '?'
                question_text = re.sub(r'^[-•*\d.]+\s*', '', question_text)
                
                if question_text:
                    questions.append({
                        'question': question_text,
                        'intent': 'details',
                        'context_hint': 'General follow-up',
                        'relevance': 0.5
                    })
        
        return questions[:5]
    
    def _generate_fallback_questions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fallback questions when LLM fails"""
        original_query = state.get('original_query', '').lower()
        questions = []
        
        # Generate based on query type
        if 'who is' in original_query or 'who are' in original_query:
            questions = [
                {"question": "What is their role and main responsibilities?", "intent": "details", "icon": "👤"},
                {"question": "How can I contact them?", "intent": "action", "icon": "📞"},
                {"question": "What team or department are they part of?", "intent": "related", "icon": "🏢"},
                {"question": "What are their key qualifications?", "intent": "details", "icon": "🎓"}
            ]
        elif 'what is' in original_query or 'what are' in original_query:
            questions = [
                {"question": "Can you provide more specific details?", "intent": "details", "icon": "🔍"},
                {"question": "How does this work in practice?", "intent": "clarification", "icon": "⚙️"},
                {"question": "What are some real-world examples?", "intent": "exploration", "icon": "🌍"},
                {"question": "What are the key benefits?", "intent": "details", "icon": "✅"}
            ]
        elif 'how' in original_query:
            questions = [
                {"question": "What are the specific step-by-step instructions?", "intent": "details", "icon": "📋"},
                {"question": "What tools or resources are needed?", "intent": "action", "icon": "🛠️"},
                {"question": "Are there any prerequisites or requirements?", "intent": "clarification", "icon": "⚠️"},
                {"question": "How long does this typically take?", "intent": "details", "icon": "⏱️"}
            ]
        else:
            questions = [
                {"question": "Can you tell me more about this topic?", "intent": "details", "icon": "📖"},
                {"question": "What are the key points I should remember?", "intent": "clarification", "icon": "🎯"},
                {"question": "Are there related topics I should explore?", "intent": "related", "icon": "🔗"},
                {"question": "What would be the next logical step?", "intent": "action", "icon": "➡️"}
            ]
        
        # Enhance fallback questions
        enhanced_questions = []
        for i, q in enumerate(questions):
            enhanced_q = {
                'id': f"fallback_{i}",
                'question': q['question'],
                'intent': q['intent'],
                'icon': q.get('icon', '💬'),
                'context_hint': 'General follow-up question',
                'priority': 0.4 - (i * 0.05),
                'has_quick_answer': False,
                'relevance': 0.5,
                'response_time': 'medium'
            }
            enhanced_questions.append(enhanced_q)
        
        return enhanced_questions
    
    def _generate_fallback_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback response when enhancement fails"""
        return {
            'response_id': f"fallback_{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now().isoformat(),
            'main_response': state.get('response', ''),
            'suggested_questions': self._generate_fallback_questions(state),
            'exploration': {'topics': [], 'entities': [], 'technical_terms': [], 'related_areas': []},
            'ui_elements': {'suggestion_buttons': [], 'topic_chips': [], 'entity_cards': []},
            'interaction_hints': ["💡 Try asking more specific questions for better suggestions"]
        }
    
    # Additional helper methods for UI enhancement
    def _enhance_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance topics with UI elements"""
        enhanced = []
        for topic in topics:
            if isinstance(topic, dict):
                enhanced.append({
                    'name': topic.get('name', ''),
                    'type': topic.get('type', 'concept'),
                    'explore_potential': topic.get('explore_potential', 'medium'),
                    'icon': topic.get('icon', '🔍'),
                    'click_action': f"explore_topic:{topic.get('name', '')}"
                })
        return enhanced
    
    def _enhance_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance entities with UI elements"""
        enhanced = []
        for entity in entities:
            if isinstance(entity, dict):
                enhanced.append({
                    'name': entity.get('name', ''),
                    'type': entity.get('type', 'unknown'),
                    'context': entity.get('context', ''),
                    'icon': entity.get('icon', '📋'),
                    'explore_action': f"explore_entity:{entity.get('name', '')}"
                })
        return enhanced
    
    def _enhance_technical_terms(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance technical terms with UI elements"""
        enhanced = []
        for term in terms:
            if isinstance(term, dict):
                enhanced.append({
                    'term': term.get('term', ''),
                    'difficulty': term.get('difficulty', 'medium'),
                    'definition_available': term.get('definition_available', False),
                    'icon': term.get('icon', '🔧'),
                    'explain_action': f"explain_term:{term.get('term', '')}"
                })
        return enhanced
    
    def _enhance_related_areas(self, areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance related areas with UI elements"""
        enhanced = []
        for area in areas:
            if isinstance(area, dict):
                enhanced.append({
                    'area': area.get('area', ''),
                    'connection': area.get('connection', 'medium'),
                    'explore_potential': area.get('explore_potential', 'medium'),
                    'icon': area.get('icon', '📊'),
                    'explore_action': f"explore_area:{area.get('area', '')}"
                })
        return enhanced
    
    # Placeholder methods for missing functionality
    def _summarize_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Summarize search results for context"""
        summary_parts = []
        for i, result in enumerate(results):
            content = result.get('content', '')[:200]
            source = result.get('source', 'Unknown')
            summary_parts.append(f"Source {i+1} ({source}): {content}...")
        return "\n".join(summary_parts)
    
    def _get_conversation_context(self, state: Dict[str, Any]) -> str:
        """Get conversation context"""
        messages = state.get('messages', [])
        context_parts = []
        for msg in messages[-3:]:  # Last 3 messages
            role = msg.get('type', 'unknown')
            content = msg.get('content', '')[:100]
            context_parts.append(f"{role}: {content}...")
        return "\n".join(context_parts)
    
    def _categorize_question(self, question: Dict[str, Any]) -> str:
        """Categorize question for UI grouping"""
        intent = question.get('intent', 'general')
        categories = {
            'details': 'Information',
            'related': 'Exploration',
            'action': 'Actions',
            'clarification': 'Clarification',
            'comparison': 'Analysis',
            'exploration': 'Discovery'
        }
        return categories.get(intent, 'General')
    
    def _estimate_response_length(self, question: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Estimate response length"""
        intent = question.get('intent', 'details')
        if intent in ['action', 'clarification']:
            return 'short'
        elif intent in ['details', 'comparison']:
            return 'medium'
        else:
            return 'long'
    
    def _calculate_topic_continuity(self, state: Dict[str, Any]) -> float:
        """Calculate topic continuity score"""
        return 0.8  # Placeholder
    
    def _estimate_information_coverage(self, state: Dict[str, Any]) -> str:
        """Estimate information coverage"""
        if not state.get('search_results'):
            return 'minimal'
        source_count = len(state['search_results'])
        if source_count >= 3:
            return 'comprehensive'
        elif source_count >= 2:
            return 'good'
        else:
            return 'basic'
    
    def _assess_conversation_depth(self, state: Dict[str, Any]) -> str:
        """Assess conversation depth"""
        turn_count = state.get('turn_count', 0)
        if turn_count >= 5:
            return 'deep'
        elif turn_count >= 3:
            return 'moderate'
        else:
            return 'surface'
    
    def _suggest_exploration_path(self, state: Dict[str, Any]) -> List[str]:
        """Suggest exploration path"""
        return [
            "Start with clarifying questions",
            "Explore specific details",
            "Consider related topics"
        ]
    
    def _assess_conversation_health(self, state: Dict[str, Any]) -> str:
        """Assess conversation health"""
        if state.get('search_results'):
            return 'healthy'
        else:
            return 'needs_improvement'
    
    def _suggest_next_actions(self, state: Dict[str, Any]) -> List[str]:
        """Suggest next actions"""
        return [
            "Ask follow-up questions",
            "Explore related topics",
            "Request specific examples"
        ]
    
    def _create_exploration_summary(self, topics: Dict[str, Any]) -> str:
        """Create exploration summary"""
        summary_parts = []
        if topics.get('topics'):
            summary_parts.append(f"{len(topics['topics'])} topics to explore")
        if topics.get('entities'):
            summary_parts.append(f"{len(topics['entities'])} entities mentioned")
        return ", ".join(summary_parts)
    
    def _create_conversation_guidance(self, insights: Dict[str, Any]) -> str:
        """Create conversation guidance"""
        coverage = insights.get('information_coverage', 'basic')
        depth = insights.get('conversation_depth', 'surface')
        
        if coverage == 'comprehensive' and depth == 'deep':
            return "Great conversation! You're exploring the topic thoroughly."
        elif coverage == 'minimal':
            return "Try asking more specific questions to get better information."
        else:
            return "Good progress! Consider exploring related topics."
    
    def _fallback_topic_extraction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback topic extraction"""
        return {
            'topics': [{'name': 'General Topics', 'icon': '🔍', 'explore_potential': 'medium'}],
            'entities': [],
            'technical_terms': [],
            'related_areas': []
        } 