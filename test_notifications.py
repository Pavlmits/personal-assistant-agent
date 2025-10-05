#!/usr/bin/env python3
"""
Test Notification System
Demonstrates different types of proactive notifications
"""

import time
import sys
import os
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.notification_system import NotificationSystem, NotificationConfig
from agent.ai_service_client import AIServiceClient
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_notification_types():
    """Test different types of notifications"""
    
    console.print(Panel(
        "[bold blue]Testing Proactive Notification System[/bold blue]\n"
        "This will send several test notifications to demonstrate the system.\n"
        "[yellow]Look for notifications in your macOS Notification Center![/yellow]",
        title="🔔 Notification Test"
    ))
    
    # Initialize notification system
    config = NotificationConfig(
        app_name="Proactive AI Agent",
        sound_enabled=True,
        auto_dismiss_seconds=0,  # Don't auto-dismiss for testing
        persistent=True
    )
    
    notification_system = NotificationSystem(config)
    ai_service = AIServiceClient()
    
    # Test different notification scenarios
    test_scenarios = [
        {
            "title": "Calendar Reminder",
            "trigger_type": "calendar",
            "context": {
                "event": {"summary": "Thesis Meeting with Dr. Smith", "attendee_count": 2},
                "minutes_until": 45
            },
            "delay": 2
        },
        {
            "title": "Goal Reminder", 
            "trigger_type": "goal",
            "context": {
                "goal": {"title": "Complete Literature Review", "progress": 60},
                "days_stale": 4
            },
            "delay": 4
        },
        {
            "title": "Productive Time",
            "trigger_type": "pattern", 
            "context": {
                "activity_level": 8,
                "interests": ["research", "writing", "thesis"]
            },
            "delay": 6
        },
        {
            "title": "Learning Insights",
            "trigger_type": "learning",
            "context": {
                "insight_count": 5,
                "confidence": 0.85
            },
            "delay": 8
        }
    ]
    
    console.print(f"\n[green]Sending {len(test_scenarios)} test notifications...[/green]")
    console.print("[dim]Check your macOS Notification Center (top-right corner)[/dim]\n")
    
    for i, scenario in enumerate(test_scenarios, 1):
        console.print(f"[blue]{i}. {scenario['title']}[/blue]")
        
        # Generate AI content for the notification
        content = ai_service.generate_notification_content(
            trigger_type=scenario["trigger_type"],
            context=scenario["context"],
            user_preference="medium",
            priority="normal"
        )
        
        if not content:
            content = f"Test notification for {scenario['title']}"
        
        console.print(f"   Content: [dim]{content}[/dim]")
        
        # Send notification
        notification_id = notification_system.send_notification(
            title=f"Proactive AI Agent - {scenario['title']}",
            message=content,
            category=scenario["trigger_type"],
            actions=["View Details", "Dismiss", "Snooze"],
            priority="normal"
        )
        
        if notification_id:
            console.print(f"   [green]✓ Sent notification: {notification_id[:8]}...[/green]")
        else:
            console.print(f"   [red]✗ Failed to send notification[/red]")
        
        # Wait before next notification
        console.print(f"   [dim]Waiting {scenario['delay']} seconds...[/dim]\n")
        time.sleep(scenario['delay'])
    
    console.print("[green]All test notifications sent![/green]")
    console.print("\n[yellow]💡 Tips:[/yellow]")
    console.print("• Check macOS Notification Center (click clock in menu bar)")
    console.print("• Notifications may appear as banners at the top of your screen")
    console.print("• Click notifications to see action buttons")
    console.print("• The background service will send similar notifications automatically")
    
    # Show active notifications
    active = notification_system.get_active_notifications()
    if active:
        console.print(f"\n[cyan]Active Notifications: {len(active)}[/cyan]")
        for nid, notification in active.items():
            console.print(f"  • {notification['title'][:50]}...")
    
    # Cleanup
    ai_service.cleanup()
    notification_system.cleanup()

def test_immediate_notification():
    """Send one immediate test notification"""
    console.print("[blue]Sending immediate test notification...[/blue]")
    
    notification_system = NotificationSystem()
    
    notification_id = notification_system.send_notification(
        title="🤖 Proactive AI Agent Test",
        message="This is a test notification! If you see this, the system is working perfectly. 🎉",
        category="test",
        actions=["Great!", "Dismiss"],
        priority="high"
    )
    
    if notification_id:
        console.print(f"[green]✓ Test notification sent successfully![/green]")
        console.print(f"[dim]Notification ID: {notification_id}[/dim]")
        console.print("\n[yellow]Look for the notification in your macOS Notification Center![/yellow]")
        return True
    else:
        console.print("[red]✗ Failed to send test notification[/red]")
        return False

def show_notification_capabilities():
    """Show what notification capabilities are available"""
    notification_system = NotificationSystem()
    capabilities = notification_system.get_platform_capabilities()
    
    console.print(Panel(
        f"[bold]Platform:[/bold] {notification_system.platform}\n" +
        "\n".join([f"[bold]{key.replace('_', ' ').title()}:[/bold] {'✅ Yes' if value else '❌ No'}" 
                  for key, value in capabilities.items()]),
        title="🔧 Notification Capabilities"
    ))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Proactive Notifications')
    parser.add_argument('--type', choices=['immediate', 'scenarios', 'capabilities'], 
                       default='immediate', help='Type of test to run')
    
    args = parser.parse_args()
    
    if args.type == 'immediate':
        test_immediate_notification()
    elif args.type == 'scenarios':
        test_notification_types()
    elif args.type == 'capabilities':
        show_notification_capabilities()
