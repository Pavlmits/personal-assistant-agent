"""
Message templates for notifications and user-facing content
"""

# Pre-written message templates for different notification types
NOTIFICATION_TEMPLATES = {
    'calendar': {
        'meeting_soon': [
            "You have '{event_title}' in {time_until}. Need any preparation?",
            "Upcoming: '{event_title}' in {time_until}. Ready to go?",
            "'{event_title}' starts in {time_until}. All set?"
        ],
        'meeting_prep': [
            "'{event_title}' is coming up in {time_until}. Want to review your notes?",
            "Meeting with {attendees} in {time_until}. Need to prepare anything?",
            "'{event_title}' in {time_until}. Should we go over the agenda?"
        ]
    },
    'goal': {
        'stale_reminder': [
            "Haven't heard about your '{goal_title}' goal in {days} days. How's it going?",
            "Your '{goal_title}' goal has been quiet for {days} days. Ready to make progress?",
            "It's been {days} days since your last update on '{goal_title}'. Time for an update?"
        ],
        'deadline_approaching': [
            "'{goal_title}' deadline is in {days_left} days. Current progress: {progress}%",
            "Heads up: '{goal_title}' is due in {days_left} days. You're at {progress}%",
            "'{goal_title}' deadline approaching ({days_left} days). Progress check: {progress}%"
        ]
    },
    'pattern': {
        'productive_time': [
            "It's {time} - your most productive time. Ready to tackle some work?",
            "Based on your patterns, now is great for {activity}. Want to get started?",
            "You're usually very focused at {time}. Good time for {activity}?"
        ],
        'interest_match': [
            "Since you're interested in {interest}, I found something that might help today.",
            "Your {interest} interest might find this timing perfect for {activity}.",
            "Given your passion for {interest}, now could be ideal for {activity}."
        ]
    },
    'learning': {
        'insights_ready': [
            "I've learned {insight_count} new things about your preferences. Want to see?",
            "After analyzing your patterns, I have {insight_count} insights to share.",
            "I've discovered {insight_count} patterns in your behavior. Interested in the details?"
        ]
    }
}
