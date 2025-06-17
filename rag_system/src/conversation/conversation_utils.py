"""
Conversation Utilities
Utility functions for conversation processing and analysis
"""
import re
from typing import Dict, List, Any
from collections import Counter
from datetime import datetime, timedelta

from .conversation_state import MessageType

class ConversationUtils:
    """Utility functions for conversation processing"""
    
    @staticmethod
    def extract_entities(text: str) -> List[str]:
        """Extract named entities from text"""
        # Simple entity extraction - can be enhanced with spaCy or similar
        entities = []
        
        # Capitalize words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.extend(capitalized)
        
        # Acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        entities.extend(acronyms)
        
        # Technical terms with special characters
        technical = re.findall(r'\b\w+[-_.]\w+\b', text)
        entities.extend(technical)
        
        return list(set(entities))
    
    @staticmethod
    def calculate_conversation_quality(state) -> float:
        """Calculate conversation quality score"""
        
        if not state.messages:
            return 0.0
        
        factors = []
        
        # Response relevance (based on search results)
        if state.search_results:
            avg_score = sum(r.score for r in state.search_results) / len(state.search_results)
            factors.append(min(avg_score, 1.0))
        
        # Turn engagement (penalize very short or very long conversations)
        turn_factor = min(state.turn_count / 10, 1.0) if state.turn_count < 20 else max(0.5, 1 - (state.turn_count - 20) / 50)
        factors.append(turn_factor)
        
        # Error rate
        error_factor = max(0.0, 1.0 - len(state.error_messages) / max(state.turn_count, 1))
        factors.append(error_factor)
        
        # Response confidence
        factors.append(state.response_confidence)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    @staticmethod
    def suggest_conversation_improvements(state) -> List[str]:
        """Suggest improvements for conversation quality"""
        suggestions = []
        
        if state.response_confidence < 0.5:
            suggestions.append("Consider providing more specific queries")
        
        if len(state.error_messages) > 2:
            suggestions.append("Check system components for stability")
        
        if not state.search_results and state.turn_count > 3:
            suggestions.append("Knowledge base may need more relevant content")
        
        if state.turn_count > 30:
            suggestions.append("Consider starting a new conversation session")
        
        return suggestions
    
    @staticmethod
    def format_conversation_export(state) -> Dict[str, Any]:
        """Format conversation for export/analysis"""
        
        return {
            'conversation_id': state.conversation_id,
            'session_id': state.session_id,
            'created_at': state.messages[0].timestamp if state.messages else None,
            'ended_at': state.last_activity,
            'total_turns': state.turn_count,
            'final_phase': state.current_phase.value,
            'quality_score': ConversationUtils.calculate_conversation_quality(state),
            'topics_discussed': state.topics_discussed,
            'messages': [
                {
                    'type': msg.type.value,
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'metadata': msg.metadata
                }
                for msg in state.messages
            ],
            'search_performed': len(state.search_results) > 0,
            'total_searches': len([msg for msg in state.messages if 'search' in str(msg.metadata)]),
            'error_count': len(state.error_messages),
            'summary': state.conversation_summary or ConversationUtils._generate_summary(state)
        }
    
    @staticmethod 
    def _generate_summary(state) -> str:
        """Generate a conversation summary"""
        if not state.messages:
            return "Empty conversation"
        
        user_messages = [msg.content for msg in state.messages if msg.type.value == 'user']
        topics = state.topics_discussed[-3:] if state.topics_discussed else []
        
        summary_parts = []
        
        if topics:
            summary_parts.append(f"Discussed: {', '.join(topics)}")
        
        if user_messages:
            summary_parts.append(f"{len(user_messages)} user queries")
        
        summary_parts.append(f"{state.turn_count} total exchanges")
        
        return "; ".join(summary_parts)

