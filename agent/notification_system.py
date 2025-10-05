"""
Cross-Platform Notification System
Handles OS-native notifications with rich features and user interaction tracking
"""

import os
import sys
import uuid
import subprocess
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path
import logging

@dataclass
class NotificationAction:
    """Represents a notification action button"""
    id: str
    title: str
    callback: Optional[Callable] = None

@dataclass
class NotificationConfig:
    """Configuration for notification system"""
    app_name: str = "Proactive AI Agent"
    app_icon: Optional[str] = None
    sound_enabled: bool = True
    persistent: bool = False
    max_notifications: int = 5
    auto_dismiss_seconds: int = 10

class NotificationSystem:
    """
    Cross-platform notification system with rich interaction support
    """
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.platform = self._detect_platform()
        self.active_notifications = {}
        self.notification_callbacks = {}
        self.response_handlers = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize platform-specific components
        self._init_platform_support()
    
    def _detect_platform(self) -> str:
        """Detect the current platform"""
        if sys.platform == "darwin":
            return "macos"
        elif sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("linux"):
            return "linux"
        else:
            return "unknown"
    
    def _init_platform_support(self):
        """Initialize platform-specific notification support"""
        if self.platform == "macos":
            self._init_macos_support()
        elif self.platform == "windows":
            self._init_windows_support()
        elif self.platform == "linux":
            self._init_linux_support()
        else:
            self.logger.warning(f"Unsupported platform: {self.platform}")
    
    def _init_macos_support(self):
        """Initialize macOS notification support"""
        try:
            # Check if we can use osascript
            result = subprocess.run(['which', 'osascript'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.macos_method = 'osascript'
                self.logger.info("Using osascript for macOS notifications")
            else:
                self.macos_method = 'fallback'
                self.logger.warning("osascript not available, using fallback")
        except Exception as e:
            self.logger.error(f"Error initializing macOS support: {e}")
            self.macos_method = 'fallback'
    
    def _init_windows_support(self):
        """Initialize Windows notification support"""
        try:
            # Try to import Windows toast notifications
            import win10toast
            self.windows_toaster = win10toast.ToastNotifier()
            self.windows_method = 'win10toast'
            self.logger.info("Using win10toast for Windows notifications")
        except ImportError:
            try:
                # Fallback to plyer
                import plyer
                self.windows_method = 'plyer'
                self.logger.info("Using plyer for Windows notifications")
            except ImportError:
                self.windows_method = 'fallback'
                self.logger.warning("No Windows notification library available")
    
    def _init_linux_support(self):
        """Initialize Linux notification support"""
        try:
            # Check if notify-send is available
            result = subprocess.run(['which', 'notify-send'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.linux_method = 'notify-send'
                self.logger.info("Using notify-send for Linux notifications")
            else:
                try:
                    import plyer
                    self.linux_method = 'plyer'
                    self.logger.info("Using plyer for Linux notifications")
                except ImportError:
                    self.linux_method = 'fallback'
                    self.logger.warning("No Linux notification method available")
        except Exception as e:
            self.logger.error(f"Error initializing Linux support: {e}")
            self.linux_method = 'fallback'
    
    def send_notification(self, 
                         title: str, 
                         message: str,
                         category: str = "general",
                         actions: Optional[List[str]] = None,
                         callback: Optional[Callable] = None,
                         priority: str = "normal") -> Optional[str]:
        """
        Send a cross-platform notification
        
        Args:
            title: Notification title
            message: Notification message
            category: Notification category for grouping
            actions: List of action button labels
            callback: Callback function for user interaction
            priority: Priority level (low, normal, high)
        
        Returns:
            Notification ID if successful, None otherwise
        """
        notification_id = str(uuid.uuid4())
        
        try:
            # Store callback if provided
            if callback:
                self.notification_callbacks[notification_id] = callback
            
            # Send platform-specific notification
            success = False
            
            if self.platform == "macos":
                success = self._send_macos_notification(
                    notification_id, title, message, category, actions, priority
                )
            elif self.platform == "windows":
                success = self._send_windows_notification(
                    notification_id, title, message, category, actions, priority
                )
            elif self.platform == "linux":
                success = self._send_linux_notification(
                    notification_id, title, message, category, actions, priority
                )
            else:
                success = self._send_fallback_notification(
                    notification_id, title, message, category, actions, priority
                )
            
            if success:
                # Track active notification
                self.active_notifications[notification_id] = {
                    'title': title,
                    'message': message,
                    'category': category,
                    'sent_at': datetime.now().isoformat(),
                    'priority': priority
                }
                
                # Set up auto-dismiss if configured
                if self.config.auto_dismiss_seconds > 0:
                    threading.Timer(
                        self.config.auto_dismiss_seconds,
                        self._auto_dismiss_notification,
                        args=[notification_id]
                    ).start()
                
                self.logger.info(f"Sent notification: {notification_id}")
                return notification_id
            else:
                self.logger.error(f"Failed to send notification: {title}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return None
    
    def _send_macos_notification(self, notification_id: str, title: str, message: str,
                                category: str, actions: Optional[List[str]], priority: str) -> bool:
        """Send macOS notification using osascript"""
        if self.macos_method == 'osascript':
            try:
                # Build osascript command
                script_parts = [
                    'display notification',
                    f'"{message}"',
                    f'with title "{title}"'
                ]
                
                if self.config.app_name:
                    script_parts.append(f'subtitle "{self.config.app_name}"')
                
                if self.config.sound_enabled:
                    script_parts.append('sound name "default"')
                
                script = ' '.join(script_parts)
                
                # Execute osascript
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                return result.returncode == 0
                
            except Exception as e:
                self.logger.error(f"Error with osascript: {e}")
                return False
        
        return self._send_fallback_notification(notification_id, title, message, category, actions, priority)
    
    def _send_windows_notification(self, notification_id: str, title: str, message: str,
                                  category: str, actions: Optional[List[str]], priority: str) -> bool:
        """Send Windows notification"""
        if self.windows_method == 'win10toast':
            try:
                # Use win10toast for rich Windows notifications
                self.windows_toaster.show_toast(
                    title=title,
                    msg=message,
                    icon_path=self.config.app_icon,
                    duration=self.config.auto_dismiss_seconds,
                    threaded=True,
                    callback_on_click=lambda: self._handle_notification_click(notification_id)
                )
                return True
                
            except Exception as e:
                self.logger.error(f"Error with win10toast: {e}")
                return False
        
        elif self.windows_method == 'plyer':
            try:
                import plyer
                plyer.notification.notify(
                    title=title,
                    message=message,
                    app_name=self.config.app_name,
                    timeout=self.config.auto_dismiss_seconds
                )
                return True
                
            except Exception as e:
                self.logger.error(f"Error with plyer: {e}")
                return False
        
        return self._send_fallback_notification(notification_id, title, message, category, actions, priority)
    
    def _send_linux_notification(self, notification_id: str, title: str, message: str,
                                category: str, actions: Optional[List[str]], priority: str) -> bool:
        """Send Linux notification using notify-send"""
        if self.linux_method == 'notify-send':
            try:
                cmd = ['notify-send']
                
                # Add urgency based on priority
                urgency_map = {'low': 'low', 'normal': 'normal', 'high': 'critical'}
                cmd.extend(['-u', urgency_map.get(priority, 'normal')])
                
                # Add category
                cmd.extend(['-c', category])
                
                # Add app name
                cmd.extend(['-a', self.config.app_name])
                
                # Add timeout
                if self.config.auto_dismiss_seconds > 0:
                    cmd.extend(['-t', str(self.config.auto_dismiss_seconds * 1000)])
                
                # Add icon if available
                if self.config.app_icon:
                    cmd.extend(['-i', self.config.app_icon])
                
                # Add actions if supported
                if actions:
                    for i, action in enumerate(actions):
                        cmd.extend(['-A', f"{i},{action}"])
                
                # Add title and message
                cmd.extend([title, message])
                
                # Execute notify-send
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return result.returncode == 0
                
            except Exception as e:
                self.logger.error(f"Error with notify-send: {e}")
                return False
        
        elif self.linux_method == 'plyer':
            try:
                import plyer
                plyer.notification.notify(
                    title=title,
                    message=message,
                    app_name=self.config.app_name,
                    timeout=self.config.auto_dismiss_seconds
                )
                return True
                
            except Exception as e:
                self.logger.error(f"Error with plyer: {e}")
                return False
        
        return self._send_fallback_notification(notification_id, title, message, category, actions, priority)
    
    def _send_fallback_notification(self, notification_id: str, title: str, message: str,
                                   category: str, actions: Optional[List[str]], priority: str) -> bool:
        """Fallback notification method (console output)"""
        try:
            print(f"\n{'='*50}")
            print(f"NOTIFICATION [{priority.upper()}]")
            print(f"Title: {title}")
            print(f"Message: {message}")
            print(f"Category: {category}")
            if actions:
                print(f"Actions: {', '.join(actions)}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}\n")
            
            # For fallback, simulate user interaction after a delay
            if actions:
                threading.Timer(
                    5.0,  # 5 second delay
                    self._simulate_fallback_interaction,
                    args=[notification_id, actions[0]]
                ).start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error with fallback notification: {e}")
            return False
    
    def _handle_notification_click(self, notification_id: str):
        """Handle notification click events"""
        self.logger.info(f"Notification clicked: {notification_id}")
        
        # Call registered callback
        callback = self.notification_callbacks.get(notification_id)
        if callback:
            try:
                callback(notification_id, 'clicked')
            except Exception as e:
                self.logger.error(f"Error in notification callback: {e}")
        
        # Record user response
        self._record_user_response(notification_id, 'clicked')
    
    def _handle_notification_action(self, notification_id: str, action: str):
        """Handle notification action button clicks"""
        self.logger.info(f"Notification action: {notification_id} -> {action}")
        
        # Call registered callback
        callback = self.notification_callbacks.get(notification_id)
        if callback:
            try:
                callback(notification_id, action)
            except Exception as e:
                self.logger.error(f"Error in notification action callback: {e}")
        
        # Record user response
        self._record_user_response(notification_id, action)
    
    def _simulate_fallback_interaction(self, notification_id: str, action: str):
        """Simulate user interaction for fallback notifications"""
        self.logger.debug(f"Simulating interaction: {notification_id} -> {action}")
        self._handle_notification_action(notification_id, action)
    
    def _auto_dismiss_notification(self, notification_id: str):
        """Auto-dismiss a notification after timeout"""
        if notification_id in self.active_notifications:
            self.logger.debug(f"Auto-dismissing notification: {notification_id}")
            self._record_user_response(notification_id, 'auto_dismissed')
            self.dismiss_notification(notification_id)
    
    def _record_user_response(self, notification_id: str, response: str):
        """Record user response for analytics"""
        if notification_id in self.active_notifications:
            notification = self.active_notifications[notification_id]
            sent_time = datetime.fromisoformat(notification['sent_at'])
            response_time = (datetime.now() - sent_time).total_seconds()
            
            # Store response data
            self.response_handlers[notification_id] = {
                'response': response,
                'response_time': response_time,
                'recorded_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Recorded response: {notification_id} -> {response} ({response_time:.1f}s)")
    
    def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss a specific notification"""
        try:
            if notification_id in self.active_notifications:
                del self.active_notifications[notification_id]
            
            if notification_id in self.notification_callbacks:
                del self.notification_callbacks[notification_id]
            
            self.logger.debug(f"Dismissed notification: {notification_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error dismissing notification: {e}")
            return False
    
    def dismiss_all_notifications(self):
        """Dismiss all active notifications"""
        notification_ids = list(self.active_notifications.keys())
        for notification_id in notification_ids:
            self.dismiss_notification(notification_id)
        
        self.logger.info("Dismissed all notifications")
    
    def get_active_notifications(self) -> Dict[str, Dict]:
        """Get all active notifications"""
        return self.active_notifications.copy()
    
    def get_notification_responses(self) -> Dict[str, Dict]:
        """Get all recorded notification responses"""
        return self.response_handlers.copy()
    
    def set_do_not_disturb(self, enabled: bool, until: Optional[datetime] = None):
        """Set do not disturb mode"""
        # This would integrate with system DND settings
        # For now, just log the request
        if enabled:
            until_str = until.isoformat() if until else "indefinitely"
            self.logger.info(f"Do not disturb enabled until: {until_str}")
        else:
            self.logger.info("Do not disturb disabled")
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update notification configuration"""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated notification config: {key} = {value}")
    
    def test_notification(self) -> bool:
        """Send a test notification to verify system is working"""
        return self.send_notification(
            title="Test Notification",
            message="This is a test notification from your Proactive AI Agent.",
            category="test",
            actions=["OK", "Dismiss"]
        ) is not None
    
    def get_platform_capabilities(self) -> Dict[str, bool]:
        """Get platform-specific notification capabilities"""
        capabilities = {
            'basic_notifications': True,
            'rich_notifications': False,
            'action_buttons': False,
            'custom_sounds': False,
            'persistent_notifications': False,
            'do_not_disturb_integration': False
        }
        
        if self.platform == "macos":
            capabilities.update({
                'rich_notifications': True,
                'custom_sounds': True,
                'do_not_disturb_integration': True
            })
        elif self.platform == "windows":
            capabilities.update({
                'rich_notifications': True,
                'action_buttons': True,
                'persistent_notifications': True
            })
        elif self.platform == "linux":
            capabilities.update({
                'action_buttons': True,
                'custom_sounds': True
            })
        
        return capabilities
    
    def cleanup(self):
        """Cleanup notification system resources"""
        self.dismiss_all_notifications()
        self.notification_callbacks.clear()
        self.response_handlers.clear()
        self.logger.info("Notification system cleaned up")

# Example usage and testing
def main():
    """Test the notification system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Notification System')
    parser.add_argument('--title', default='Test Notification', help='Notification title')
    parser.add_argument('--message', default='This is a test message', help='Notification message')
    parser.add_argument('--priority', choices=['low', 'normal', 'high'], default='normal')
    parser.add_argument('--actions', nargs='*', default=['OK', 'Cancel'], help='Action buttons')
    
    args = parser.parse_args()
    
    # Create notification system
    config = NotificationConfig(
        app_name="Proactive AI Agent Test",
        sound_enabled=True,
        auto_dismiss_seconds=10
    )
    
    notification_system = NotificationSystem(config)
    
    # Test platform capabilities
    capabilities = notification_system.get_platform_capabilities()
    print(f"Platform: {notification_system.platform}")
    print(f"Capabilities: {capabilities}")
    
    # Send test notification
    def test_callback(notification_id, action):
        print(f"Callback received: {notification_id} -> {action}")
    
    notification_id = notification_system.send_notification(
        title=args.title,
        message=args.message,
        category="test",
        actions=args.actions,
        callback=test_callback,
        priority=args.priority
    )
    
    if notification_id:
        print(f"Sent test notification: {notification_id}")
        
        # Wait for user interaction
        time.sleep(15)
        
        # Show responses
        responses = notification_system.get_notification_responses()
        print(f"Responses: {responses}")
    else:
        print("Failed to send test notification")
    
    # Cleanup
    notification_system.cleanup()

if __name__ == '__main__':
    main()

