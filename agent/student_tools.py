"""
Student-Specific Tools for Junior High School Assistant
Provides specialized tools for study planning, mood tracking, and academic workflow
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, model_validator

from .memory import UserMemory
from .clients.calendar_integration import CalendarManager
from .notification_system import NotificationSystem


class StudyPlannerInput(BaseModel):
    """Input for study planner tool"""
    course_name: str = Field(default="", description="Course/Subject name (must match enrolled courses like 'Math', 'Physics', 'Greek')")
    assignment_title: str = Field(default="Assignment", description="Assignment title (e.g., 'Chapter 5 homework', 'Test preparation')")
    due_date: str = Field(default="", description="Due date in YYYY-MM-DD format (e.g., 2025-10-31). You must calculate the actual date from phrases like 'next Friday' before calling this tool.")
    estimated_hours: float = Field(default=2.0, description="Estimated hours needed")
    difficulty: str = Field(default="medium", description="Difficulty: easy, medium, hard")

    @model_validator(mode='before')
    @classmethod
    def parse_malformed_json(cls, data):
        """Handle case where LangChain stuffs all JSON into one field"""
        # Check both 'assignment' (old field) and 'course_name' (new field)
        for field_name in ['assignment', 'course_name', 'assignment_title']:
            if isinstance(data, dict) and field_name in data:
                field_val = data.get(field_name, '')
                # Check if field contains JSON string
                if isinstance(field_val, str) and field_val.strip().startswith('{'):
                    try:
                        # Parse the nested JSON
                        parsed = json.loads(field_val)
                        # Return the parsed object with new field names
                        return {
                            'course_name': parsed.get('course_name', parsed.get('assignment', field_val)),
                            'assignment_title': parsed.get('assignment_title', parsed.get('title', 'Assignment')),
                            'due_date': parsed.get('due_date', data.get('due_date', '')),
                            'estimated_hours': parsed.get('estimated_hours', data.get('estimated_hours', 2.0)),
                            'difficulty': parsed.get('difficulty', data.get('difficulty', 'medium'))
                        }
                    except (json.JSONDecodeError, KeyError):
                        pass  # Keep original data

        # Handle old format (assignment field) -> convert to new format
        if isinstance(data, dict) and 'assignment' in data and 'course_name' not in data:
            assignment_str = data.get('assignment', '')
            # Try to extract course name from assignment string
            course_name = assignment_str.split()[0] if assignment_str else ''
            return {
                'course_name': course_name,
                'assignment_title': assignment_str,
                'due_date': data.get('due_date', ''),
                'estimated_hours': data.get('estimated_hours', 2.0),
                'difficulty': data.get('difficulty', 'medium')
            }

        return data


class StudyPlannerTool(BaseTool):
    """Tool to break down assignments into study sessions"""
    name: str = "create_study_plan"
    description: str = """Create a study plan for an assignment in one of the student's enrolled courses.

    ⚠️ CRITICAL: DO NOT CALL THIS TOOL unless the user has provided ALL of these details:
    - Specific course/subject name (e.g., "Math", "Physics")
    - Specific assignment title (e.g., "Chapter 5 test", "Homework worksheet")
    - Due date or deadline (e.g., "Friday", "next week", "November 5th")

    If ANY of these are missing, ASK THE USER for clarification. DO NOT invent or guess information.

    IMPORTANT RULES:
    1. course_name MUST be a course the student is enrolled in (e.g., "Math", "Physics", "Greek")
    2. You must calculate dates BEFORE calling (use YYYY-MM-DD format)
    3. System prevents duplicate assignments for the same course
    4. NEVER invent assignment details - all information must come from the user

    Required inputs (use exact JSON format):
    {
        "course_name": "Math",
        "assignment_title": "Chapter 5 homework",
        "due_date": "2025-10-31",
        "estimated_hours": 2.0,
        "difficulty": "medium"
    }

    Example: {"course_name": "Math", "assignment_title": "Test preparation", "due_date": "2025-10-31", "estimated_hours": 2.0, "difficulty": "medium"}

    Returns: Study plan with daily breakdown. Assignment is saved to database and linked to the course."""
    args_schema: type = StudyPlannerInput
    
    def __init__(self, memory: UserMemory, calendar_manager: CalendarManager):
        super().__init__()
        object.__setattr__(self, 'memory', memory)
        object.__setattr__(self, 'calendar_manager', calendar_manager)

    def _run(self, course_name: str = "", assignment_title: str = "Assignment", due_date: str = "",
             estimated_hours: float = 2.0, difficulty: str = "medium") -> str:
        """Create a study plan for an assignment"""
        try:
            # 0. Validate required inputs
            if not course_name or course_name.strip() == "":
                return "❌ Error: course_name is required. Please specify which course this assignment is for."

            if not assignment_title or assignment_title.strip() in ["", "Assignment"]:
                return "❌ Error: assignment_title is required. Please provide a specific assignment title."

            # 1. Find and validate course
            courses = self.memory.get_courses()
            if not courses:
                return "❌ No courses found! Please set up your schedule first in the student setup."

            # Find course (case-insensitive match)
            course = None
            course_name_lower = course_name.lower().strip()
            for c in courses:
                if c['course_name'].lower().strip() == course_name_lower:
                    course = c
                    break

            if not course:
                available_courses = ", ".join([c['course_name'] for c in courses])
                return f"❌ Course '{course_name}' not found!\n\nYour enrolled courses: {available_courses}\n\nPlease use one of these course names."

            # 2. Check for duplicate assignment
            if self.memory.assignment_exists(course['course_id'], assignment_title):
                return f"⚠️ Assignment '{assignment_title}' already exists for {course['course_name']}!\n\nUse a different title or check existing assignments."

            # 3. Parse due date
            if not due_date or due_date.strip() == "":
                due_dt = datetime.now() + timedelta(days=7)
            else:
                try:
                    due_dt = datetime.fromisoformat(due_date)
                except ValueError:
                    return f"❌ Invalid date format: '{due_date}'. Please use YYYY-MM-DD format (e.g., 2025-10-31)."

            now = datetime.now()
            days_available = (due_dt.date() - now.date()).days

            if days_available <= 0:
                return f"⚠️ Assignment '{assignment_title}' for {course['course_name']} is due today or overdue! Consider immediate action."
            
            # Calculate session distribution based on difficulty and time available
            if difficulty == "easy":
                session_length = 25  # minutes
                buffer_days = 1
            elif difficulty == "hard":
                session_length = 45
                buffer_days = 2
            else:  # medium
                session_length = 30
                buffer_days = 1
            
            # Calculate number of sessions needed
            total_minutes = estimated_hours * 60
            sessions_needed = max(1, int(total_minutes / session_length))
            
            # Distribute sessions across available days (leaving buffer)
            study_days = max(1, days_available - buffer_days)
            sessions_per_day = max(1, sessions_needed // study_days)
            
            # Get user's preferred study times from profile
            profile = self.memory.get_user_profile()
            preferred_times = profile.get('study_times', ['16:00', '19:00'])  # Default after school times
            
            # Create study plan
            plan = f"📚 Study Plan for '{assignment}'\n\n"
            plan += f"📅 Due: {due_dt.strftime('%A, %B %d')}\n"
            plan += f"⏱️ Total time needed: {estimated_hours} hours\n"
            plan += f"📊 Difficulty: {difficulty.title()}\n"
            plan += f"🎯 Sessions: {sessions_needed} × {session_length} minutes\n\n"
            
            # Generate daily breakdown
            plan += "📋 Daily Breakdown:\n"
            current_date = now.date()
            sessions_scheduled = 0
            
            for day in range(study_days):
                study_date = current_date + timedelta(days=day + 1)
                sessions_today = min(sessions_per_day, sessions_needed - sessions_scheduled)
                
                if sessions_today > 0:
                    plan += f"\n📆 {study_date.strftime('%A, %b %d')}:\n"
                    
                    for session in range(sessions_today):
                        time_slot = preferred_times[session % len(preferred_times)]
                        plan += f"  • {time_slot} - {session_length}min study session\n"
                        sessions_scheduled += 1
            
            # Add explanation
            plan += f"\n💡 Why this plan works:\n"
            if days_available > 3:
                plan += f"• Spread across {study_days} days to avoid cramming\n"
            else:
                plan += f"• Concentrated schedule due to tight deadline\n"
            
            plan += f"• {session_length}-minute sessions match {difficulty} difficulty\n"
            plan += f"• {buffer_days}-day buffer before due date for review\n"
            
            # 4. Save assignment to database
            assignment_id = self.memory.add_assignment(
                course_id=course['course_id'],
                title=assignment_title,
                due_date=due_date,
                description=f"Study plan created with {sessions_needed} sessions",
                priority=difficulty,
                estimated_hours=estimated_hours
            )

            if assignment_id:
                # Also create a goal for tracking
                goal_title = f"{course['course_name']}: {assignment_title}"
                self.memory.add_goal(goal_title, f"Complete by {due_date}", due_date)

                plan += f"\n✅ Assignment saved! Course: {course['course_name']}\n"
            else:
                plan += f"\n⚠️ Note: Could not save assignment to database.\n"

            return plan

        except Exception as e:
            return f"❌ Error creating study plan: {str(e)}"


class MoodTrackingInput(BaseModel):
    """Input for mood tracking"""
    mood: str = Field(default="", description="Mood emoji or rating: 😊, 😐, 🙁 or 1-5")
    energy: Optional[str] = Field(default=None, description="Energy level: low, medium, high")
    difficulty: Optional[str] = Field(default=None, description="Task difficulty feedback: too_easy, just_right, too_hard")
    notes: Optional[str] = Field(default=None, description="Optional notes about current state")

    @model_validator(mode='before')
    @classmethod
    def parse_malformed_json(cls, data):
        """Handle case where LangChain stuffs all JSON into one field"""
        if isinstance(data, dict):
            # Check if entire JSON is stuffed into mood field
            if 'mood' in data and isinstance(data['mood'], str) and data['mood'].strip().startswith('{'):
                try:
                    parsed = json.loads(data['mood'])
                    if isinstance(parsed, dict):
                        return parsed
                except:
                    pass
        return data


class MoodTrackingTool(BaseTool):
    """Tool for quick mood and energy check-ins"""
    name: str = "mood_checkin"
    description: str = """RECORD a mood check-in to the database. This is THE ONLY WAY to save mood data.

    ⚠️ CRITICAL - TWO-STEP PROCESS:
    Step 1: If user says "I want to do a mood check-in" but hasn't given their mood:
      - DO NOT call this tool yet
      - Ask: "How are you feeling? Rate 1-5 or use 😊😐🙁"

    Step 2: When user provides their mood (e.g., "3", "😊", "feeling good - 4"):
      - MUST call this tool with their mood: {"mood": "3"}
      - If they mention energy, include it: {"mood": "3", "energy": "medium"}
      - This saves to database and returns confirmation

    IMPORTANT: If you don't call this tool, mood is NOT saved!

    Returns: Confirmation message with mood summary."""
    args_schema: type = MoodTrackingInput
    
    def __init__(self, memory: UserMemory):
        super().__init__()
        object.__setattr__(self, 'memory', memory)
    
    def _run(self, mood: str = "", energy: Optional[str] = None,
             difficulty: Optional[str] = None, notes: Optional[str] = None) -> str:
        """Record mood and energy check-in"""
        try:
            # Check if mood was provided
            if not mood or mood.strip() == "":
                return "⚠️ Cannot record mood check-in without mood data. Please ask the user: 'How are you feeling right now? You can use emojis (😊😐🙁) or rate 1-5!'"

            # Convert emoji to numeric if needed
            mood_map = {"😊": 5, "🙂": 4, "😐": 3, "🙁": 2, "😢": 1}
            if mood in mood_map:
                mood_score = mood_map[mood]
                mood_display = f"{mood} ({mood_score}/5)"
            else:
                try:
                    mood_score = int(mood)
                    if 1 <= mood_score <= 5:
                        emoji_map = {1: "😢", 2: "🙁", 3: "😐", 4: "🙂", 5: "😊"}
                        mood_display = f"{emoji_map[mood_score]} ({mood_score}/5)"
                    else:
                        return "Error: Mood rating must be 1-5 or use emojis 😊😐🙁"
                except ValueError:
                    return "Error: Invalid mood format. Use emojis (😊😐🙁) or numbers (1-5)"
            
            # Record the check-in
            timestamp = datetime.now().isoformat()
            checkin_data = {
                "timestamp": timestamp,
                "mood": mood_score,
                "energy": energy,
                "difficulty": difficulty,
                "notes": notes
            }
            
            # Store in memory as insight
            insight = f"Mood check-in: {mood_display}"
            if energy:
                insight += f", Energy: {energy}"
            if difficulty:
                insight += f", Task difficulty: {difficulty}"
            if notes:
                insight += f" - {notes}"
            
            self.memory.add_simple_insight(insight)
            
            # Generate response with suggestions
            response = f"✅ SUCCESS: Mood check-in recorded and saved to database!\n\n"
            response += f"📊 Mood: {mood_display}\n"
            if energy:
                response += f"⚡ Energy: {energy.title()}\n"
            if difficulty:
                response += f"📊 Task difficulty: {difficulty.replace('_', ' ').title()}\n"
            response += f"\n✓ Data saved successfully. You can now respond to the user."
            
            # Provide contextual suggestions
            if mood_score <= 2:
                response += f"\n💙 Feeling down? Consider:\n"
                response += f"• Taking a 10-minute break\n"
                response += f"• Switching to an easier task\n"
                response += f"• Talking to someone you trust\n"
            elif energy == "low":
                response += f"\n🔋 Low energy suggestions:\n"
                response += f"• Try a 5-minute walk or stretch\n"
                response += f"• Have a healthy snack\n"
                response += f"• Switch to lighter review tasks\n"
            elif difficulty == "too_hard":
                response += f"\n🎯 Task too challenging? Try:\n"
                response += f"• Breaking it into smaller steps\n"
                response += f"• Asking for help\n"
                response += f"• Reviewing prerequisite material\n"
            elif difficulty == "too_easy":
                response += f"\n🚀 Ready for more challenge:\n"
                response += f"• Try advanced practice problems\n"
                response += f"• Set a faster completion goal\n"
                response += f"• Help a classmate with this topic\n"
            
            return response
            
        except Exception as e:
            return f"Error recording mood check-in: {str(e)}"


class ViewMoodHistoryTool(BaseTool):
    """Tool to view mood check-in history"""
    name: str = "view_mood_history"
    description: str = """VIEW past mood check-ins from the database.

    Use this when the student asks:
    - "How was my mood last time?"
    - "Show me my mood history"
    - "What were my recent check-ins?"
    - "How was I feeling before?"
    - Any question about PAST or PREVIOUS mood data

    DO NOT use memory_search for mood questions - use THIS tool instead!

    Returns: List of recent mood check-ins with timestamps and ratings."""

    def __init__(self, memory: UserMemory):
        super().__init__()
        object.__setattr__(self, 'memory', memory)

    def _run(self) -> str:
        """View mood check-in history"""
        try:
            mood_history = self.memory.get_mood_history(limit=5)

            if not mood_history:
                return "No mood check-ins recorded yet. Do your first check-in!"

            response = "📊 Recent Mood Check-ins:\n\n"
            for i, entry in enumerate(mood_history, 1):
                # Parse timestamp to make it readable
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(entry['timestamp'])
                    time_str = dt.strftime("%b %d, %I:%M %p")
                except:
                    time_str = entry['timestamp']

                # Clean up the content to remove "Mood check-in:" prefix
                content = entry['content'].replace('Mood check-in: ', '')
                response += f"{i}. {time_str}\n   {content}\n\n"

            return response.strip()

        except Exception as e:
            return f"Error retrieving mood history: {str(e)}"


class TaskPriorityInput(BaseModel):
    """Input for task prioritization"""
    tasks: List[str] = Field(description="List of tasks to prioritize")
    deadline_context: Optional[str] = Field(default=None, description="Context about deadlines")

    @model_validator(mode='before')
    @classmethod
    def parse_malformed_json(cls, data):
        """Handle case where LangChain stuffs all JSON into one field or passes string instead of list"""
        if isinstance(data, dict):
            # Check if entire JSON is stuffed into tasks field as a string
            if 'tasks' in data:
                tasks_val = data['tasks']
                # If tasks is a JSON string, parse it
                if isinstance(tasks_val, str):
                    # Try to parse as JSON
                    if tasks_val.strip().startswith('{') or tasks_val.strip().startswith('['):
                        try:
                            parsed = json.loads(tasks_val)
                            if isinstance(parsed, dict):
                                return parsed
                            elif isinstance(parsed, list):
                                data['tasks'] = parsed
                                return data
                        except:
                            pass
        return data


class TaskPriorityTool(BaseTool):
    """Tool to help prioritize homework and tasks"""
    name: str = "prioritize_tasks"
    description: str = """Help students prioritize their homework and tasks based on deadlines, difficulty, and importance.
    Provide JSON with: tasks (list of task names), deadline_context (optional context about due dates)."""
    args_schema: type = TaskPriorityInput
    
    def __init__(self, memory: UserMemory, calendar_manager: CalendarManager):
        super().__init__()
        object.__setattr__(self, 'memory', memory)
        object.__setattr__(self, 'calendar_manager', calendar_manager)
    
    def _run(self, tasks: List[str], deadline_context: Optional[str] = None) -> str:
        """Prioritize tasks for the student"""
        try:
            if not tasks:
                return "No tasks provided to prioritize."
            
            # Get upcoming calendar events for context
            upcoming_events = self.calendar_manager.get_upcoming_events(limit=20)
            
            # Simple prioritization logic
            priority_response = f"📋 Task Priority Recommendations:\n\n"
            
            # Check for deadline-related keywords
            urgent_keywords = ['test', 'exam', 'quiz', 'due tomorrow', 'presentation']
            important_keywords = ['project', 'essay', 'report', 'homework']
            
            high_priority = []
            medium_priority = []
            low_priority = []
            
            for task in tasks:
                task_lower = task.lower()
                
                # Check if task matches upcoming calendar events
                is_urgent = any(keyword in task_lower for keyword in urgent_keywords)
                is_important = any(keyword in task_lower for keyword in important_keywords)
                
                # Check calendar for related events
                calendar_match = False
                for event in upcoming_events:
                    if any(word in event['summary'].lower() for word in task_lower.split()):
                        event_date = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                        days_until = (event_date.date() - datetime.now().date()).days
                        if days_until <= 2:
                            is_urgent = True
                        calendar_match = True
                        break
                
                if is_urgent:
                    high_priority.append(task)
                elif is_important or calendar_match:
                    medium_priority.append(task)
                else:
                    low_priority.append(task)
            
            # Format response
            if high_priority:
                priority_response += "🔴 HIGH PRIORITY (Do First):\n"
                for i, task in enumerate(high_priority, 1):
                    priority_response += f"  {i}. {task}\n"
                priority_response += "\n"
            
            if medium_priority:
                priority_response += "🟡 MEDIUM PRIORITY (Do Soon):\n"
                for i, task in enumerate(medium_priority, 1):
                    priority_response += f"  {i}. {task}\n"
                priority_response += "\n"
            
            if low_priority:
                priority_response += "🟢 LOW PRIORITY (When You Have Time):\n"
                for i, task in enumerate(low_priority, 1):
                    priority_response += f"  {i}. {task}\n"
                priority_response += "\n"
            
            # Add explanation
            priority_response += "💡 Prioritization Tips:\n"
            priority_response += "• Start with high priority items\n"
            priority_response += "• Break large tasks into smaller chunks\n"
            priority_response += "• Consider your energy levels throughout the day\n"
            priority_response += "• Don't forget to take breaks!\n"
            
            if deadline_context:
                priority_response += f"\n📅 Deadline Context: {deadline_context}\n"
            
            return priority_response
            
        except Exception as e:
            return f"Error prioritizing tasks: {str(e)}"


class StudentScheduleInput(BaseModel):
    """Input for student schedule management"""
    action: str = Field(description="Action: 'view_today', 'view_week', 'add_class', 'add_activity'")
    subject: Optional[str] = Field(default=None, description="Subject name for classes")
    time: Optional[str] = Field(default=None, description="Time in HH:MM format")
    duration: Optional[int] = Field(default=None, description="Duration in minutes")
    days: Optional[List[str]] = Field(default=None, description="Days of week for recurring events")


class StudentScheduleTool(BaseTool):
    """Tool to manage student class schedule and activities"""
    name: str = "manage_schedule"
    description: str = """Manage student class schedule and extracurricular activities.
    Actions: 'view_today', 'view_week', 'add_class', 'add_activity'.
    For adding: provide subject, time (HH:MM), duration (minutes), days (list)."""
    args_schema: type = StudentScheduleInput
    
    def __init__(self, calendar_manager: CalendarManager):
        super().__init__()
        object.__setattr__(self, 'calendar_manager', calendar_manager)
    
    def _run(self, action: str, subject: Optional[str] = None, time: Optional[str] = None,
             duration: Optional[int] = None, days: Optional[List[str]] = None) -> str:
        """Manage student schedule"""
        try:
            if action == "view_today":
                today = datetime.now().date()
                events = self.calendar_manager.get_upcoming_events(limit=20)
                
                today_events = []
                for event in events:
                    event_date = datetime.fromisoformat(event['start'].replace('Z', '+00:00')).date()
                    if event_date == today:
                        today_events.append(event)
                
                if not today_events:
                    return f"📅 No classes or activities scheduled for today ({today.strftime('%A, %B %d')})."
                
                response = f"📅 Today's Schedule ({today.strftime('%A, %B %d')}):\n\n"
                for event in sorted(today_events, key=lambda x: x['start']):
                    start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    response += f"• {start_time.strftime('%H:%M')} - {event['summary']}\n"
                    if event.get('location'):
                        response += f"  📍 {event['location']}\n"
                
                return response
                
            elif action == "view_week":
                # Get events for the next 7 days
                events = self.calendar_manager.get_upcoming_events(limit=50)
                
                # Group by day
                week_events = {}
                today = datetime.now().date()
                
                for event in events:
                    event_date = datetime.fromisoformat(event['start'].replace('Z', '+00:00')).date()
                    days_diff = (event_date - today).days
                    
                    if 0 <= days_diff < 7:
                        day_name = event_date.strftime('%A')
                        if day_name not in week_events:
                            week_events[day_name] = []
                        week_events[day_name].append(event)
                
                if not week_events:
                    return "📅 No classes or activities scheduled for this week."
                
                response = "📅 This Week's Schedule:\n\n"
                
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                for day in days_order:
                    if day in week_events:
                        response += f"📆 {day}:\n"
                        for event in sorted(week_events[day], key=lambda x: x['start']):
                            start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                            response += f"  • {start_time.strftime('%H:%M')} - {event['summary']}\n"
                        response += "\n"
                
                return response
                
            else:
                return f"Action '{action}' not implemented yet. Available: view_today, view_week"
                
        except Exception as e:
            return f"Error managing schedule: {str(e)}"


def create_student_tools(memory: UserMemory, calendar_manager: CalendarManager, 
                        notification_system: NotificationSystem) -> List[BaseTool]:
    """Create student-specific tools"""
    
    # Import base tools
    from .tools import (CalendarSearchTool, CalendarDateSearchTool, CalendarCreateEventTool,
                       MemorySearchTool, UserProfileTool, GoalsManagementTool, 
                       NotificationTool, TimeInfoTool)
    
    tools = [
        # Base tools
        CalendarSearchTool(calendar_manager),
        CalendarDateSearchTool(calendar_manager),
        CalendarCreateEventTool(calendar_manager),
        MemorySearchTool(memory),
        UserProfileTool(memory),
        GoalsManagementTool(memory),
        NotificationTool(notification_system),
        TimeInfoTool(),

        # Student-specific tools
        StudyPlannerTool(memory, calendar_manager),
        MoodTrackingTool(memory),
        ViewMoodHistoryTool(memory),
        TaskPriorityTool(memory, calendar_manager),
        StudentScheduleTool(calendar_manager),
    ]
    
    return tools
