"""
User Memory and Profile Management
Handles persistent storage of user interactions, preferences, and learning
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

class UserMemory:
    """
    Manages user conversation history, preferences, and learned patterns
    """
    
    def __init__(self, db_path: str = "user_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                sentiment REAL,
                topics TEXT
            )
        ''')
        
        # User profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                progress INTEGER DEFAULT 0,
                target_date TEXT,
                created_at TEXT NOT NULL,
                last_updated TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Learning insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL,
                applied BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Interaction patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interaction_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_message(self, sender: str, content: str, context: Optional[Dict] = None):
        """Add a message to conversation history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        context_json = json.dumps(context) if context else None
        
        # Simple sentiment analysis (placeholder)
        sentiment = self._analyze_sentiment(content)
        
        # Extract topics (placeholder)
        topics = json.dumps(self._extract_topics(content))
        
        cursor.execute('''
            INSERT INTO conversations (timestamp, sender, content, context, sentiment, topics)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, sender, content, context_json, sentiment, topics))
        
        conn.commit()
        conn.close()
        
        # Learn from the message
        self._learn_from_message(sender, content, sentiment)
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, sender, content, context, sentiment, topics
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'timestamp': row[0],
                'sender': row[1],
                'content': row[2],
                'context': json.loads(row[3]) if row[3] else None,
                'sentiment': row[4],
                'topics': json.loads(row[5]) if row[5] else []
            })
        
        conn.close()
        return list(reversed(messages))  # Return in chronological order
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM user_profile')
        
        profile = {}
        for row in cursor.fetchall():
            try:
                profile[row[0]] = json.loads(row[1])
            except json.JSONDecodeError:
                profile[row[0]] = row[1]
        
        conn.close()
        
        # Ensure default values
        defaults = {
            'communication_style': 'adaptive',
            'interests': [],
            'active_hours': {},
            'interaction_preference': 'balanced',
            'learning_rate': 'normal',
            'total_interactions': 0,
            'primary_goals': [],
            'preferred_reminder_time': '09:00'
        }
        
        for key, default_value in defaults.items():
            if key not in profile:
                profile[key] = default_value
        
        return profile
    
    def update_user_profile(self, profile: Dict[str, Any]):
        """Update user profile data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        for key, value in profile.items():
            value_json = json.dumps(value) if not isinstance(value, str) else value
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profile (key, value, last_updated)
                VALUES (?, ?, ?)
            ''', (key, value_json, timestamp))
        
        conn.commit()
        conn.close()
    
    def add_goal(self, title: str, description: str = "", target_date: str = ""):
        """Add a new goal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO goals (title, description, target_date, created_at, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, target_date, timestamp, timestamp))
        
        conn.commit()
        conn.close()
        
        # Add to profile
        profile = self.get_user_profile()
        primary_goals = profile.get('primary_goals', [])
        if title not in primary_goals:
            primary_goals.append(title)
            profile['primary_goals'] = primary_goals[:5]  # Keep top 5
            self.update_user_profile(profile)
    
    def get_goals(self) -> List[Dict]:
        """Get all active goals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, description, progress, target_date, created_at, last_updated
            FROM goals
            WHERE status = 'active'
            ORDER BY created_at DESC
        ''')
        
        goals = []
        for row in cursor.fetchall():
            goals.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'progress': row[3],
                'target_date': row[4],
                'created_at': row[5],
                'last_updated': row[6]
            })
        
        conn.close()
        return goals
    
    def update_goal_progress(self, goal_id: int, progress: int):
        """Update progress on a goal by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE goals 
            SET progress = ?, last_updated = ?
            WHERE id = ? AND status = 'active'
        ''', (progress, timestamp, goal_id))
        
        conn.commit()
        conn.close()
    
    def add_insight(self, insight_type: str, content: str, confidence: float):
        """Add a learning insight"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO insights (insight_type, content, confidence, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (insight_type, content, confidence, timestamp))
        
        conn.commit()
        conn.close()
    
    def add_simple_insight(self, content: str):
        """Add a simple insight with default parameters"""
        self.add_insight("interaction", content, 0.8)
    
    def get_recent_insights(self, limit: int = 10) -> List[str]:
        """Get recent learning insights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content FROM insights
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        insights = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return insights
    
    def record_interaction_pattern(self, pattern_type: str, pattern_data: Dict):
        """Record an interaction pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        pattern_json = json.dumps(pattern_data)
        
        # Check if pattern exists
        cursor.execute('''
            SELECT frequency FROM interaction_patterns
            WHERE pattern_type = ? AND pattern_data = ?
        ''', (pattern_type, pattern_json))
        
        result = cursor.fetchone()
        
        if result:
            # Update existing pattern
            new_frequency = result[0] + 1
            cursor.execute('''
                UPDATE interaction_patterns
                SET frequency = ?, last_seen = ?
                WHERE pattern_type = ? AND pattern_data = ?
            ''', (new_frequency, timestamp, pattern_type, pattern_json))
        else:
            # Insert new pattern
            cursor.execute('''
                INSERT INTO interaction_patterns (pattern_type, pattern_data, last_seen)
                VALUES (?, ?, ?)
            ''', (pattern_type, pattern_json, timestamp))
        
        conn.commit()
        conn.close()
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total messages
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_messages = cursor.fetchone()[0]
        
        # Messages by sender
        cursor.execute('''
            SELECT sender, COUNT(*) 
            FROM conversations 
            GROUP BY sender
        ''')
        messages_by_sender = dict(cursor.fetchall())
        
        # Average sentiment
        cursor.execute('SELECT AVG(sentiment) FROM conversations WHERE sentiment IS NOT NULL')
        avg_sentiment = cursor.fetchone()[0] or 0.0
        
        # Most active hours
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM conversations
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 3
        ''')
        active_hours = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_messages': total_messages,
            'messages_by_sender': messages_by_sender,
            'average_sentiment': round(avg_sentiment, 2),
            'most_active_hours': [f"{hour}:00" for hour, _ in active_hours]
        }
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Simple sentiment analysis (placeholder)
        Returns value between -1.0 (negative) and 1.0 (positive)
        """
        positive_words = ['good', 'great', 'excellent', 'love', 'like', 'happy', 'thanks', 'perfect']
        negative_words = ['bad', 'terrible', 'hate', 'dislike', 'sad', 'angry', 'frustrated', 'problem']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Simple topic extraction (placeholder)
        In a real implementation, use NLP libraries
        """
        topics = []
        
        topic_keywords = {
            'work': ['work', 'job', 'office', 'project', 'meeting', 'deadline'],
            'health': ['exercise', 'gym', 'diet', 'health', 'doctor', 'medicine'],
            'learning': ['learn', 'study', 'book', 'course', 'skill', 'knowledge'],
            'personal': ['family', 'friend', 'relationship', 'personal', 'home'],
            'technology': ['code', 'programming', 'computer', 'software', 'tech'],
            'goals': ['goal', 'target', 'achieve', 'progress', 'plan', 'objective']
        }
        
        text_lower = text.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _learn_from_message(self, sender: str, content: str, sentiment: float):
        """
        Extract learning insights from messages
        """
        if sender == 'user':
            # Learn communication patterns
            message_length = len(content.split())
            
            if message_length < 5:
                self.add_insight('communication', 'User prefers concise communication', 0.7)
            elif message_length > 30:
                self.add_insight('communication', 'User provides detailed context', 0.8)
            
            # Learn from sentiment
            if sentiment > 0.5:
                self.add_insight('mood', 'User seems positive and engaged', 0.6)
            elif sentiment < -0.3:
                self.add_insight('mood', 'User may be frustrated or need support', 0.7)
            
            # Learn timing patterns
            hour = datetime.now().hour
            self.record_interaction_pattern('active_hour', {'hour': hour})
            
            # Learn topic preferences
            topics = self._extract_topics(content)
            for topic in topics:
                self.record_interaction_pattern('topic_interest', {'topic': topic})
    
    def export_data(self) -> Dict[str, Any]:
        """Export all user data for privacy compliance"""
        conn = sqlite3.connect(self.db_path)
        
        # Export conversations
        conversations = conn.execute('SELECT * FROM conversations').fetchall()
        
        # Export profile
        profile = conn.execute('SELECT * FROM user_profile').fetchall()
        
        # Export goals
        goals = conn.execute('SELECT * FROM goals').fetchall()
        
        # Export insights
        insights = conn.execute('SELECT * FROM insights').fetchall()
        
        conn.close()
        
        return {
            'conversations': conversations,
            'profile': profile,
            'goals': goals,
            'insights': insights,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def clear_data(self, data_type: str = 'all'):
        """Clear user data for privacy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if data_type == 'conversations' or data_type == 'all':
            cursor.execute('DELETE FROM conversations')
        
        if data_type == 'profile' or data_type == 'all':
            cursor.execute('DELETE FROM user_profile')
        
        if data_type == 'goals' or data_type == 'all':
            cursor.execute('DELETE FROM goals')
        
        if data_type == 'insights' or data_type == 'all':
            cursor.execute('DELETE FROM insights')
        
        if data_type == 'patterns' or data_type == 'all':
            cursor.execute('DELETE FROM interaction_patterns')
        
        conn.commit()
        conn.close()
