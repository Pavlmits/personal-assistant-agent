"""
LangChain Tools for Personal AI Agent
Provides tools for calendar, memory, goals, and system interactions
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .memory import UserMemory
from .clients.calendar_integration import CalendarManager
from .notification_system import NotificationSystem


class CalendarSearchInput(BaseModel):
    """Input for calendar search tool"""
    days_ahead: int = Field(default=7, description="Number of days ahead to search (default: 7)")
    limit: int = Field(default=10, description="Maximum number of events to return (default: 10)")


class CalendarCreateEventTool(BaseTool):
    """Tool to create new calendar events"""
    name: str = "create_calendar_event"
    description: str = """Create a new event in the user's Google Calendar. Use this to schedule meetings, appointments, or reminders. 
    Requires JSON input with: summary, start_time, end_time. Optional: description, location, attendees."""
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        object.__setattr__(self, 'calendar_manager', calendar_manager)
    
    def _run(self, tool_input: str) -> str:
        """Create a new calendar event"""
        try:
            # Parse the JSON input
            if isinstance(tool_input, str):
                params = json.loads(tool_input)
            elif isinstance(tool_input, dict):
                params = tool_input
            else:
                return f"Error: Invalid input type {type(tool_input)}"
            
            summary = params.get('summary', '')
            start_time = params.get('start_time', '')
            end_time = params.get('end_time', '')
            description = params.get('description', '')
            location = params.get('location', '')
            attendees = params.get('attendees')
            
            if not summary or not start_time or not end_time:
                return "Error: Required fields missing. Need: summary, start_time, end_time"
            
            # Parse datetime strings
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
            except ValueError as e:
                return f"Error parsing dates: {str(e)}. Please use ISO format: YYYY-MM-DDTHH:MM:SS"
            
            # Validate that end time is after start time
            if end_dt <= start_dt:
                return "Error: End time must be after start time"
            
            # Create the event
            result = self.calendar_manager.create_event(
                summary=summary,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                location=location,
                attendees=attendees
            )
            
            if result:
                # Simple, clear success message
                response = f"SUCCESS: Calendar event '{summary}' created for {start_dt.strftime('%Y-%m-%d at %H:%M')}."
                if result.get('htmlLink'):
                    response += f" Link: {result['htmlLink']}"
                return response
            else:
                return "FAILED: Could not create calendar event. Please check calendar permissions."
                
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Please provide valid JSON."
        except Exception as e:
            return f"Error creating calendar event: {str(e)}"


class CalendarSearchTool(BaseTool):
    """Tool to search upcoming calendar events. Call this with no arguments to get upcoming events."""
    name: str = "calendar_search"
    description: str = "Search for upcoming calendar events. Use this to check what meetings or appointments the user has coming up. No arguments needed - just call calendar_search"
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        object.__setattr__(self, 'calendar_manager', calendar_manager)
    
    def _run(self, query: str = "") -> str:
        """Search for upcoming calendar events"""
        try:
            # Ignore the query parameter, just get upcoming events
            events = self.calendar_manager.get_upcoming_events(limit=10)
            
            if not events:
                return "No upcoming events found in your calendar."
            
            # Filter events within the next 7 days
            from datetime import timezone
            cutoff_date = datetime.now(timezone.utc) + timedelta(days=7)
            filtered_events = []
            
            for event in events:
                event_start = event['start'].replace('Z', '+00:00')
                event_time = datetime.fromisoformat(event_start)
                # Make sure both datetimes are timezone-aware
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=timezone.utc)
                if event_time <= cutoff_date:
                    filtered_events.append(event)
            
            if not filtered_events:
                return "No events found in the next 7 days."
            
            # Format events
            result = f"Found {len(filtered_events)} upcoming events:\n\n"
            for event in filtered_events:
                start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                result += f"• {event['summary']}\n"
                result += f"  Time: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                if event.get('calendar_name'):
                    result += f"  Calendar: {event['calendar_name']}\n"
                if event.get('location'):
                    result += f"  Location: {event['location']}\n"
                result += "\n"
            
            return result.strip()
            
        except Exception as e:
            return f"Error accessing calendar: {str(e)}"


class CalendarDateSearchTool(BaseTool):
    """Tool to search calendar events on a specific date or date range"""
    name: str = "calendar_search_by_date"
    description: str = """Search for calendar events on a specific date or date range. 
    Provide JSON with 'date' (YYYY-MM-DD) or 'start_date' and 'end_date' (YYYY-MM-DD)."""
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        object.__setattr__(self, 'calendar_manager', calendar_manager)
    
    def _run(self, tool_input: str) -> str:
        """Search for events on a specific date or date range"""
        try:
            # Parse the JSON input
            if isinstance(tool_input, str):
                params = json.loads(tool_input)
            elif isinstance(tool_input, dict):
                params = tool_input
            else:
                return f"Error: Invalid input type {type(tool_input)}"
            
            # Check if single date or date range
            if 'date' in params:
                # Single date query
                date_str = params['date']
                try:
                    target_date = datetime.fromisoformat(date_str)
                except ValueError:
                    return f"Error: Invalid date format '{date_str}'. Use YYYY-MM-DD"
                
                # Use get_events_for_date if available, otherwise use get_upcoming_events with filtering
                if hasattr(self.calendar_manager, 'get_events_for_date'):
                    raw_events = self.calendar_manager.get_events_for_date(target_date)
                else:
                    # Fallback: get all upcoming events and filter
                    raw_events = self.calendar_manager.get_upcoming_events(limit=50, days_ahead=365)
                
                # Strict filtering to ensure events are actually on the target date
                events = []
                for event in raw_events:
                    event_start = event['start'].replace('Z', '+00:00')
                    if 'T' in event_start:
                        # Timed event
                        event_time = datetime.fromisoformat(event_start)
                        if event_time.date() == target_date.date():
                            events.append(event)
                    else:
                        # All-day event (format: YYYY-MM-DD)
                        event_date = datetime.fromisoformat(event_start).date()
                        if event_date == target_date.date():
                            events.append(event)
                
                if not events:
                    return f"No events found on {target_date.strftime('%Y-%m-%d')}."
                
                result = f"Found {len(events)} event(s) on {target_date.strftime('%Y-%m-%d')}:\n\n"
                
            elif 'start_date' in params and 'end_date' in params:
                # Date range query
                start_str = params['start_date']
                end_str = params['end_date']
                
                try:
                    start_date = datetime.fromisoformat(start_str)
                    end_date = datetime.fromisoformat(end_str)
                except ValueError as e:
                    return f"Error: Invalid date format. Use YYYY-MM-DD. {str(e)}"
                
                if end_date < start_date:
                    return "Error: end_date must be after start_date"
                
                # Calculate days between
                days_diff = (end_date - start_date).days + 1
                
                # Get events in range
                raw_events = self.calendar_manager.get_upcoming_events(limit=100, days_ahead=days_diff + 30)
                events = []
                
                # Strict filtering for date range
                for event in raw_events:
                    event_start = event['start'].replace('Z', '+00:00')
                    if 'T' in event_start:
                        # Timed event
                        event_time = datetime.fromisoformat(event_start)
                        if start_date.date() <= event_time.date() <= end_date.date():
                            events.append(event)
                    else:
                        # All-day event
                        event_date = datetime.fromisoformat(event_start).date()
                        if start_date.date() <= event_date <= end_date.date():
                            events.append(event)
                
                if not events:
                    return f"No events found between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}."
                
                result = f"Found {len(events)} event(s) between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}:\n\n"
            else:
                return "Error: Provide either 'date' for single date or 'start_date' and 'end_date' for a range"
            
            # Format events
            for event in events:
                event_start = event['start'].replace('Z', '+00:00')
                
                # Parse the start time
                if 'T' in event_start:
                    start_time = datetime.fromisoformat(event_start)
                else:
                    # All-day event - treat as date only
                    start_time = datetime.fromisoformat(event_start + 'T00:00:00')
                
                result += f"• {event['summary']}\n"
                result += f"  Time: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                if event.get('calendar_name'):
                    result += f"  Calendar: {event['calendar_name']}\n"
                if event.get('location'):
                    result += f"  Location: {event['location']}\n"
                if event.get('description'):
                    desc = event['description'][:100]
                    if len(event['description']) > 100:
                        desc += "..."
                    result += f"  Description: {desc}\n"
                result += "\n"
            
            return result.strip()
            
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Please provide valid JSON."
        except Exception as e:
            return f"Error searching calendar: {str(e)}"


class MemorySearchInput(BaseModel):
    """Input for memory search tool"""
    query: str = Field(description="What to search for in conversation history")
    limit: int = Field(default=5, description="Maximum number of results to return")


class MemorySearchTool(BaseTool):
    """Tool to search conversation history and user insights"""
    name: str = "memory_search"
    description: str = """Search through conversation history and user insights from PAST conversations. 
    Use this to find context from previous interactions, not for information the user just mentioned in their current message. 
    If user is providing new information about tasks or goals, offer to create goals/reminders instead of searching memory."""
    args_schema: type = MemorySearchInput
    
    def __init__(self, memory: UserMemory):
        super().__init__()
        object.__setattr__(self, 'memory', memory)
    
    def _run(self, query: str, limit: int = 5) -> str:
        """Search memory for relevant information"""
        try:
            # Search recent messages
            recent_messages = self.memory.get_recent_messages(limit * 2)
            relevant_messages = []
            
            query_lower = query.lower()
            for msg in recent_messages:
                if query_lower in msg['content'].lower():
                    relevant_messages.append(msg)
            
            # Get user insights
            insights = self.memory.get_recent_insights()
            relevant_insights = [insight for insight in insights if query_lower in insight.lower()]
            
            result = ""
            
            if relevant_messages:
                result += f"Found {len(relevant_messages)} relevant conversations:\n\n"
                for msg in relevant_messages[:limit]:
                    timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%Y-%m-%d %H:%M')
                    result += f"[{timestamp}] {msg['sender']}: {msg['content']}\n"
                result += "\n"
            
            if relevant_insights:
                result += f"Relevant insights about the user:\n"
                for insight in relevant_insights[:3]:
                    result += f"• {insight}\n"
            
            if not result:
                result = f"No relevant information found for '{query}' in conversation history."
            
            return result.strip()
            
        except Exception as e:
            return f"Error searching memory: {str(e)}"


class UserProfileTool(BaseTool):
    """Tool to get user profile and preferences"""
    name: str = "get_user_profile"
    description: str = "Get the user's profile including preferences, interests, communication style, and learned patterns."
    
    def __init__(self, memory: UserMemory):
        super().__init__()
        object.__setattr__(self, 'memory', memory)
    
    def _run(self, query: str = "") -> str:
        """Get user profile information"""
        try:
            profile = self.memory.get_user_profile()
            
            result = "User Profile:\n\n"
            
            # Communication style
            style = profile.get('communication_style', 'Unknown')
            result += f"Communication Style: {style}\n"
            
            # Interests
            interests = profile.get('interests', [])
            if interests:
                result += f"Interests: {', '.join(interests)}\n"
            
            # Active hours
            active_hours = profile.get('active_hours', {})
            if active_hours:
                most_active = max(active_hours.items(), key=lambda x: x[1])
                result += f"Most Active Hour: {most_active[0]}:00\n"
            
            # Interaction stats
            total_interactions = profile.get('total_interactions', 0)
            result += f"Total Interactions: {total_interactions}\n"
            
            last_interaction = profile.get('last_interaction')
            if last_interaction:
                last_time = datetime.fromisoformat(last_interaction).strftime('%Y-%m-%d %H:%M')
                result += f"Last Interaction: {last_time}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"Error getting user profile: {str(e)}"


class GoalsInput(BaseModel):
    """Input for goals management"""
    action: str = Field(description="Action to perform: 'list', 'add', 'update', or 'complete'")
    title: Optional[str] = Field(default=None, description="Goal title (for add/update)")
    description: Optional[str] = Field(default=None, description="Goal description")
    progress: Optional[int] = Field(default=None, description="Progress percentage (0-100)")


class GoalsManagementTool(BaseTool):
    """Tool to manage user goals"""
    name: str = "manage_goals"
    description: str = """Manage user goals and tasks - list current goals, add new ones, update progress, or mark as complete. 
    Use this tool when the user mentions NEW tasks or to-dos they need to accomplish (e.g., 'I need to...', 'I should...', 'I might need to...'). 
    Offer to add these as goals to help them track progress."""
    args_schema: type = GoalsInput
    
    def __init__(self, memory: UserMemory):
        super().__init__()
        object.__setattr__(self, 'memory', memory)
    
    def _run(self, action: str = None, title: Optional[str] = None, description: Optional[str] = None, 
             progress: Optional[int] = None) -> str:
        """Manage user goals"""
        try:
            # Handle potential JSON string input (for ReAct agents)
            if isinstance(action, str) and action.startswith('{'):
                try:
                    params = json.loads(action)
                    action = params.get('action')
                    title = params.get('title', params.get('goal'))  # Support both 'title' and 'goal'
                    description = params.get('description')
                    progress = params.get('progress')
                except json.JSONDecodeError:
                    pass  # Continue with original action value
            
            if not action:
                return "Error: 'action' parameter is required. Available actions: list, add, update"
            
            if action == "list":
                goals = self.memory.get_goals()
                if not goals:
                    return "No goals found. The user hasn't set any goals yet."
                
                result = f"Current Goals ({len(goals)}):\n\n"
                for i, goal in enumerate(goals, 1):
                    result += f"{i}. {goal['title']}\n"
                    if goal.get('description'):
                        result += f"   Description: {goal['description']}\n"
                    result += f"   Progress: {goal.get('progress', 0)}%\n"
                    if goal.get('target_date'):
                        result += f"   Target Date: {goal['target_date']}\n"
                    result += "\n"
                
                return result.strip()
            
            elif action == "add":
                if not title:
                    return "Error: Goal title is required to add a new goal."
                
                self.memory.add_goal(title, description or "", "")
                return f"Successfully added new goal: '{title}'"
            
            elif action == "update":
                if not title:
                    return "Error: Goal title is required to update a goal."
                
                goals = self.memory.get_goals()
                goal_found = False
                
                for goal in goals:
                    if goal['title'].lower() == title.lower():
                        if progress is not None:
                            # Update progress in database
                            self.memory.update_goal_progress(goal['id'], progress)
                            goal_found = True
                            return f"Updated progress for '{title}' to {progress}%"
                
                if not goal_found:
                    return f"Goal '{title}' not found. Use 'list' action to see current goals."
            
            else:
                return f"Unknown action '{action}'. Available actions: list, add, update"
                
        except Exception as e:
            return f"Error managing goals: {str(e)}"


class NotificationInput(BaseModel):
    """Input for sending notifications"""
    title: str = Field(description="Notification title")
    message: str = Field(description="Notification message")
    priority: str = Field(default="normal", description="Priority: low, normal, high")


class NotificationTool(BaseTool):
    """Tool to send notifications to the user"""
    name: str = "send_notification"
    description: str = """Send a notification to the user. Use this for important reminders or proactive suggestions.
    Requires JSON with: 'title' (short heading), 'message' (notification text), 'priority' (optional: low/normal/high).
    Example: {"title": "Reminder", "message": "Meeting at 3pm", "priority": "normal"}"""
    args_schema: type = NotificationInput
    
    def __init__(self, notification_system: NotificationSystem):
        super().__init__()
        object.__setattr__(self, 'notification_system', notification_system)
    
    def _run(self, title: str, message: str, priority: str = "normal") -> str:
        """Send a notification"""
        try:
            notification_id = self.notification_system.send_notification(
                title=title,
                message=message,
                priority=priority
            )
            
            if notification_id:
                return f"Notification sent successfully (ID: {notification_id})"
            else:
                return "Failed to send notification"
                
        except Exception as e:
            return f"Error sending notification: {str(e)}"


class TimeInfoTool(BaseTool):
    """Tool to get current time and date information"""
    name: str = "get_time_info"
    description: str = "Get current date, time, and day of week. Use this when you need to know what time it is."
    
    def _run(self, query: str = "") -> str:
        """Get current time information"""
        now = datetime.now()
        
        result = f"Current Time Information:\n"
        result += f"Date: {now.strftime('%Y-%m-%d')}\n"
        result += f"Time: {now.strftime('%H:%M:%S')}\n"
        result += f"Day: {now.strftime('%A')}\n"
        result += f"Week: Week {now.isocalendar()[1]} of {now.year}\n"
        
        return result


def create_agent_tools(memory: UserMemory, calendar_manager: CalendarManager, 
                      notification_system: NotificationSystem) -> List[BaseTool]:
    """Create all tools for the agent"""
    
    tools = [
        CalendarSearchTool(calendar_manager),
        CalendarDateSearchTool(calendar_manager),
        CalendarCreateEventTool(calendar_manager),
        MemorySearchTool(memory),
        UserProfileTool(memory),
        GoalsManagementTool(memory),
        NotificationTool(notification_system),
        TimeInfoTool(),
    ]
    
    return tools
