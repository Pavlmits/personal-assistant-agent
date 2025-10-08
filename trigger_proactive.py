#!/usr/bin/env python3
"""
Trigger Proactive Notifications
Forces the background system to check for proactive opportunities immediately
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.memory import UserMemory
from agent.cache_database import CacheDatabase
from agent.notification_system import NotificationSystem
from rich.console import Console
from rich.panel import Panel

console = Console()

def setup_test_data():
    """Setup some test data to trigger notifications"""
    console.print("[blue]Setting up test data for proactive notifications...[/blue]")
    
    memory = UserMemory()
    
    # Add a test goal that's "stale" (simulate old goal)
    old_date = (datetime.now() - timedelta(days=4)).isoformat()
    
    # Clear existing goals first
    memory.clear_data('goals')
    
    # Add test goal
    memory.add_goal(
        title="Complete Thesis Literature Review",
        description="Review 20 research papers on proactive AI systems",
        target_date=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    )
    
    # Manually set the last_updated to 4 days ago to make it "stale"
    # This simulates a goal that hasn't been updated recently
    
    console.print("[green]✓ Added test goal: 'Complete Thesis Literature Review'[/green]")
    console.print("[dim]  (Simulated as 4 days old to trigger stale goal notification)[/dim]")
    
    # Add some user patterns
    profile = memory.get_user_profile()
    profile.update({
        'interests': ['thesis', 'research', 'AI', 'proactive systems'],
        'communication_style': 'helpful',
        'active_hours': {str(datetime.now().hour): 10}  # Current hour is very active
    })
    memory.update_user_profile(profile)
    
    console.print("[green]✓ Updated user profile with interests and patterns[/green]")
    
    return memory

def force_proactive_check():
    """Force an immediate proactive check"""
    console.print("[blue]Forcing immediate proactive check...[/blue]")
    
    try:
        # Initialize components (separate from background service)
        cache_db = CacheDatabase("test_cache.db")  # Use separate DB to avoid lock
        notification_system = NotificationSystem()
        
        # Setup test data
        memory = setup_test_data()
        
        # Sync data to cache
        goals = memory.get_goals()
        if goals:
            # Manually set one goal as stale
            goals[0]['last_updated'] = (datetime.now() - timedelta(days=4)).isoformat()
            cache_db.sync_goals_cache(goals)
            console.print(f"[green]✓ Synced {len(goals)} goals to cache[/green]")
        
        # Sync user patterns
        profile = memory.get_user_profile()
        cache_db.update_user_pattern('interests', profile.get('interests', []), 0.8)
        cache_db.update_user_pattern('active_hours', profile.get('active_hours', {}), 0.9)
        console.print("[green]✓ Synced user patterns to cache[/green]")
        
        # Check for stale goals
        stale_goals = cache_db.get_stale_goals(days_threshold=3)
        console.print(f"[yellow]Found {len(stale_goals)} stale goals[/yellow]")
        
        notifications_sent = 0
        
        # Generate notifications for stale goals
        for goal in stale_goals[:2]:  # Limit to 2 notifications
            console.print(f"[cyan]Generating notification for: {goal['title']}[/cyan]")
            
            # Use template-based notification for testing
            content = f"Your goal '{goal['title']}' hasn't been updated in {goal['days_since_update']} days. How's it going?"
            
            if content:
                notification_id = notification_system.send_notification(
                    title="🎯 Goal Reminder",
                    message=content,
                    category="goal",
                    actions=["Update Progress", "View Goal", "Dismiss"],
                    priority="normal"
                )
                
                if notification_id:
                    console.print(f"[green]✓ Sent goal notification: {content[:60]}...[/green]")
                    notifications_sent += 1
                    time.sleep(2)  # Brief pause between notifications
        
        # Check for pattern-based suggestions
        current_hour = str(datetime.now().hour)
        pattern = cache_db.get_user_pattern('active_hours')
        
        if pattern and pattern['data'].get(current_hour, 0) > 5:
            console.print("[cyan]Current time matches active pattern - generating suggestion[/cyan]")
            
            interests = cache_db.get_user_pattern('interests')
            # Use template-based notification for testing
            interest_list = interests['data'] if interests and isinstance(interests.get('data'), list) else []
            interest_text = interest_list[0] if interest_list else "your interests"
            content = f"You're typically active at this time. Based on your interest in {interest_text}, you might want to work on something related."
            
            if content:
                notification_id = notification_system.send_notification(
                    title="⏰ Productive Time",
                    message=content,
                    category="pattern",
                    actions=["Start Working", "Maybe Later", "Dismiss"],
                    priority="low"
                )
                
                if notification_id:
                    console.print(f"[green]✓ Sent pattern notification: {content[:60]}...[/green]")
                    notifications_sent += 1
        
        console.print(f"\n[bold green]✓ Proactive check complete! Sent {notifications_sent} notifications[/bold green]")
        
        if notifications_sent > 0:
            console.print("\n[yellow]📱 Check your macOS Notification Center to see the notifications![/yellow]")
            console.print("[dim]These are the same types of notifications the background service sends automatically.[/dim]")
        else:
            console.print("\n[yellow]No notifications triggered. This is normal if conditions aren't met.[/yellow]")
        
        # Cleanup
        notification_system.cleanup()
        cache_db.close()
        
        # Clean up test database
        if os.path.exists("test_cache.db"):
            os.remove("test_cache.db")
        
    except Exception as e:
        console.print(f"[red]Error during proactive check: {e}[/red]")

def show_background_service_info():
    """Show information about the background service"""
    console.print(Panel(
        "[bold blue]Background Service Information[/bold blue]\n\n"
        "[bold]Current Status:[/bold]\n"
        "• The background service is running (PID from service status)\n"
        "• It checks every 15 minutes for proactive opportunities\n"
        "• Database is locked (shows it's actively working)\n\n"
        "[bold]Notification Types:[/bold]\n"
        "• 📅 Calendar: 30-120 min before events\n"
        "• 🎯 Goals: Reminders for stale goals (3+ days)\n"
        "• ⏰ Patterns: Suggestions during productive hours\n"
        "• 🧠 Learning: Insights about your preferences\n\n"
        "[bold]How to See Notifications:[/bold]\n"
        "• macOS Notification Center (top-right corner)\n"
        "• Banner notifications at top of screen\n"
        "• System notification sound\n"
        "• Action buttons for interaction\n\n"
        "[bold]To Trigger More Notifications:[/bold]\n"
        "• Add calendar events (Google Calendar integration)\n"
        "• Create goals and don't update them for 3+ days\n"
        "• Use the agent during your active hours\n"
        "• Interact with sent notifications to improve learning",
        title="🔔 Proactive Notification System"
    ))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Trigger Proactive Notifications')
    parser.add_argument('--action', choices=['check', 'info'], default='check',
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'check':
        force_proactive_check()
    elif args.action == 'info':
        show_background_service_info()
