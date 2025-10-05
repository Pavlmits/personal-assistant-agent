"""
Proactive Manager - Integration Layer
Coordinates all hybrid architecture components with the main agent
"""

import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging
from pathlib import Path

from .cache_database import CacheDatabase, TriggerRule, NotificationRecord
from .background_scheduler import BackgroundScheduler, SchedulerConfig
from .notification_system import NotificationSystem, NotificationConfig
from .ai_service_client import AIServiceClient
from .memory import UserMemory
from .clients.calendar_integration import CalendarManager
from .privacy import PrivacyManager

@dataclass
class ProactiveConfig:
    """Configuration for proactive manager"""
    enabled: bool = True
    check_interval: int = 900  # 15 minutes
    max_notifications_per_hour: int = 6
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 7     # 7 AM
    notification_priority_threshold: float = 0.7
    learning_enabled: bool = True
    calendar_integration: bool = True
    goal_tracking: bool = True
    pattern_analysis: bool = True

class ProactiveManager:
    """
    Central coordinator for the hybrid proactive architecture
    Integrates all components and manages the proactive experience
    """
    
    def __init__(self, 
                 memory: UserMemory,
                 calendar_manager: CalendarManager,
                 privacy_manager: PrivacyManager,
                 config: Optional[ProactiveConfig] = None):
        
        self.memory = memory
        self.calendar_manager = calendar_manager
        self.privacy_manager = privacy_manager
        self.config = config or ProactiveConfig()
        
        # Initialize hybrid architecture components
        self.cache_db = CacheDatabase()
        self.ai_service = AIServiceClient()
        self.notification_system = NotificationSystem()
        self.background_scheduler = None
        
        # State management
        self.running = False
        self.sync_lock = threading.RLock()
        self.last_sync = {}
        
        # Performance tracking
        self.metrics = {
            'notifications_sent': 0,
            'user_interactions': 0,
            'sync_operations': 0,
            'cache_hits': 0,
            'ai_generations': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all hybrid architecture components"""
        try:
            # Setup notification callbacks
            self._setup_notification_callbacks()
            
            # Initialize default trigger rules
            self._initialize_trigger_rules()
            
            # Perform initial data sync
            self._sync_all_data()
            
            self.logger.info("Proactive manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing proactive manager: {e}")
            raise
    
    def _setup_notification_callbacks(self):
        """Setup callbacks for notification interactions"""
        def notification_callback(notification_id: str, action: str):
            """Handle notification user interactions"""
            try:
                self.logger.info(f"Notification interaction: {notification_id} -> {action}")
                
                # Record user response
                response_time = time.time()  # Simplified - would calculate actual response time
                self.cache_db.update_notification_response(notification_id, action, response_time)
                
                # Update metrics
                self.metrics['user_interactions'] += 1
                
                # Learn from user response
                self._learn_from_notification_response(notification_id, action)
                
                # Handle specific actions
                if action == 'clicked':
                    self._handle_notification_click(notification_id)
                elif action == 'dismissed':
                    self._handle_notification_dismiss(notification_id)
                elif action.startswith('action_'):
                    self._handle_notification_action(notification_id, action)
                
            except Exception as e:
                self.logger.error(f"Error in notification callback: {e}")
        
        # Register callback with notification system
        self.notification_callback = notification_callback
    
    def _initialize_trigger_rules(self):
        """Initialize trigger rules based on user preferences and privacy settings"""
        privacy_level = self.privacy_manager.get_privacy_level()
        
        # Adjust trigger rules based on privacy level
        if privacy_level == 'minimal':
            # Very limited proactive features
            rules = [
                TriggerRule(
                    id="calendar_urgent_only",
                    rule_type="calendar",
                    conditions={"minutes_before": [15, 30]},
                    threshold=0.9,
                    enabled=True,
                    user_preference="high"
                )
            ]
        elif privacy_level == 'balanced':
            # Standard proactive features
            rules = [
                TriggerRule(
                    id="calendar_meetings",
                    rule_type="calendar",
                    conditions={"minutes_before": [30, 120]},
                    threshold=0.7,
                    enabled=True,
                    user_preference="medium"
                ),
                TriggerRule(
                    id="goal_reminders",
                    rule_type="goal",
                    conditions={"days_since_update": 3},
                    threshold=0.6,
                    enabled=True,
                    user_preference="medium"
                ),
                TriggerRule(
                    id="pattern_suggestions",
                    rule_type="pattern",
                    conditions={"active_hour_threshold": 5},
                    threshold=0.5,
                    enabled=True,
                    user_preference="low"
                )
            ]
        else:  # 'full'
            # All proactive features enabled
            rules = [
                TriggerRule(
                    id="calendar_all_events",
                    rule_type="calendar",
                    conditions={"minutes_before": [30, 180]},
                    threshold=0.6,
                    enabled=True,
                    user_preference="medium"
                ),
                TriggerRule(
                    id="goal_tracking",
                    rule_type="goal",
                    conditions={"days_since_update": 2},
                    threshold=0.5,
                    enabled=True,
                    user_preference="medium"
                ),
                TriggerRule(
                    id="pattern_optimization",
                    rule_type="pattern",
                    conditions={"active_hour_threshold": 3},
                    threshold=0.4,
                    enabled=True,
                    user_preference="low"
                ),
                TriggerRule(
                    id="learning_insights",
                    rule_type="learning",
                    conditions={"insight_count": 3},
                    threshold=0.7,
                    enabled=True,
                    user_preference="medium"
                )
            ]
        
        # Store trigger rules
        for rule in rules:
            self.cache_db.upsert_trigger_rule(rule)
        
        self.logger.info(f"Initialized {len(rules)} trigger rules for privacy level: {privacy_level}")
    
    def start_proactive_system(self):
        """Start the proactive system"""
        if self.running:
            self.logger.warning("Proactive system already running")
            return
        
        if not self.config.enabled:
            self.logger.info("Proactive system disabled in configuration")
            return
        
        try:
            self.logger.info("Starting proactive system")
            
            # Start background scheduler
            scheduler_config = SchedulerConfig(
                check_interval=self.config.check_interval,
                notification_rate_limit=self.config.max_notifications_per_hour,
                max_memory_mb=100,  # Allow more memory for full system
                max_cpu_percent=10.0
            )
            
            self.background_scheduler = BackgroundScheduler(scheduler_config)
            self.background_scheduler.start()
            
            # Start periodic sync
            self._start_sync_thread()
            
            # Precompute common responses
            self.ai_service.precompute_common_responses()
            
            self.running = True
            self.logger.info("Proactive system started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting proactive system: {e}")
            raise
    
    def stop_proactive_system(self):
        """Stop the proactive system"""
        if not self.running:
            return
        
        self.logger.info("Stopping proactive system")
        
        try:
            self.running = False
            
            # Stop background scheduler
            if self.background_scheduler:
                self.background_scheduler.stop()
                self.background_scheduler = None
            
            # Cleanup components
            self.ai_service.cleanup()
            self.notification_system.cleanup()
            self.cache_db.close()
            
            self.logger.info("Proactive system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping proactive system: {e}")
    
    def _start_sync_thread(self):
        """Start background thread for data synchronization"""
        def sync_worker():
            while self.running:
                try:
                    self._sync_all_data()
                    time.sleep(300)  # Sync every 5 minutes
                except Exception as e:
                    self.logger.error(f"Error in sync thread: {e}")
                    time.sleep(60)  # Wait before retrying
        
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_thread.start()
        self.logger.info("Data sync thread started")
    
    def _sync_all_data(self):
        """Synchronize data between main agent and cache database"""
        with self.sync_lock:
            try:
                self.logger.debug("Starting data synchronization")
                
                # Sync user patterns
                self._sync_user_patterns()
                
                # Sync goals
                if self.config.goal_tracking:
                    self._sync_goals()
                
                # Sync calendar data
                if self.config.calendar_integration and self.calendar_manager.is_available():
                    self._sync_calendar_data()
                
                # Update metrics
                self.metrics['sync_operations'] += 1
                self.last_sync['all_data'] = datetime.now().isoformat()
                
                self.logger.debug("Data synchronization completed")
                
            except Exception as e:
                self.logger.error(f"Error in data synchronization: {e}")
    
    def _sync_user_patterns(self):
        """Sync user patterns from main memory to cache"""
        try:
            profile = self.memory.get_user_profile()
            
            # Sync communication style
            if 'communication_style' in profile:
                self.cache_db.update_user_pattern(
                    'communication_style',
                    {'style': profile['communication_style']},
                    0.8
                )
            
            # Sync interests
            if 'interests' in profile:
                self.cache_db.update_user_pattern(
                    'interests',
                    profile['interests'],
                    0.7
                )
            
            # Sync active hours
            if 'active_hours' in profile:
                self.cache_db.update_user_pattern(
                    'active_hours',
                    profile['active_hours'],
                    0.9
                )
            
            # Sync recent insights
            recent_insights = self.memory.get_recent_insights()
            if recent_insights:
                self.cache_db.update_user_pattern(
                    'recent_insights',
                    recent_insights,
                    0.8
                )
            
            self.last_sync['user_patterns'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error syncing user patterns: {e}")
    
    def _sync_goals(self):
        """Sync goals from main memory to cache"""
        try:
            goals = self.memory.get_goals()
            
            # Convert to cache format
            cache_goals = []
            for goal in goals:
                cache_goal = {
                    'id': goal.get('id', goal['title']),
                    'title': goal['title'],
                    'description': goal.get('description', ''),
                    'progress': goal.get('progress', 0),
                    'target_date': goal.get('target_date'),
                    'last_updated': goal.get('last_updated', datetime.now().isoformat()),
                    'status': goal.get('status', 'active')
                }
                cache_goals.append(cache_goal)
            
            self.cache_db.sync_goals_cache(cache_goals)
            self.last_sync['goals'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error syncing goals: {e}")
    
    def _sync_calendar_data(self):
        """Sync calendar data to cache"""
        try:
            # Get upcoming events
            upcoming_events = self.calendar_manager.get_upcoming_events(limit=20)
            
            if upcoming_events:
                self.cache_db.sync_calendar_cache(upcoming_events)
                self.last_sync['calendar'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error syncing calendar data: {e}")
    
    def _learn_from_notification_response(self, notification_id: str, action: str):
        """Learn from user responses to improve future notifications"""
        if not self.config.learning_enabled:
            return
        
        try:
            # Get notification details
            notification = self.cache_db.active_notifications.get(notification_id)
            if not notification:
                return
            
            # Determine if response was positive
            positive_responses = ['clicked', 'action_view', 'action_ok', 'action_yes']
            was_successful = action in positive_responses
            
            # Update trigger rule success rate
            # This would need the trigger rule ID from the notification record
            # For now, we'll update based on category
            category = notification.get('category', 'general')
            trigger_rules = self.cache_db.get_active_trigger_rules(category)
            
            for rule in trigger_rules:
                self.cache_db.update_trigger_success(rule.id, was_successful)
            
            # Learn timing preferences
            sent_time = datetime.fromisoformat(notification['sent_at'])
            hour = sent_time.hour
            
            if was_successful:
                # This hour is good for notifications
                pattern = self.cache_db.get_user_pattern('notification_timing') or {'data': {}, 'confidence': 0.5}
                timing_data = pattern['data']
                timing_data[str(hour)] = timing_data.get(str(hour), 0) + 1
                
                self.cache_db.update_user_pattern(
                    'notification_timing',
                    timing_data,
                    min(pattern['confidence'] + 0.1, 1.0)
                )
            
            self.logger.debug(f"Learned from notification response: {action} -> {'positive' if was_successful else 'negative'}")
            
        except Exception as e:
            self.logger.error(f"Error learning from notification response: {e}")
    
    def _handle_notification_click(self, notification_id: str):
        """Handle notification click events"""
        # This could open the main app, show relevant information, etc.
        self.logger.info(f"User clicked notification: {notification_id}")
    
    def _handle_notification_dismiss(self, notification_id: str):
        """Handle notification dismissal"""
        # Learn that this type of notification might be less useful
        self.logger.info(f"User dismissed notification: {notification_id}")
    
    def _handle_notification_action(self, notification_id: str, action: str):
        """Handle specific notification actions"""
        self.logger.info(f"User performed action: {notification_id} -> {action}")
        
        # Handle common actions
        if action == 'action_snooze':
            # Reschedule notification for later
            pass
        elif action == 'action_complete':
            # Mark associated goal/task as complete
            pass
        elif action == 'action_view':
            # Show more details
            pass
    
    # Public API methods
    
    def send_immediate_notification(self, title: str, message: str, 
                                  category: str = "manual", 
                                  priority: str = "normal") -> Optional[str]:
        """Send an immediate notification (bypassing normal triggers)"""
        try:
            notification_id = self.notification_system.send_notification(
                title=title,
                message=message,
                category=category,
                actions=['View', 'Dismiss'],
                callback=self.notification_callback,
                priority=priority
            )
            
            if notification_id:
                # Record notification
                record = NotificationRecord(
                    id=notification_id,
                    trigger_rule_id="manual",
                    content=message,
                    sent_at=datetime.now().isoformat()
                )
                self.cache_db.record_notification(record)
                
                self.metrics['notifications_sent'] += 1
                self.logger.info(f"Sent immediate notification: {notification_id}")
            
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Error sending immediate notification: {e}")
            return None
    
    def update_proactive_config(self, new_config: Dict[str, Any]):
        """Update proactive configuration"""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated proactive config: {key} = {value}")
        
        # Update background scheduler if running
        if self.background_scheduler:
            scheduler_updates = {}
            if 'check_interval' in new_config:
                scheduler_updates['check_interval'] = new_config['check_interval']
            if 'max_notifications_per_hour' in new_config:
                scheduler_updates['notification_rate_limit'] = new_config['max_notifications_per_hour']
            
            if scheduler_updates:
                self.background_scheduler.update_config(scheduler_updates)
    
    def force_proactive_check(self, rule_type: Optional[str] = None):
        """Force an immediate proactive check"""
        if self.background_scheduler:
            self.background_scheduler.force_check(rule_type)
        else:
            self.logger.warning("Cannot force check - background scheduler not running")
    
    def get_proactive_status(self) -> Dict[str, Any]:
        """Get comprehensive proactive system status"""
        status = {
            'enabled': self.config.enabled,
            'running': self.running,
            'last_sync': self.last_sync,
            'metrics': self.metrics.copy(),
            'cache_stats': self.cache_db.get_cache_stats(),
            'notification_stats': self.cache_db.get_notification_stats(),
            'ai_service_stats': self.ai_service.get_service_stats(),
            'active_notifications': len(self.notification_system.get_active_notifications()),
            'trigger_rules_count': len(self.cache_db.get_active_trigger_rules())
        }
        
        if self.background_scheduler:
            status['scheduler_status'] = self.background_scheduler.get_status()
        
        return status
    
    def get_notification_history(self, days: int = 7) -> List[Dict]:
        """Get recent notification history"""
        try:
            # This would query the cache database for recent notifications
            # For now, return basic stats
            stats = self.cache_db.get_notification_stats(days)
            return [stats]  # Simplified
            
        except Exception as e:
            self.logger.error(f"Error getting notification history: {e}")
            return []
    
    def export_proactive_data(self) -> Dict[str, Any]:
        """Export proactive system data for analysis"""
        return {
            'config': self.config.__dict__,
            'metrics': self.metrics,
            'cache_stats': self.cache_db.get_cache_stats(),
            'notification_stats': self.cache_db.get_notification_stats(30),
            'trigger_rules': [rule.__dict__ for rule in self.cache_db.get_active_trigger_rules()],
            'export_timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Cleanup proactive manager resources"""
        self.logger.info("Cleaning up proactive manager")
        self.stop_proactive_system()

# Integration with main ProactiveAgent class
def integrate_with_main_agent():
    """
    This function shows how to integrate the ProactiveManager with the main agent
    """
    # This would be added to the main ProactiveAgent class in core.py
    
    example_integration = """
    # In agent/core.py ProactiveAgent.__init__():
    
    # Add proactive manager
    if enable_proactive_system:
        from .proactive_manager import ProactiveManager, ProactiveConfig
        
        proactive_config = ProactiveConfig(
            enabled=True,
            check_interval=900,  # 15 minutes
            max_notifications_per_hour=6,
            learning_enabled=privacy_manager.can_learn_preferences(),
            calendar_integration=calendar_manager.is_available(),
            goal_tracking=True,
            pattern_analysis=privacy_manager.can_learn_preferences()
        )
        
        self.proactive_manager = ProactiveManager(
            memory=memory,
            calendar_manager=calendar_manager,
            privacy_manager=privacy_manager,
            config=proactive_config
        )
        
        # Start proactive system
        self.proactive_manager.start_proactive_system()
    else:
        self.proactive_manager = None
    
    # Add methods to ProactiveAgent class:
    
    def enable_proactive_notifications(self, enabled: bool = True):
        if self.proactive_manager:
            self.proactive_manager.update_proactive_config({'enabled': enabled})
    
    def send_proactive_notification(self, title: str, message: str, priority: str = 'normal'):
        if self.proactive_manager:
            return self.proactive_manager.send_immediate_notification(title, message, priority=priority)
        return None
    
    def get_proactive_status(self):
        if self.proactive_manager:
            return self.proactive_manager.get_proactive_status()
        return {'enabled': False, 'running': False}
    """
    
    return example_integration

if __name__ == '__main__':
    # Example usage
    print("Proactive Manager Integration Example")
    print("=" * 50)
    print(integrate_with_main_agent())

