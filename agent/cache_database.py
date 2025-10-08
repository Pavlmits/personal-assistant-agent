"""
Cache Database for Hybrid Architecture
Optimized local storage for fast proactive checks
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import threading
import os

@dataclass
class TriggerRule:
    """Represents a trigger rule for notifications"""
    id: str
    rule_type: str  # 'calendar', 'goal', 'pattern', 'learning'
    conditions: Dict[str, Any]
    threshold: float
    enabled: bool
    user_preference: str  # 'high', 'medium', 'low', 'disabled'
    last_triggered: Optional[str] = None

@dataclass
class NotificationRecord:
    """Record of sent notifications"""
    id: str
    trigger_rule_id: str
    content: str
    sent_at: str
    user_response: Optional[str] = None  # 'clicked', 'dismissed', 'snoozed', 'acted'
    response_time: Optional[float] = None

class CacheDatabase:
    """
    High-performance cache database for proactive agent
    Optimized for fast reads and minimal resource usage
    """
    
    def __init__(self, db_path: str = "agent_cache.db"):
        self.db_path = db_path
        self.connection_pool = {}
        self.lock = threading.RLock()
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-safe database connection"""
        thread_id = threading.get_ident()
        
        if thread_id not in self.connection_pool:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            # Optimize for read performance
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            self.connection_pool[thread_id] = conn
        
        return self.connection_pool[thread_id]
    
    def _init_database(self):
        """Initialize cache database with optimized schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # User patterns table - frequently accessed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_patterns (
                pattern_type TEXT PRIMARY KEY,
                pattern_data TEXT NOT NULL,
                confidence REAL NOT NULL,
                last_updated TEXT NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        # Goals cache - optimized for deadline queries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals_cache (
                goal_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                progress INTEGER DEFAULT 0,
                target_date TEXT,
                last_updated TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                days_since_update INTEGER
            )
        ''')
        
        # Trigger rules - notification logic
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trigger_rules (
                rule_id TEXT PRIMARY KEY,
                rule_type TEXT NOT NULL,
                conditions TEXT NOT NULL,
                threshold REAL NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                user_preference TEXT DEFAULT 'medium',
                last_triggered TEXT,
                trigger_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0
            )
        ''')
        
        # Notification history - learning and analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_history (
                notification_id TEXT PRIMARY KEY,
                trigger_rule_id TEXT NOT NULL,
                content TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                user_response TEXT,
                response_time REAL,
                context_data TEXT,
                FOREIGN KEY (trigger_rule_id) REFERENCES trigger_rules (rule_id)
            )
        ''')
        
        # Context snapshots - pre-computed contexts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                context_type TEXT NOT NULL,
                context_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        # Performance indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_deadline ON goals_cache(target_date, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_stale ON goals_cache(days_since_update, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_recent ON notification_history(sent_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_triggers_enabled ON trigger_rules(enabled, rule_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_context_expires ON context_snapshots(expires_at)')
        
        # Initialize default trigger rules
        self._init_default_triggers()
        
        conn.commit()
    
    def _init_default_triggers(self):
        """Initialize default trigger rules"""
        default_triggers = [
            TriggerRule(
                id="calendar_upcoming_30min",
                rule_type="calendar",
                conditions={"minutes_before": [30, 120], "event_types": ["meeting", "appointment"]},
                threshold=0.8,
                enabled=True,
                user_preference="high"
            ),
            TriggerRule(
                id="goal_stale_3days",
                rule_type="goal",
                conditions={"days_since_update": 3, "progress_threshold": 100},
                threshold=0.7,
                enabled=True,
                user_preference="medium"
            ),
            TriggerRule(
                id="pattern_active_hours",
                rule_type="pattern",
                conditions={"active_hour_threshold": 5, "interest_match": True},
                threshold=0.6,
                enabled=True,
                user_preference="low"
            ),
            TriggerRule(
                id="learning_insights_ready",
                rule_type="learning",
                conditions={"insight_count": 3, "confidence_threshold": 0.7},
                threshold=0.8,
                enabled=True,
                user_preference="medium"
            )
        ]
        
        for trigger in default_triggers:
            self.upsert_trigger_rule(trigger)
    
    # User Patterns Methods
    def update_user_pattern(self, pattern_type: str, pattern_data: Dict, confidence: float):
        """Update user pattern with optimistic locking"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_patterns 
                (pattern_type, pattern_data, confidence, last_updated, access_count)
                VALUES (?, ?, ?, ?, COALESCE((SELECT access_count FROM user_patterns WHERE pattern_type = ?), 0))
            ''', (pattern_type, json.dumps(pattern_data), confidence, datetime.now().isoformat(), pattern_type))
            
            conn.commit()
    
    def get_user_pattern(self, pattern_type: str) -> Optional[Dict]:
        """Get user pattern with access tracking"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_patterns SET access_count = access_count + 1 
            WHERE pattern_type = ?
        ''', (pattern_type,))
        
        cursor.execute('''
            SELECT pattern_data, confidence, last_updated 
            FROM user_patterns WHERE pattern_type = ?
        ''', (pattern_type,))
        
        result = cursor.fetchone()
        if result:
            return {
                'data': json.loads(result['pattern_data']),
                'confidence': result['confidence'],
                'last_updated': result['last_updated']
            }
        return None
    
    # Goals Cache Methods
    def sync_goals_cache(self, goals: List[Dict]):
        """Sync goals from main database to cache"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Clear existing cache
            cursor.execute('DELETE FROM goals_cache')
            
            # Insert updated goals
            for goal in goals:
                last_updated = goal.get('last_updated', datetime.now().isoformat())
                
                # Calculate days since update
                try:
                    last_update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    days_since = (datetime.now() - last_update_date).days
                except:
                    days_since = 0
                
                cursor.execute('''
                    INSERT INTO goals_cache 
                    (goal_id, title, description, progress, target_date, last_updated, priority, status, days_since_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    goal.get('id', goal['title']),
                    goal['title'],
                    goal.get('description', ''),
                    goal.get('progress', 0),
                    goal.get('target_date'),
                    last_updated,
                    goal.get('priority', 1),
                    goal.get('status', 'active'),
                    days_since
                ))
            
            conn.commit()
    
    def get_stale_goals(self, days_threshold: int = 3) -> List[Dict]:
        """Get goals that haven't been updated recently"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT goal_id, title, description, progress, target_date, days_since_update
            FROM goals_cache 
            WHERE status = 'active' AND days_since_update >= ? AND progress < 100
            ORDER BY days_since_update DESC, priority DESC
        ''', (days_threshold,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_deadline_approaching_goals(self, days_ahead: int = 7) -> List[Dict]:
        """Get goals with approaching deadlines"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
        
        cursor.execute('''
            SELECT goal_id, title, description, progress, target_date,
                   (julianday(target_date) - julianday('now')) as days_until_deadline
            FROM goals_cache 
            WHERE status = 'active' AND target_date IS NOT NULL 
            AND target_date <= ? AND progress < 100
            ORDER BY days_until_deadline ASC
        ''', (future_date,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # Trigger Rules Methods
    def upsert_trigger_rule(self, rule: TriggerRule):
        """Insert or update trigger rule"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO trigger_rules 
                (rule_id, rule_type, conditions, threshold, enabled, user_preference, 
                 last_triggered, trigger_count, success_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, 
                        COALESCE((SELECT trigger_count FROM trigger_rules WHERE rule_id = ?), 0),
                        COALESCE((SELECT success_rate FROM trigger_rules WHERE rule_id = ?), 0.0))
            ''', (
                rule.id, rule.rule_type, json.dumps(rule.conditions), rule.threshold,
                rule.enabled, rule.user_preference, rule.last_triggered, rule.id, rule.id
            ))
            
            conn.commit()
    
    def get_active_trigger_rules(self, rule_type: Optional[str] = None) -> List[TriggerRule]:
        """Get active trigger rules"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM trigger_rules WHERE enabled = TRUE'
        params = []
        
        if rule_type:
            query += ' AND rule_type = ?'
            params.append(rule_type)
        
        query += ' ORDER BY user_preference DESC, success_rate DESC'
        
        cursor.execute(query, params)
        
        rules = []
        for row in cursor.fetchall():
            rules.append(TriggerRule(
                id=row['rule_id'],
                rule_type=row['rule_type'],
                conditions=json.loads(row['conditions']),
                threshold=row['threshold'],
                enabled=row['enabled'],
                user_preference=row['user_preference'],
                last_triggered=row['last_triggered']
            ))
        
        return rules
    
    def update_trigger_success(self, rule_id: str, was_successful: bool):
        """Update trigger rule success rate"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE trigger_rules 
                SET trigger_count = trigger_count + 1,
                    success_rate = (success_rate * trigger_count + ?) / (trigger_count + 1),
                    last_triggered = ?
                WHERE rule_id = ?
            ''', (1.0 if was_successful else 0.0, datetime.now().isoformat(), rule_id))
            
            conn.commit()
    
    # Notification History Methods
    def record_notification(self, record: NotificationRecord):
        """Record sent notification"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notification_history 
                (notification_id, trigger_rule_id, content, sent_at, user_response, response_time, context_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.id, record.trigger_rule_id, record.content, record.sent_at,
                record.user_response, record.response_time, None
            ))
            
            conn.commit()
    
    def update_notification_response(self, notification_id: str, response: str, response_time: float):
        """Update notification with user response"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE notification_history 
                SET user_response = ?, response_time = ?
                WHERE notification_id = ?
            ''', (response, response_time, notification_id))
            
            conn.commit()
    
    def get_notification_stats(self, days_back: int = 7) -> Dict[str, Any]:
        """Get notification statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sent,
                COUNT(user_response) as total_responses,
                AVG(response_time) as avg_response_time,
                COUNT(CASE WHEN user_response = 'clicked' THEN 1 END) as clicked,
                COUNT(CASE WHEN user_response = 'dismissed' THEN 1 END) as dismissed
            FROM notification_history 
            WHERE sent_at >= ?
        ''', (since_date,))
        
        overall = dict(cursor.fetchone())
        
        # By trigger type
        cursor.execute('''
            SELECT tr.rule_type, COUNT(*) as count, 
                   COUNT(nh.user_response) as responses,
                   AVG(nh.response_time) as avg_response_time
            FROM notification_history nh
            JOIN trigger_rules tr ON nh.trigger_rule_id = tr.rule_id
            WHERE nh.sent_at >= ?
            GROUP BY tr.rule_type
        ''', (since_date,))
        
        by_type = {row['rule_type']: dict(row) for row in cursor.fetchall()}
        
        return {
            'overall': overall,
            'by_type': by_type,
            'response_rate': overall['total_responses'] / max(overall['total_sent'], 1)
        }
    
    # Context Snapshots Methods
    def store_context_snapshot(self, context_type: str, context_data: Dict, ttl_minutes: int = 60):
        """Store pre-computed context snapshot"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            snapshot_id = f"{context_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            expires_at = (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat()
            
            cursor.execute('''
                INSERT INTO context_snapshots 
                (snapshot_id, context_type, context_data, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (snapshot_id, context_type, json.dumps(context_data), 
                  datetime.now().isoformat(), expires_at))
            
            conn.commit()
            return snapshot_id
    
    def get_context_snapshot(self, context_type: str) -> Optional[Dict]:
        """Get latest valid context snapshot"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE context_snapshots SET access_count = access_count + 1
            WHERE context_type = ? AND expires_at > datetime('now')
        ''', (context_type,))
        
        cursor.execute('''
            SELECT context_data, created_at FROM context_snapshots 
            WHERE context_type = ? AND expires_at > datetime('now')
            ORDER BY created_at DESC LIMIT 1
        ''', (context_type,))
        
        result = cursor.fetchone()
        if result:
            return {
                'data': json.loads(result['context_data']),
                'created_at': result['created_at']
            }
        return None
    
    def cleanup_expired_data(self):
        """Clean up expired snapshots and old notifications"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Remove expired context snapshots
            cursor.execute('DELETE FROM context_snapshots WHERE expires_at <= datetime("now")')
            
            # Remove old notifications (older than 30 days)
            old_date = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute('DELETE FROM notification_history WHERE sent_at < ?', (old_date,))
            
            conn.commit()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache database statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Table sizes
        tables = ['user_patterns', 'goals_cache', 'trigger_rules', 
                 'notification_history', 'context_snapshots']
        
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
            stats[f'{table}_count'] = cursor.fetchone()['count']
        
        # Database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        stats['db_size_bytes'] = cursor.fetchone()['size']
        
        return stats
    
    def close(self):
        """Close all database connections"""
        with self.lock:
            for conn in self.connection_pool.values():
                conn.close()
            self.connection_pool.clear()

