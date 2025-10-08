"""
Lightweight Background Scheduler
Minimal resource footprint, always-running process for proactive notifications
"""

import time
import threading
import signal
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
import psutil
import queue
from pathlib import Path

from .clients.calendar_integration import CalendarManager
from .cache_database import CacheDatabase, TriggerRule
from .notification_system import NotificationSystem

@dataclass
class SchedulerConfig:
    """Configuration for background scheduler"""
    check_interval: int = 900  # 15 minutes in seconds
    max_memory_mb: int = 50    # Maximum memory usage
    max_cpu_percent: float = 5.0  # Maximum CPU usage
    log_level: str = "INFO"
    enable_system_integration: bool = True
    notification_rate_limit: int = 10  # Max notifications per hour

class BackgroundScheduler:
    """
    Lightweight background scheduler for proactive notifications
    Designed for minimal resource usage and high reliability
    """
    
    def __init__(self, config: Optional[SchedulerConfig] = None, agent=None, calendar_manager=None, cache_db=None):
        self.config = config or SchedulerConfig()
        self.cache_db = cache_db if cache_db is not None else CacheDatabase()
        self.notification_system = NotificationSystem()
        self.agent = agent  # LangChainPersonalAgent instance
        self.calendar_manager = calendar_manager  # CalendarManager instance
        
        # Runtime state
        self.running = False
        self.last_check = {}
        self.notification_count = 0
        self.last_hour_reset = datetime.now().hour
        
        # Threading
        self.main_thread = None
        self.check_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        
        # Performance monitoring
        self.process = psutil.Process()
        self.performance_stats = {
            'checks_performed': 0,
            'notifications_sent': 0,
            'avg_check_time': 0.0,
            'memory_usage_mb': 0.0,
            'cpu_percent': 0.0
        }
        
        # Setup logging
        self._setup_logging()
        
        # Register signal handlers
        if self.config.enable_system_integration:
            self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Setup lightweight logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "scheduler.log"),
                logging.StreamHandler() if self.config.log_level == "DEBUG" else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.stop()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
    
    def start(self):
        """Start the background scheduler"""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.logger.info("Starting background scheduler")
        self.running = True
        
        # Start main monitoring thread
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        # Start performance monitoring thread
        perf_thread = threading.Thread(daemon=True)
        perf_thread.start()
        
        self.logger.info("Background scheduler started successfully")
    
    def stop(self):
        """Stop the background scheduler gracefully"""
        if not self.running:
            return
        
        self.logger.info("Stopping background scheduler")
        self.running = False
        self.shutdown_event.set()
        
        # Wait for main thread to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=30)
        
        # Cleanup resources
        self.cache_db.close()
        self.notification_system.cleanup()
        
        self.logger.info("Background scheduler stopped")
    
    def _main_loop(self):
        """Main scheduler loop"""
        self.logger.info("Main scheduler loop started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                start_time = time.time()
                
                # Reset notification rate limit hourly
                current_hour = datetime.now().hour
                if current_hour != self.last_hour_reset:
                    self.notification_count = 0
                    self.last_hour_reset = current_hour
                
                # Perform scheduled checks
                self._perform_checks()
                
                # Update performance stats
                check_time = time.time() - start_time
                self._update_performance_stats(check_time)
                
                # Cleanup expired data periodically
                if self.performance_stats['checks_performed'] % 24 == 0:  # Every ~6 hours
                    self.cache_db.cleanup_expired_data()
                
                # Sleep until next check
                self.shutdown_event.wait(timeout=self.config.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                # Brief pause before retrying
                self.shutdown_event.wait(timeout=60)
    
    def _perform_checks(self):
        """Perform all scheduled proactive checks"""
        if self.notification_count >= self.config.notification_rate_limit:
            self.logger.debug("Rate limit reached, skipping checks")
            return
        
        self.logger.debug("Performing proactive checks")
        
        # Get active trigger rules
        trigger_rules = self.cache_db.get_active_trigger_rules()
        
        for rule in trigger_rules:
            try:
                if self._should_check_rule(rule):
                    self._check_trigger_rule(rule)
            except Exception as e:
                self.logger.error(f"Error checking rule {rule.id}: {e}")
        
        self.performance_stats['checks_performed'] += 1
    
    def _should_check_rule(self, rule: TriggerRule) -> bool:
        """Determine if a rule should be checked now"""
        # Check rate limiting
        if self.notification_count >= self.config.notification_rate_limit:
            return False
        
        # Check if rule was triggered recently
        if rule.last_triggered:
            last_triggered = datetime.fromisoformat(rule.last_triggered)
            min_interval = self._get_rule_min_interval(rule)
            if datetime.now() - last_triggered < timedelta(minutes=min_interval):
                return False
        
        # Check user preference timing
        if not self._is_appropriate_time(rule.user_preference):
            return False
        
        return True
    
    def _get_rule_min_interval(self, rule: TriggerRule) -> int:
        """Get minimum interval between rule triggers (in minutes)"""
        intervals = {
            'calendar': 30,    # Calendar events can be checked frequently
            'goal': 240,       # Goals checked every 4 hours max
            'pattern': 120,    # Pattern-based every 2 hours
            'learning': 480    # Learning insights every 8 hours
        }
        return intervals.get(rule.rule_type, 120)
    
    def _is_appropriate_time(self, user_preference: str) -> bool:
        """Check if current time is appropriate for notifications"""
        current_hour = datetime.now().hour
        
        # Basic quiet hours (11 PM to 7 AM)
        if current_hour >= 23 or current_hour < 7:
            return user_preference == 'high'  # Only high priority during quiet hours
        
        # Get user's active hours pattern
        pattern = self.cache_db.get_user_pattern('active_hours')
        if pattern:
            active_hours = pattern['data']
            current_activity = active_hours.get(str(current_hour), 0)
            
            # Only notify during reasonably active hours
            if user_preference == 'low' and current_activity < 3:
                return False
            elif user_preference == 'medium' and current_activity < 2:
                return False
        
        return True
    
    def _check_trigger_rule(self, rule: TriggerRule):
        """Check a specific trigger rule and generate notifications if needed"""
        self.logger.debug(f"Checking trigger rule: {rule.id}")
        
        try:
            if rule.rule_type == 'calendar':
                self._check_calendar_triggers(rule)
            elif rule.rule_type == 'goal':
                self._check_goal_triggers(rule)
            elif rule.rule_type == 'pattern':
                self._check_pattern_triggers(rule)
            elif rule.rule_type == 'learning':
                self._check_learning_triggers(rule)
        except Exception as e:
            self.logger.error(f"Error in trigger rule {rule.id}: {e}")
    
    def _check_calendar_triggers(self, rule: TriggerRule):
        """Check calendar-based triggers"""
        # Always fetch fresh data from Google Calendar
        if not self.calendar_manager or not self.calendar_manager.is_available():
            return
        
        conditions = rule.conditions
        minutes_range = conditions.get('minutes_before', [30, 120])
        
        # Fetch events directly from Google Calendar
        upcoming_events = self.calendar_manager.get_upcoming_events(limit=20)
        
        # Filter events by time range
        now = datetime.now()
        filtered_events = []
        for event in upcoming_events:
            if event.get('time_until'):
                minutes_until = event['time_until'].total_seconds() / 60
                if minutes_range[0] <= minutes_until <= minutes_range[1]:
                    event['minutes_until'] = int(minutes_until)
                    filtered_events.append(event)
        
        for event in filtered_events:
            # Check if we should notify about this event
            if self._should_notify_about_event(event, rule):
                self._generate_notification(rule, 'calendar', {
                    'event': event,
                    'minutes_until': event['minutes_until']
                })
    
    def _check_goal_triggers(self, rule: TriggerRule):
        """Check goal-based triggers"""
        conditions = rule.conditions
        days_threshold = conditions.get('days_since_update', 3)
        
        stale_goals = self.cache_db.get_stale_goals(days_threshold)
        
        for goal in stale_goals[:2]:  # Limit to 2 goals per check
            if goal['progress'] < conditions.get('progress_threshold', 100):
                self._generate_notification(rule, 'goal', {
                    'goal': goal,
                    'days_stale': goal['days_since_update']
                })
    
    def _check_pattern_triggers(self, rule: TriggerRule):
        """Check pattern-based triggers"""
        conditions = rule.conditions
        
        # Check if user is typically active now
        pattern = self.cache_db.get_user_pattern('active_hours')
        if not pattern:
            return
        
        current_hour = str(datetime.now().hour)
        activity_level = pattern['data'].get(current_hour, 0)
        
        if activity_level >= conditions.get('active_hour_threshold', 5):
            # Check for interest match
            interests_pattern = self.cache_db.get_user_pattern('interests')
            if interests_pattern and conditions.get('interest_match'):
                self._generate_notification(rule, 'pattern', {
                    'activity_level': activity_level,
                    'interests': interests_pattern['data']
                })
    
    def _check_learning_triggers(self, rule: TriggerRule):
        """Check learning-based triggers"""
        conditions = rule.conditions
        
        # Get recent insights count
        insights_pattern = self.cache_db.get_user_pattern('recent_insights')
        if not insights_pattern:
            return
        
        insight_count = len(insights_pattern['data'])
        confidence = insights_pattern['confidence']
        
        if (insight_count >= conditions.get('insight_count', 3) and 
            confidence >= conditions.get('confidence_threshold', 0.7)):
            self._generate_notification(rule, 'learning', {
                'insight_count': insight_count,
                'confidence': confidence
            })
    
    def _should_notify_about_event(self, event: Dict, rule: TriggerRule) -> bool:
        """Determine if we should notify about a specific event"""
        # Check if we've already notified about this event
        recent_notifications = self.cache_db.get_notification_stats(days_back=1)
        
        # Simple heuristic: don't notify about the same event multiple times
        # In a real implementation, you'd store event-specific notification history
        
        return True  # Simplified for now
    
    def _generate_notification_with_agent(self, trigger_type: str, context: Dict, user_preference: str) -> Optional[str]:
        """Generate notification content using the LangChain agent"""
        
        if not self.agent:
            # Fallback to template-based generation
            return self._generate_template_notification(trigger_type, context)
        
        try:
            # Create a prompt for the agent to generate notification content
            if trigger_type == 'calendar':
                event = context.get('event', {})
                minutes = context.get('minutes_until', 0)
                prompt = f"Generate a brief, helpful notification message (max 2 sentences) to remind the user about their upcoming event: '{event.get('summary', 'Event')}' in {minutes} minutes."
            
            elif trigger_type == 'goal':
                goal = context.get('goal', {})
                days = context.get('days_stale', 0)
                prompt = f"Generate a brief, motivating notification message (max 2 sentences) to remind the user about their goal: '{goal.get('title', 'Goal')}' which hasn't been updated in {days} days."
            
            elif trigger_type == 'pattern':
                interests = context.get('interests', [])
                prompt = f"Generate a brief, helpful notification message (max 2 sentences) based on the user's interests: {', '.join(interests[:3])}. Suggest something relevant they might want to do."
            
            elif trigger_type == 'learning':
                insight_count = context.get('insight_count', 0)
                prompt = f"Generate a brief notification message (max 2 sentences) letting the user know you've learned {insight_count} new things about their preferences and asking if they'd like to see them."
            
            else:
                return self._generate_template_notification(trigger_type, context)
            
            # Use the agent to generate content (without saving to memory)
            result = self.agent.process_message(prompt, save_to_memory=False)
            
            if result['success']:
                return result['response']
            else:
                return self._generate_template_notification(trigger_type, context)
                
        except Exception as e:
            self.logger.error(f"Error generating notification with agent: {e}")
            return self._generate_template_notification(trigger_type, context)
    
    def _generate_template_notification(self, trigger_type: str, context: Dict) -> str:
        """Fallback template-based notification generation"""
        
        if trigger_type == 'calendar':
            event = context.get('event', {})
            minutes = context.get('minutes_until', 0)
            return f"Reminder: '{event.get('summary', 'Event')}' starts in {minutes} minutes."
        
        elif trigger_type == 'goal':
            goal = context.get('goal', {})
            days = context.get('days_stale', 0)
            return f"Your goal '{goal.get('title', 'Goal')}' hasn't been updated in {days} days. How's it going?"
        
        elif trigger_type == 'pattern':
            interests = context.get('interests', [])
            if interests:
                return f"Based on your interest in {interests[0]}, you might want to work on something related today."
            return "You're typically active at this time. Anything you'd like to work on?"
        
        elif trigger_type == 'learning':
            insight_count = context.get('insight_count', 0)
            return f"I've learned {insight_count} new things about your preferences. Want to see what I discovered?"
        
        return "Proactive notification from your AI assistant."
    
    def _generate_notification(self, rule: TriggerRule, trigger_type: str, context: Dict):
        """Generate and send a notification"""
        if self.notification_count >= self.config.notification_rate_limit:
            self.logger.debug("Rate limit reached, skipping notification")
            return
        
        try:
            # Generate notification content using LangChain agent
            notification_content = self._generate_notification_with_agent(trigger_type, context, rule.user_preference)
            
            if notification_content:
                # Send notification
                notification_id = self.notification_system.send_notification(
                    title="Proactive Assistant",
                    message=notification_content,
                    category=trigger_type,
                    actions=['View', 'Dismiss']
                )
                
                if notification_id:
                    # Record notification
                    from .cache_database import NotificationRecord
                    record = NotificationRecord(
                        id=notification_id,
                        trigger_rule_id=rule.id,
                        content=notification_content,
                        sent_at=datetime.now().isoformat()
                    )
                    self.cache_db.record_notification(record)
                    
                    # Update counters
                    self.notification_count += 1
                    self.performance_stats['notifications_sent'] += 1
                    
                    # Update rule trigger time
                    rule.last_triggered = datetime.now().isoformat()
                    self.cache_db.upsert_trigger_rule(rule)
                    
                    self.logger.info(f"Sent notification: {notification_content[:50]}...")
        
        except Exception as e:
            self.logger.error(f"Error generating notification: {e}")
    
    def _update_performance_stats(self, check_time: float):
        """Update performance statistics"""
        # Update average check time
        current_avg = self.performance_stats['avg_check_time']
        checks_count = self.performance_stats['checks_performed']
        
        if checks_count > 0:
            self.performance_stats['avg_check_time'] = (
                (current_avg * checks_count + check_time) / (checks_count + 1)
            )
        else:
            self.performance_stats['avg_check_time'] = check_time
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'running': self.running,
            'uptime_seconds': time.time() - (self.performance_stats.get('start_time', time.time())),
            'performance_stats': self.performance_stats.copy(),
            'notification_count_this_hour': self.notification_count,
            'rate_limit': self.config.notification_rate_limit,
            'cache_stats': self.cache_db.get_cache_stats()
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update scheduler configuration"""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated config: {key} = {value}")
    
    def force_check(self, rule_type: Optional[str] = None):
        """Force an immediate check (for testing/debugging)"""
        self.logger.info(f"Forcing immediate check for rule type: {rule_type or 'all'}")
        
        trigger_rules = self.cache_db.get_active_trigger_rules(rule_type)
        
        for rule in trigger_rules:
            try:
                self._check_trigger_rule(rule)
            except Exception as e:
                self.logger.error(f"Error in forced check for rule {rule.id}: {e}")

def main():
    """Main entry point for running scheduler as standalone service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Proactive AI Agent Background Scheduler')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--check-interval', type=int, default=900,
                       help='Check interval in seconds (default: 900)')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run as daemon process')
    
    args = parser.parse_args()
    
    # Load configuration
    config = SchedulerConfig(
        check_interval=args.check_interval,
        log_level=args.log_level
    )
    
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    # Initialize calendar manager for direct Google Calendar access
    calendar_manager = CalendarManager()
    
    # Create and start scheduler
    scheduler = BackgroundScheduler(config, calendar_manager=calendar_manager)
    
    try:
        scheduler.start()
        
        if args.daemon:
            # Run as daemon
            while scheduler.running:
                time.sleep(60)
        else:
            # Interactive mode
            print("Background scheduler started. Press Ctrl+C to stop.")
            while scheduler.running:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    break
    
    finally:
        scheduler.stop()

if __name__ == '__main__':
    main()

