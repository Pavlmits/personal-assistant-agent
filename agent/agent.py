"""
Main AI Agent Implementation
Handles conversation, learning, and proactive behavior
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
from .model_manager import ModelManager
from .prompts import SYSTEM_PROMPT

class ProactiveAgent:
    """
    Main AI agent that learns from interactions and provides proactive assistance
    """
    
    def __init__(self, memory, calendar_manager, privacy_manager, model_manager=None):
        self.memory = memory
        self.calendar_manager = calendar_manager
        self.privacy_manager = privacy_manager
        
        # Initialize model manager
        self.model_manager = model_manager or ModelManager()
        
        # Agent configuration
        self.config = {
            'proactive_enabled': True,
            'max_context_messages': 10,  # Number of previous messages to include in AI model context
            'proactive_frequency': 0.3  # 30% chance of proactive suggestion
        }
        
        # Agent system prompt
        self.system_prompt = SYSTEM_PROMPT

    def process_message(self, user_message: str, save_to_memory: bool = True) -> str:
        """
        Process a user message and generate a response
        """
        # Save user message to memory
        if save_to_memory:
            self.memory.add_message('user', user_message)
        
        # Get conversation context
        context = self._build_context()
        
        # Generate response using OpenAI or fallback
        response = self._generate_response(user_message, context)
        
        # Save agent response to memory
        if save_to_memory:
            self.memory.add_message('agent', response)
            
        # Learn from the interaction
        self._learn_from_interaction(user_message, response)
        
        return response
    
    def _generate_response(self, user_message: str, context: Dict) -> str:
        """
        Generate a response using the selected AI model or fallback logic
        """
        try:
            # Build messages for the AI model
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": f"Context: {json.dumps(context, default=str)}"},
            ]
            
            # Add recent conversation history
            recent_messages = self.memory.get_recent_messages(self.config['max_context_messages'])
            for msg in recent_messages[:-1]:  # Exclude the current message
                role = "user" if msg['sender'] == 'user' else "assistant"
                messages.append({"role": role, "content": msg['content']})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response using model manager
            response = self.model_manager.generate_response(messages)
            return response
                
        except Exception as e:
            print(f"AI model error: {e}")
            return self._fallback_response(user_message, context)
    
    def _fallback_response(self, user_message: str, context: Dict) -> str:
        """
        Simple fallback response when AI model is not available
        """
        return "I'm sorry, but my AI language model is currently unavailable. Please try again later or check your connection."
    
    def _build_context(self) -> Dict[str, Any]:
        """
        Build context for response generation
        """
        context = {
            'current_time': datetime.now().isoformat(),
            'user_profile': self.memory.get_user_profile(),
            'goals': self.memory.get_goals(),
            'recent_insights': self.memory.get_recent_insights()
        }
        
        # Add calendar context if available
        try:
            upcoming_events = self.calendar_manager.get_upcoming_events(limit=5)
            context['upcoming_events'] = upcoming_events
        except:
            context['upcoming_events'] = []
        
        return context
    
    def _learn_from_interaction(self, user_message: str, agent_response: str):
        """
        Learn from the interaction to improve future responses
        """
        # Analyze communication patterns
        self._analyze_communication_style(user_message)
        
        # Extract potential interests/topics
        self._extract_interests(user_message)
        
        # Learn timing patterns
        self._learn_timing_patterns()
        
        # Update user profile
        self._update_user_profile(user_message)
    
    def _analyze_communication_style(self, message: str):
        """
        Analyze user's communication style preferences
        """
        # Simple heuristics for communication style, I will use NLP in a real implementation
        if len(message.split()) < 5:
            style = 'concise'
        elif '?' in message and len(message.split()) > 20:
            style = 'detailed'
        else:
            style = 'conversational'
        
        # Update profile
        profile = self.memory.get_user_profile()
        profile['communication_style'] = style
        self.memory.update_user_profile(profile)
    
    def _extract_interests(self, message: str):
        """
        Extract topics and interests from user messages
        """
        # Simple keyword extraction (in a real implementation, I will use NLP)
        interests_keywords = [
            'work', 'project', 'coding', 'programming', 'meeting', 'exercise',
            'health', 'book', 'reading', 'travel', 'music', 'cooking', 'learning'
        ]
        
        message_lower = message.lower()
        found_interests = [word for word in interests_keywords if word in message_lower]
        
        if found_interests:
            profile = self.memory.get_user_profile()
            current_interests = profile.get('interests', [])
            
            for interest in found_interests:
                if interest not in current_interests:
                    current_interests.append(interest)
            
            profile['interests'] = current_interests[:10]  # Keep top 10
            self.memory.update_user_profile(profile)
    
    def _learn_timing_patterns(self):
        """
        Learn when user is most active
        """
        current_hour = datetime.now().hour
        profile = self.memory.get_user_profile()
        
        # Track active hours
        active_hours = profile.get('active_hours', {})
        hour_str = str(current_hour)
        active_hours[hour_str] = active_hours.get(hour_str, 0) + 1
        
        profile['active_hours'] = active_hours
        self.memory.update_user_profile(profile)
    
    def _update_user_profile(self, message: str):
        """
        Update user profile based on message content
        """
        profile = self.memory.get_user_profile()
        
        # Update last interaction
        profile['last_interaction'] = datetime.now().isoformat()
        profile['total_interactions'] = profile.get('total_interactions', 0) + 1
        
        self.memory.update_user_profile(profile)
    
    def get_proactive_suggestions(self) -> List[str]:
        """
        Generate proactive suggestions based on user context
        """
        if not self.config['proactive_enabled']:
            return []
        
        suggestions = []
        context = self._build_context()
        
        # Calendar-based suggestions
        upcoming_events = context.get('upcoming_events', [])
        if upcoming_events:
            next_event = upcoming_events[0]
            event_time = datetime.fromisoformat(next_event['start'].replace('Z', '+00:00'))
            time_until = event_time - datetime.now(event_time.tzinfo)
            
            if timedelta(minutes=30) <= time_until <= timedelta(hours=2):
                suggestions.append(f"You have '{next_event['summary']}' in {self._format_time_delta(time_until)}. Need any preparation?")
        
        # Goal-based suggestions
        goals = context.get('goals', [])
        for goal in goals:
            if goal.get('progress', 0) < 100:
                last_update = goal.get('last_update')
                if not last_update or (datetime.now() - datetime.fromisoformat(last_update)).days > 3:
                    suggestions.append(f"Haven't heard about your '{goal['title']}' goal lately. How's it progressing?")
        
        # Pattern-based suggestions
        profile = context.get('user_profile', {})
        active_hours = profile.get('active_hours', {})
        current_hour = str(datetime.now().hour)
        
        if active_hours.get(current_hour, 0) > 5:  # User is typically active now
            if random.random() < self.config['proactive_frequency']:
                interests = profile.get('interests', [])
                if interests:
                    interest = random.choice(interests)
                    suggestions.append(f"Since you're interested in {interest}, I found something that might help you today.")
        
        # Learning-based suggestions
        recent_insights = context.get('recent_insights', [])
        if len(recent_insights) > 3:
            suggestions.append("I've been learning a lot about your preferences. Want to see what I've discovered?")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _format_time_delta(self, td: timedelta) -> str:
        """
        Format a time delta in a human-readable way
        """
        total_minutes = int(td.total_seconds() / 60)
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{hours}h {minutes}m"
