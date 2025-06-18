# -*- coding: utf-8 -*-
"""
Feedback Storage System
Stores and manages user feedback on query responses for continuous improvement
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import sqlite3
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class FeedbackStore:
    """Storage system for user feedback on query responses"""
    
    def __init__(self, storage_path: str = "feedback_store.db"):
        """Initialize feedback store with SQLite backend"""
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()
        
        logger.info(f"Feedback store initialized at: {self.storage_path}")
    
    def _init_database(self):
        """Initialize SQLite database with feedback tables"""
        with self._get_connection() as conn:
            # Main feedback table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    response_id TEXT,
                    query TEXT NOT NULL,
                    response_text TEXT,
                    helpful BOOLEAN NOT NULL,
                    feedback_text TEXT,
                    confidence_score REAL,
                    confidence_level TEXT,
                    sources_count INTEGER,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    metadata TEXT
                )
            """)
            
            # Feedback analytics table for aggregated insights
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_analytics (
                    id TEXT PRIMARY KEY,
                    query_pattern TEXT,
                    helpful_count INTEGER DEFAULT 0,
                    unhelpful_count INTEGER DEFAULT 0,
                    avg_confidence REAL,
                    common_issues TEXT,
                    last_updated TEXT,
                    metadata TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_helpful ON feedback(helpful)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_confidence ON feedback(confidence_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_query ON feedback(query)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.storage_path), timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def add_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """Add user feedback to the store"""
        with self._lock:
            try:
                # Generate unique feedback ID
                feedback_id = str(uuid.uuid4())
                
                # Extract and validate data
                query = feedback_data.get('query', '')
                response_id = feedback_data.get('response_id', '')
                response_text = feedback_data.get('response_text', '')
                helpful = feedback_data.get('helpful', False)
                feedback_text = feedback_data.get('feedback_text', '')
                confidence_score = feedback_data.get('confidence_score', 0.0)
                confidence_level = feedback_data.get('confidence_level', 'unknown')
                sources_count = feedback_data.get('sources_count', 0)
                user_id = feedback_data.get('user_id', 'anonymous')
                session_id = feedback_data.get('session_id', '')
                timestamp = feedback_data.get('timestamp', datetime.now().isoformat())
                
                # Store additional metadata as JSON
                metadata = {
                    'user_agent': feedback_data.get('user_agent', ''),
                    'ip_address': feedback_data.get('ip_address', ''),
                    'processing_time': feedback_data.get('processing_time', 0),
                    'sources': feedback_data.get('sources', [])
                }
                
                with self._get_connection() as conn:
                    conn.execute("""
                        INSERT INTO feedback (
                            id, response_id, query, response_text, helpful, feedback_text,
                            confidence_score, confidence_level, sources_count, timestamp,
                            user_id, session_id, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        feedback_id, response_id, query, response_text, helpful, feedback_text,
                        confidence_score, confidence_level, sources_count, timestamp,
                        user_id, session_id, json.dumps(metadata)
                    ))
                    conn.commit()
                
                # Update analytics asynchronously
                self._update_analytics(query, helpful, confidence_score, feedback_text)
                
                logger.info(f"Feedback stored: {feedback_id} - {'helpful' if helpful else 'unhelpful'}")
                return feedback_id
                
            except Exception as e:
                logger.error(f"Failed to store feedback: {e}")
                raise
    
    def _update_analytics(self, query: str, helpful: bool, confidence_score: float, feedback_text: str):
        """Update feedback analytics for query patterns"""
        try:
            # Extract query pattern (simplified - could use NLP for better patterns)
            query_pattern = self._extract_query_pattern(query)
            
            with self._get_connection() as conn:
                # Check if pattern exists
                result = conn.execute(
                    "SELECT * FROM feedback_analytics WHERE query_pattern = ?",
                    (query_pattern,)
                ).fetchone()
                
                if result:
                    # Update existing pattern
                    helpful_count = result['helpful_count'] + (1 if helpful else 0)
                    unhelpful_count = result['unhelpful_count'] + (0 if helpful else 1)
                    
                    # Update average confidence (simple moving average)
                    total_feedback = helpful_count + unhelpful_count
                    current_avg = result['avg_confidence'] or 0
                    new_avg = ((current_avg * (total_feedback - 1)) + confidence_score) / total_feedback
                    
                    # Update common issues
                    common_issues = self._update_common_issues(result['common_issues'], feedback_text, helpful)
                    
                    conn.execute("""
                        UPDATE feedback_analytics SET
                            helpful_count = ?, unhelpful_count = ?, avg_confidence = ?,
                            common_issues = ?, last_updated = ?
                        WHERE query_pattern = ?
                    """, (
                        helpful_count, unhelpful_count, new_avg,
                        json.dumps(common_issues), datetime.now().isoformat(),
                        query_pattern
                    ))
                else:
                    # Create new pattern
                    analytics_id = str(uuid.uuid4())
                    common_issues = [feedback_text] if feedback_text and not helpful else []
                    
                    conn.execute("""
                        INSERT INTO feedback_analytics (
                            id, query_pattern, helpful_count, unhelpful_count,
                            avg_confidence, common_issues, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analytics_id, query_pattern,
                        1 if helpful else 0, 0 if helpful else 1,
                        confidence_score, json.dumps(common_issues),
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update analytics: {e}")
    
    def _extract_query_pattern(self, query: str) -> str:
        """Extract query pattern for analytics (simplified approach)"""
        # Convert to lowercase and extract key patterns
        query_lower = query.lower().strip()
        
        # Common question patterns
        if query_lower.startswith(('who is', 'who are')):
            return 'who_question'
        elif query_lower.startswith(('what is', 'what are', 'what')):
            return 'what_question'
        elif query_lower.startswith(('how to', 'how do', 'how')):
            return 'how_question'
        elif query_lower.startswith(('when', 'where')):
            return 'when_where_question'
        elif query_lower.startswith(('why')):
            return 'why_question'
        elif 'list' in query_lower or 'show me' in query_lower:
            return 'list_request'
        elif 'explain' in query_lower or 'describe' in query_lower:
            return 'explanation_request'
        else:
            return 'general_query'
    
    def _update_common_issues(self, current_issues: str, new_feedback: str, helpful: bool) -> List[str]:
        """Update common issues list"""
        try:
            issues = json.loads(current_issues) if current_issues else []
        except:
            issues = []
        
        # Only add to issues if feedback is negative and has text
        if not helpful and new_feedback and new_feedback.strip():
            issues.append(new_feedback.strip())
            # Keep only last 10 issues to prevent bloat
            issues = issues[-10:]
        
        return issues
    
    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback statistics for the last N days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with self._get_connection() as conn:
                # Overall stats
                overall = conn.execute("""
                    SELECT 
                        COUNT(*) as total_feedback,
                        SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
                        SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) as unhelpful_count,
                        AVG(confidence_score) as avg_confidence,
                        MIN(timestamp) as earliest_feedback,
                        MAX(timestamp) as latest_feedback
                    FROM feedback 
                    WHERE timestamp >= ?
                """, (cutoff_date,)).fetchone()
                
                # Confidence level breakdown
                confidence_breakdown = conn.execute("""
                    SELECT 
                        confidence_level,
                        COUNT(*) as count,
                        AVG(CASE WHEN helpful = 1 THEN 1.0 ELSE 0.0 END) as helpfulness_rate
                    FROM feedback 
                    WHERE timestamp >= ?
                    GROUP BY confidence_level
                """, (cutoff_date,)).fetchall()
                
                # Query pattern analytics
                pattern_stats = conn.execute("""
                    SELECT * FROM feedback_analytics 
                    ORDER BY (helpful_count + unhelpful_count) DESC 
                    LIMIT 10
                """).fetchall()
                
                return {
                    'period_days': days,
                    'total_feedback': overall['total_feedback'],
                    'helpful_count': overall['helpful_count'],
                    'unhelpful_count': overall['unhelpful_count'],
                    'helpfulness_rate': overall['helpful_count'] / max(overall['total_feedback'], 1),
                    'avg_confidence': round(overall['avg_confidence'] or 0, 3),
                    'confidence_breakdown': [dict(row) for row in confidence_breakdown],
                    'top_query_patterns': [dict(row) for row in pattern_stats],
                    'earliest_feedback': overall['earliest_feedback'],
                    'latest_feedback': overall['latest_feedback']
                }
                
        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}")
            return {'error': str(e)}
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions for system improvement based on feedback"""
        suggestions = []
        
        try:
            with self._get_connection() as conn:
                # Find patterns with low helpfulness rates
                low_performance = conn.execute("""
                    SELECT query_pattern, helpful_count, unhelpful_count, avg_confidence, common_issues
                    FROM feedback_analytics
                    WHERE (helpful_count + unhelpful_count) >= 5
                    AND (helpful_count * 1.0 / (helpful_count + unhelpful_count)) < 0.6
                    ORDER BY (helpful_count + unhelpful_count) DESC
                """).fetchall()
                
                for pattern in low_performance:
                    total = pattern['helpful_count'] + pattern['unhelpful_count']
                    helpfulness_rate = pattern['helpful_count'] / total
                    
                    suggestion = {
                        'type': 'low_performance_pattern',
                        'query_pattern': pattern['query_pattern'],
                        'helpfulness_rate': round(helpfulness_rate, 3),
                        'total_feedback': total,
                        'avg_confidence': round(pattern['avg_confidence'] or 0, 3),
                        'common_issues': json.loads(pattern['common_issues'] or '[]'),
                        'recommendation': self._get_pattern_recommendation(pattern['query_pattern'], helpfulness_rate)
                    }
                    suggestions.append(suggestion)
                
                # Find confidence vs helpfulness mismatches
                mismatches = conn.execute("""
                    SELECT confidence_level, 
                           AVG(CASE WHEN helpful = 1 THEN 1.0 ELSE 0.0 END) as helpfulness_rate,
                           COUNT(*) as count
                    FROM feedback
                    GROUP BY confidence_level
                    HAVING count >= 10
                """).fetchall()
                
                for mismatch in mismatches:
                    if (mismatch['confidence_level'] == 'high' and mismatch['helpfulness_rate'] < 0.8) or \
                       (mismatch['confidence_level'] == 'low' and mismatch['helpfulness_rate'] > 0.6):
                        
                        suggestion = {
                            'type': 'confidence_calibration',
                            'confidence_level': mismatch['confidence_level'],
                            'helpfulness_rate': round(mismatch['helpfulness_rate'], 3),
                            'feedback_count': mismatch['count'],
                            'recommendation': f"Recalibrate confidence scoring for {mismatch['confidence_level']} confidence responses"
                        }
                        suggestions.append(suggestion)
                
        except Exception as e:
            logger.error(f"Failed to generate improvement suggestions: {e}")
            suggestions.append({
                'type': 'error',
                'message': f"Failed to analyze feedback: {str(e)}"
            })
        
        return suggestions
    
    def _get_pattern_recommendation(self, pattern: str, helpfulness_rate: float) -> str:
        """Get specific recommendation for query pattern"""
        recommendations = {
            'who_question': "Consider improving person/entity recognition and contact information retrieval",
            'what_question': "Enhance definition and explanation capabilities",
            'how_question': "Improve step-by-step instruction generation and process documentation",
            'list_request': "Better structured data extraction and formatting",
            'explanation_request': "Enhance detailed explanation generation with examples",
            'general_query': "Improve query understanding and context matching"
        }
        
        base_rec = recommendations.get(pattern, "Review and improve response quality for this query type")
        
        if helpfulness_rate < 0.3:
            return f"URGENT: {base_rec}. Very low user satisfaction."
        elif helpfulness_rate < 0.5:
            return f"HIGH PRIORITY: {base_rec}"
        else:
            return base_rec
    
    def get_recent_feedback(self, limit: int = 50, helpful_only: bool = False) -> List[Dict[str, Any]]:
        """Get recent feedback entries"""
        try:
            with self._get_connection() as conn:
                query = """
                    SELECT * FROM feedback 
                    {} 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """.format("WHERE helpful = 1" if helpful_only else "")
                
                results = conn.execute(query, (limit,)).fetchall()
                
                feedback_list = []
                for row in results:
                    feedback_dict = dict(row)
                    # Parse metadata JSON
                    try:
                        feedback_dict['metadata'] = json.loads(feedback_dict['metadata'] or '{}')
                    except:
                        feedback_dict['metadata'] = {}
                    
                    feedback_list.append(feedback_dict)
                
                return feedback_list
                
        except Exception as e:
            logger.error(f"Failed to get recent feedback: {e}")
            return []
    
    def export_feedback(self, output_path: str, format: str = 'json') -> bool:
        """Export feedback data for analysis"""
        try:
            feedback_data = self.get_recent_feedback(limit=10000)  # Get all recent feedback
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(feedback_data, f, indent=2, ensure_ascii=False)
            elif format.lower() == 'csv':
                import csv
                if feedback_data:
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=feedback_data[0].keys())
                        writer.writeheader()
                        writer.writerows(feedback_data)
            
            logger.info(f"Feedback exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export feedback: {e}")
            return False 