class ConversationAnalytics:
    """Analytics for conversation performance and insights"""
    
    def __init__(self):
        self.conversation_logs = []
        self.daily_stats = {}
    
    def log_conversation_end(self, state):
        """Log completed conversation for analytics"""
        conversation_data = {
            'conversation_id': state.conversation_id,
            'session_id': state.session_id,
            'start_time': state.messages[0].timestamp if state.messages else None,
            'end_time': state.last_activity,
            'turn_count': state.turn_count,
            'final_phase': state.current_phase.value,
            'topics_discussed': state.topics_discussed,
            'error_count': len(state.error_messages),
            'quality_score': ConversationUtils.calculate_conversation_quality(state),
            'user_satisfaction': self._estimate_satisfaction(state)
        }
        
        self.conversation_logs.append(conversation_data)
        self._update_daily_stats(conversation_data)
    
    def _estimate_satisfaction(self, state) -> float:
        """Estimate user satisfaction based on conversation patterns"""
        # Simple heuristic based on:
        # - Number of follow-up questions
        # - Lack of error messages
        # - Natural conversation end vs abrupt end
        
        factors = []
        
        # Turn engagement factor
        if 3 <= state.turn_count <= 15:
            factors.append(1.0)  # Good engagement
        elif state.turn_count < 3:
            factors.append(0.6)  # Too short
        else:
            factors.append(0.7)  # Very long conversation
        
        # Error factor
        error_factor = max(0.2, 1.0 - (len(state.error_messages) / max(state.turn_count, 1)) * 2)
        factors.append(error_factor)
        
        # Ending factor
        if state.current_phase.value == 'ending':
            factors.append(1.0)  # Natural ending
        else:
            factors.append(0.8)  # Abrupt ending
        
        # Response confidence factor
        factors.append(state.response_confidence)
        
        return sum(factors) / len(factors)
    
    def _update_daily_stats(self, conversation_data):
        """Update daily statistics"""
        if conversation_data['end_time']:
            date_key = datetime.fromisoformat(conversation_data['end_time']).date().isoformat()
            
            if date_key not in self.daily_stats:
                self.daily_stats[date_key] = {
                    'conversations': 0,
                    'messages': 0,
                    'avg_turns': 0,
                    'error_rate': 0,
                    'topics': Counter()
                }
            
            stats = self.daily_stats[date_key]
            stats['conversations'] += 1
            stats['messages'] += conversation_data['turn_count']
            
            # Update average turns
            total_conversations = stats['conversations']
            stats['avg_turns'] = (stats['avg_turns'] * (total_conversations - 1) + conversation_data['turn_count']) / total_conversations
            
            # Update error rate
            has_error = conversation_data['error_count'] > 0
            stats['error_rate'] = (stats['error_rate'] * (total_conversations - 1) + (1 if has_error else 0)) / total_conversations
            
            # Update topics
            for topic in conversation_data['topics_discussed']:
                stats['topics'][topic] += 1
    
    def get_conversation_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get conversation insights for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_conversations = [
            conv for conv in self.conversation_logs
            if conv['end_time'] and datetime.fromisoformat(conv['end_time']) > cutoff_date
        ]
        
        if not recent_conversations:
            return {'message': 'No recent conversations found'}
        
        # Calculate metrics
        total_conversations = len(recent_conversations)
        total_turns = sum(conv['turn_count'] for conv in recent_conversations)
        avg_turns = total_turns / total_conversations
        
        # Quality distribution
        quality_scores = [conv['quality_score'] for conv in recent_conversations]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Satisfaction distribution
        satisfaction_scores = [conv['user_satisfaction'] for conv in recent_conversations]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
        
        # Topic popularity
        all_topics = []
        for conv in recent_conversations:
            all_topics.extend(conv['topics_discussed'])
        
        topic_counts = Counter(all_topics)
        
        # Phase distribution
        phase_counts = Counter(conv['final_phase'] for conv in recent_conversations)
        
        return {
            'period_days': days,
            'total_conversations': total_conversations,
            'average_turns_per_conversation': round(avg_turns, 2),
            'average_quality_score': round(avg_quality, 3),
            'average_satisfaction': round(avg_satisfaction, 3),
            'popular_topics': dict(topic_counts.most_common(10)),
            'conversation_phases': dict(phase_counts),
            'daily_conversation_count': len(set(
                datetime.fromisoformat(conv['end_time']).date() 
                for conv in recent_conversations if conv['end_time']
            )),
            'insights': self._generate_insights(recent_conversations)
        }
    
    def _generate_insights(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights from conversation data"""
        insights = []
        
        if not conversations:
            return insights
        
        # Average satisfaction analysis
        avg_satisfaction = sum(conv['user_satisfaction'] for conv in conversations) / len(conversations)
        if avg_satisfaction < 0.7:
            insights.append("User satisfaction is below optimal. Consider improving response quality and relevance.")
        
        # Turn count analysis
        avg_turns = sum(conv['turn_count'] for conv in conversations) / len(conversations)
        if avg_turns < 3:
            insights.append("Conversations are quite short. Users might need more engaging initial responses.")
        elif avg_turns > 15:
            insights.append("Conversations are lengthy. Consider providing more direct answers earlier.")
        
        # Error analysis
        error_conversations = [conv for conv in conversations if conv['error_count'] > 0]
        if len(error_conversations) / len(conversations) > 0.2:
            insights.append("High error rate detected. Check system stability and error handling.")
        
        # Topic diversity
        all_topics = []
        for conv in conversations:
            all_topics.extend(conv['topics_discussed'])
        
        unique_topics = len(set(all_topics))
        if unique_topics < 5:
            insights.append("Limited topic diversity. Consider expanding the knowledge base.")
        
        # Quality score analysis
        avg_quality = sum(conv['quality_score'] for conv in conversations) / len(conversations)
        if avg_quality < 0.6:
            insights.append("Conversation quality is below average. Review retrieval accuracy and response generation.")
        
        return insights 