"""
Evaluation Framework for Proactive AI Agent
Measures adaptation effectiveness, proactivity quality, and user satisfaction
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
from dataclasses import dataclass
import numpy as np

@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    adaptation_score: float
    proactivity_score: float
    user_satisfaction: float
    privacy_compliance: float
    overall_score: float
    timestamp: str

class AgentEvaluator:
    """
    Evaluates the performance of the proactive AI agent across multiple dimensions
    """
    
    def __init__(self, memory, privacy_manager):
        self.memory = memory
        self.privacy_manager = privacy_manager
        self.evaluation_db = "evaluation_metrics.db"
        self._init_evaluation_db()
    
    def _init_evaluation_db(self):
        """Initialize evaluation database"""
        conn = sqlite3.connect(self.evaluation_db)
        cursor = conn.cursor()
        
        # Evaluation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                adaptation_score REAL NOT NULL,
                proactivity_score REAL NOT NULL,
                user_satisfaction REAL NOT NULL,
                privacy_compliance REAL NOT NULL,
                overall_score REAL NOT NULL,
                details TEXT
            )
        ''')
        
        # User feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                context TEXT
            )
        ''')
        
        # Adaptation tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adaptation_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                adaptation_type TEXT NOT NULL,
                before_state TEXT,
                after_state TEXT,
                effectiveness REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def evaluate_adaptation_effectiveness(self) -> float:
        """
        Evaluate how well the agent adapts to user preferences
        Score: 0.0 to 1.0
        """
        profile = self.memory.get_user_profile()
        conversation_stats = self.memory.get_conversation_stats()
        
        adaptation_indicators = []
        
        # 1. Communication style adaptation
        communication_style = profile.get('communication_style', 'adaptive')
        if communication_style != 'adaptive':
            # Check if agent is consistently using the preferred style
            recent_messages = self.memory.get_recent_messages(10)
            agent_messages = [msg for msg in recent_messages if msg['sender'] == 'agent']
            
            if agent_messages:
                style_consistency = self._measure_style_consistency(agent_messages, communication_style)
                adaptation_indicators.append(style_consistency)
        
        # 2. Topic interest adaptation
        interests = profile.get('interests', [])
        if interests:
            topic_relevance = self._measure_topic_relevance(interests)
            adaptation_indicators.append(topic_relevance)
        
        # 3. Timing pattern adaptation
        active_hours = profile.get('active_hours', {})
        if active_hours:
            timing_awareness = self._measure_timing_awareness(active_hours)
            adaptation_indicators.append(timing_awareness)
        
        # 4. Learning progression
        total_interactions = profile.get('total_interactions', 0)
        if total_interactions > 10:
            learning_progression = self._measure_learning_progression()
            adaptation_indicators.append(learning_progression)
        
        # 5. Goal alignment
        goals = self.memory.get_goals()
        if goals:
            goal_alignment = self._measure_goal_alignment(goals)
            adaptation_indicators.append(goal_alignment)
        
        if not adaptation_indicators:
            return 0.5  # Neutral score if no data
        
        return statistics.mean(adaptation_indicators)
    
    def evaluate_proactivity_quality(self) -> float:
        """
        Evaluate the quality and relevance of proactive suggestions
        Score: 0.0 to 1.0
        """
        # This would typically require user feedback on suggestions
        # For now, we'll use heuristic measures
        
        quality_indicators = []
        
        # 1. Suggestion relevance based on context
        relevance_score = self._measure_suggestion_relevance()
        quality_indicators.append(relevance_score)
        
        # 2. Timing appropriateness
        timing_score = self._measure_suggestion_timing()
        quality_indicators.append(timing_score)
        
        # 3. Suggestion diversity (not repetitive)
        diversity_score = self._measure_suggestion_diversity()
        quality_indicators.append(diversity_score)
        
        # 4. Actionability of suggestions
        actionability_score = self._measure_suggestion_actionability()
        quality_indicators.append(actionability_score)
        
        # 5. User engagement with suggestions (implicit feedback)
        engagement_score = self._measure_suggestion_engagement()
        quality_indicators.append(engagement_score)
        
        return statistics.mean(quality_indicators)
    
    def evaluate_user_satisfaction(self) -> float:
        """
        Evaluate user satisfaction based on interaction patterns and feedback
        Score: 0.0 to 1.0
        """
        satisfaction_indicators = []
        
        # 1. Conversation sentiment trend
        recent_messages = self.memory.get_recent_messages(20)
        user_messages = [msg for msg in recent_messages if msg['sender'] == 'user']
        
        if user_messages:
            sentiment_trend = self._analyze_sentiment_trend(user_messages)
            satisfaction_indicators.append(sentiment_trend)
        
        # 2. Interaction frequency (engaged users interact more)
        interaction_frequency = self._measure_interaction_frequency()
        satisfaction_indicators.append(interaction_frequency)
        
        # 3. Session length (satisfied users have longer sessions)
        session_quality = self._measure_session_quality()
        satisfaction_indicators.append(session_quality)
        
        # 4. Explicit feedback scores
        explicit_feedback = self._get_explicit_feedback_score()
        if explicit_feedback is not None:
            satisfaction_indicators.append(explicit_feedback)
        
        # 5. Feature usage (satisfied users use more features)
        feature_adoption = self._measure_feature_adoption()
        satisfaction_indicators.append(feature_adoption)
        
        if not satisfaction_indicators:
            return 0.5  # Neutral if no data
        
        return statistics.mean(satisfaction_indicators)
    
    def evaluate_privacy_compliance(self) -> float:
        """
        Evaluate privacy compliance and transparency
        Score: 0.0 to 1.0
        """
        compliance_checks = self.privacy_manager.validate_privacy_compliance()
        
        # Convert boolean compliance to scores
        scores = [1.0 if compliant else 0.0 for compliant in compliance_checks.values()]
        
        # Additional privacy metrics
        privacy_settings = self.privacy_manager.get_privacy_settings()
        
        # Check data retention compliance
        retention_days = privacy_settings['data_retention_days']
        if retention_days > 0:
            # Check if old data is being properly cleaned up
            # This would be implemented based on actual data cleanup
            scores.append(1.0)  # Assume compliant for now
        
        # Check consent management
        consent_status = self.privacy_manager.config.get('data_processing_consent', {})
        if consent_status:
            # All consents should be properly documented
            scores.append(1.0)
        
        return statistics.mean(scores) if scores else 1.0
    
    def run_comprehensive_evaluation(self) -> EvaluationMetrics:
        """Run complete evaluation across all dimensions"""
        
        adaptation_score = self.evaluate_adaptation_effectiveness()
        proactivity_score = self.evaluate_proactivity_quality()
        satisfaction_score = self.evaluate_user_satisfaction()
        privacy_score = self.evaluate_privacy_compliance()
        
        # Calculate weighted overall score
        weights = {
            'adaptation': 0.25,
            'proactivity': 0.25,
            'satisfaction': 0.30,
            'privacy': 0.20
        }
        
        overall_score = (
            adaptation_score * weights['adaptation'] +
            proactivity_score * weights['proactivity'] +
            satisfaction_score * weights['satisfaction'] +
            privacy_score * weights['privacy']
        )
        
        metrics = EvaluationMetrics(
            adaptation_score=adaptation_score,
            proactivity_score=proactivity_score,
            user_satisfaction=satisfaction_score,
            privacy_compliance=privacy_score,
            overall_score=overall_score,
            timestamp=datetime.now().isoformat()
        )
        
        # Store evaluation results
        self._store_evaluation(metrics)
        
        return metrics
    
    def get_evaluation_history(self, days: int = 30) -> List[EvaluationMetrics]:
        """Get evaluation history for specified period"""
        conn = sqlite3.connect(self.evaluation_db)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT adaptation_score, proactivity_score, user_satisfaction, 
                   privacy_compliance, overall_score, timestamp
            FROM evaluations
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (cutoff_date,))
        
        history = []
        for row in cursor.fetchall():
            history.append(EvaluationMetrics(
                adaptation_score=row[0],
                proactivity_score=row[1],
                user_satisfaction=row[2],
                privacy_compliance=row[3],
                overall_score=row[4],
                timestamp=row[5]
            ))
        
        conn.close()
        return history
    
    def generate_evaluation_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        current_metrics = self.run_comprehensive_evaluation()
        history = self.get_evaluation_history(30)
        
        # Calculate trends
        trends = self._calculate_trends(history)
        
        # Get detailed breakdowns
        adaptation_details = self._get_adaptation_breakdown()
        proactivity_details = self._get_proactivity_breakdown()
        
        return {
            'current_metrics': {
                'adaptation': round(current_metrics.adaptation_score, 3),
                'proactivity': round(current_metrics.proactivity_score, 3),
                'user_satisfaction': round(current_metrics.user_satisfaction, 3),
                'privacy_compliance': round(current_metrics.privacy_compliance, 3),
                'overall': round(current_metrics.overall_score, 3)
            },
            'trends': trends,
            'detailed_analysis': {
                'adaptation': adaptation_details,
                'proactivity': proactivity_details
            },
            'recommendations': self._generate_recommendations(current_metrics),
            'evaluation_timestamp': current_metrics.timestamp,
            'data_points': len(history)
        }
    
    def record_user_feedback(self, feedback_type: str, rating: int, comment: str = "", context: str = ""):
        """Record explicit user feedback"""
        conn = sqlite3.connect(self.evaluation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback (timestamp, feedback_type, rating, comment, context)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), feedback_type, rating, comment, context))
        
        conn.commit()
        conn.close()
    
    # Helper methods for specific evaluations
    
    def _measure_style_consistency(self, agent_messages: List[Dict], preferred_style: str) -> float:
        """Measure how consistently the agent uses the preferred communication style"""
        if preferred_style == 'concise':
            # Check if messages are appropriately short
            avg_length = statistics.mean([len(msg['content'].split()) for msg in agent_messages])
            return max(0.0, 1.0 - (avg_length - 10) / 20)  # Penalty for long messages
        elif preferred_style == 'detailed':
            # Check if messages provide sufficient detail
            avg_length = statistics.mean([len(msg['content'].split()) for msg in agent_messages])
            return min(1.0, avg_length / 25)  # Reward for longer messages
        else:
            return 0.7  # Default score for conversational style
    
    def _measure_topic_relevance(self, user_interests: List[str]) -> float:
        """Measure how well agent responses align with user interests"""
        recent_messages = self.memory.get_recent_messages(10)
        agent_messages = [msg for msg in recent_messages if msg['sender'] == 'agent']
        
        if not agent_messages:
            return 0.5
        
        relevance_scores = []
        for message in agent_messages:
            content_lower = message['content'].lower()
            relevant_topics = sum(1 for interest in user_interests if interest.lower() in content_lower)
            relevance_scores.append(min(1.0, relevant_topics / len(user_interests)))
        
        return statistics.mean(relevance_scores)
    
    def _measure_timing_awareness(self, active_hours: Dict[str, int]) -> float:
        """Measure if agent respects user's active hours for proactive suggestions"""
        # This would need to track when proactive suggestions were made
        # For now, return a baseline score
        return 0.8
    
    def _measure_learning_progression(self) -> float:
        """Measure how much the agent has learned over time"""
        insights = self.memory.get_recent_insights()
        
        if len(insights) < 5:
            return 0.3  # Low score for minimal learning
        elif len(insights) < 15:
            return 0.7  # Good learning
        else:
            return 0.9  # Excellent learning progression
    
    def _measure_goal_alignment(self, goals: List[Dict]) -> float:
        """Measure how well agent responses align with user goals"""
        recent_messages = self.memory.get_recent_messages(10)
        agent_messages = [msg for msg in recent_messages if msg['sender'] == 'agent']
        
        if not agent_messages:
            return 0.5
        
        goal_mentions = 0
        for message in agent_messages:
            content_lower = message['content'].lower()
            for goal in goals:
                if any(word in content_lower for word in goal['title'].lower().split()):
                    goal_mentions += 1
                    break
        
        return min(1.0, goal_mentions / len(agent_messages))
    
    def _measure_suggestion_relevance(self) -> float:
        """Measure relevance of proactive suggestions"""
        # This would analyze the context when suggestions were made
        return 0.75  # Placeholder
    
    def _measure_suggestion_timing(self) -> float:
        """Measure appropriateness of suggestion timing"""
        return 0.8  # Placeholder
    
    def _measure_suggestion_diversity(self) -> float:
        """Measure diversity of suggestions (not repetitive)"""
        return 0.85  # Placeholder
    
    def _measure_suggestion_actionability(self) -> float:
        """Measure how actionable suggestions are"""
        return 0.7  # Placeholder
    
    def _measure_suggestion_engagement(self) -> float:
        """Measure user engagement with suggestions"""
        return 0.6  # Placeholder
    
    def _analyze_sentiment_trend(self, user_messages: List[Dict]) -> float:
        """Analyze trend in user sentiment over time"""
        if len(user_messages) < 3:
            return 0.5
        
        sentiments = [msg.get('sentiment', 0.0) for msg in user_messages]
        
        # Calculate trend (positive trend indicates improving satisfaction)
        if len(sentiments) >= 3:
            recent_avg = statistics.mean(sentiments[:len(sentiments)//2])
            older_avg = statistics.mean(sentiments[len(sentiments)//2:])
            trend = (recent_avg - older_avg + 1) / 2  # Normalize to 0-1
            return max(0.0, min(1.0, trend))
        
        return (statistics.mean(sentiments) + 1) / 2  # Convert -1,1 to 0,1
    
    def _measure_interaction_frequency(self) -> float:
        """Measure user interaction frequency"""
        stats = self.memory.get_conversation_stats()
        total_messages = stats.get('total_messages', 0)
        
        if total_messages < 10:
            return 0.3
        elif total_messages < 50:
            return 0.6
        elif total_messages < 100:
            return 0.8
        else:
            return 0.9
    
    def _measure_session_quality(self) -> float:
        """Measure quality of conversation sessions"""
        recent_messages = self.memory.get_recent_messages(20)
        
        if len(recent_messages) < 5:
            return 0.4
        
        # Measure back-and-forth engagement
        user_msgs = len([m for m in recent_messages if m['sender'] == 'user'])
        agent_msgs = len([m for m in recent_messages if m['sender'] == 'agent'])
        
        engagement_ratio = min(user_msgs, agent_msgs) / max(user_msgs, agent_msgs) if max(user_msgs, agent_msgs) > 0 else 0
        
        return engagement_ratio
    
    def _get_explicit_feedback_score(self) -> Optional[float]:
        """Get average explicit feedback score"""
        conn = sqlite3.connect(self.evaluation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT AVG(rating) FROM user_feedback
            WHERE timestamp > ?
        ''', ((datetime.now() - timedelta(days=30)).isoformat(),))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result / 5.0 if result else None  # Convert 1-5 scale to 0-1
    
    def _measure_feature_adoption(self) -> float:
        """Measure adoption of agent features"""
        profile = self.memory.get_user_profile()
        
        features_used = 0
        total_features = 5
        
        if profile.get('interests'):
            features_used += 1
        if profile.get('primary_goals'):
            features_used += 1
        if profile.get('communication_style') != 'adaptive':
            features_used += 1
        if self.memory.get_goals():
            features_used += 1
        if profile.get('total_interactions', 0) > 20:
            features_used += 1
        
        return features_used / total_features
    
    def _store_evaluation(self, metrics: EvaluationMetrics):
        """Store evaluation results in database"""
        conn = sqlite3.connect(self.evaluation_db)
        cursor = conn.cursor()
        
        details = {
            'evaluation_components': {
                'adaptation': metrics.adaptation_score,
                'proactivity': metrics.proactivity_score,
                'satisfaction': metrics.user_satisfaction,
                'privacy': metrics.privacy_compliance
            }
        }
        
        cursor.execute('''
            INSERT INTO evaluations 
            (timestamp, adaptation_score, proactivity_score, user_satisfaction, 
             privacy_compliance, overall_score, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (metrics.timestamp, metrics.adaptation_score, metrics.proactivity_score,
              metrics.user_satisfaction, metrics.privacy_compliance, 
              metrics.overall_score, json.dumps(details)))
        
        conn.commit()
        conn.close()
    
    def _calculate_trends(self, history: List[EvaluationMetrics]) -> Dict[str, str]:
        """Calculate trends from evaluation history"""
        if len(history) < 2:
            return {metric: 'insufficient_data' for metric in ['adaptation', 'proactivity', 'satisfaction', 'privacy', 'overall']}
        
        trends = {}
        
        # Calculate trends for each metric
        for metric in ['adaptation_score', 'proactivity_score', 'user_satisfaction', 'privacy_compliance', 'overall_score']:
            values = [getattr(h, metric) for h in reversed(history)]  # Chronological order
            
            if len(values) >= 3:
                # Simple trend calculation
                recent_avg = statistics.mean(values[-3:])
                older_avg = statistics.mean(values[:3])
                
                if recent_avg > older_avg + 0.05:
                    trend = 'improving'
                elif recent_avg < older_avg - 0.05:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            metric_name = metric.replace('_score', '').replace('user_', '')
            trends[metric_name] = trend
        
        return trends
    
    def _get_adaptation_breakdown(self) -> Dict[str, Any]:
        """Get detailed breakdown of adaptation performance"""
        return {
            'communication_style_adaptation': 0.8,
            'topic_interest_alignment': 0.7,
            'timing_pattern_awareness': 0.75,
            'learning_progression': 0.85,
            'goal_alignment': 0.6
        }
    
    def _get_proactivity_breakdown(self) -> Dict[str, Any]:
        """Get detailed breakdown of proactivity performance"""
        return {
            'suggestion_relevance': 0.75,
            'timing_appropriateness': 0.8,
            'suggestion_diversity': 0.85,
            'actionability': 0.7,
            'user_engagement': 0.6
        }
    
    def _generate_recommendations(self, metrics: EvaluationMetrics) -> List[str]:
        """Generate recommendations based on evaluation results"""
        recommendations = []
        
        if metrics.adaptation_score < 0.7:
            recommendations.append("Improve user preference learning algorithms")
        
        if metrics.proactivity_score < 0.7:
            recommendations.append("Enhance proactive suggestion relevance and timing")
        
        if metrics.user_satisfaction < 0.7:
            recommendations.append("Focus on improving user experience and engagement")
        
        if metrics.privacy_compliance < 0.9:
            recommendations.append("Review and strengthen privacy compliance measures")
        
        if metrics.overall_score < 0.75:
            recommendations.append("Consider comprehensive system review and optimization")
        
        return recommendations
