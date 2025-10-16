"""
LangChain-based Personal AI Agent
A real agent implementation with tools, memory, and reasoning capabilities
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime
import json
import os

from langchain.agents import AgentExecutor, create_openai_tools_agent, create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI

from .tools import create_agent_tools
from .student_tools import create_student_tools
from .memory import UserMemory
from .clients.calendar_integration import CalendarManager
from .notification_system import NotificationSystem
from .model_manager import ModelManager, ModelProvider


class LangChainPersonalAgent:
    """
    Advanced Personal AI Agent using LangChain
    Features: Tool use, reasoning, memory, proactive behavior
    """
    
    def __init__(self, memory: UserMemory, calendar_manager: CalendarManager, 
                 model_manager: ModelManager,
                 notification_system: NotificationSystem = None,
                 student_mode: bool = True):
        
        self.memory = memory
        self.calendar_manager = calendar_manager
        self.model_manager = model_manager
        self.notification_system = notification_system or NotificationSystem()
        self.student_mode = student_mode
        
        # Agent configuration
        self.config = {
            'max_iterations': 6,  # Reduced to prevent excessive looping
            'max_execution_time': 60,
            'verbose': True,
            'return_intermediate_steps': True,
            'early_stopping_method': 'force'  # Force stop when hitting limits
        }
        
        # Initialize LangChain components
        self.llm = self._setup_llm()
        
        # Use student-specific tools if in student mode
        if self.student_mode:
            self.tools = create_student_tools(memory, calendar_manager, self.notification_system)
        else:
            self.tools = create_agent_tools(memory, calendar_manager, self.notification_system)
            
        self.agent_executor = self._create_agent_executor()
    
    def _setup_llm(self):
        """Setup the language model based on current configuration"""
        current_model = self.model_manager.get_current_model()
        
        if current_model.provider == ModelProvider.OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            
            return ChatOpenAI(
                model=current_model.model_id,
                temperature=current_model.temperature,
                max_tokens=current_model.max_tokens,
                api_key=api_key
            )
        
        elif current_model.provider == ModelProvider.OLLAMA:
            return ChatOllama(
                model=current_model.model_id,
                temperature=current_model.temperature,
                num_predict=current_model.max_tokens,
                base_url="http://localhost:11434"
            )
        
        else:
            raise ValueError(f"Unsupported model provider: {current_model.provider}")
    
    def _handle_parsing_error(self, error: Exception) -> str:
        """Custom error handler that provides helpful feedback for retry"""
        error_str = str(error)
        
        # Check for common error patterns and provide specific guidance
        if "Field required" in error_str or "validation error" in error_str.lower():
            # Return a simple string (not an f-string) so no escaping needed
            return ('Invalid tool input format. Please retry with VALID JSON format.\n\n'
                   'CRITICAL: All JSON keys MUST be in double quotes!\n\n'
                   'Correct format examples:\n'
                   '- {"summary": "Meeting Title", "start_time": "2025-10-07T09:00:00", "end_time": "2025-10-07T10:00:00"}\n'
                   '- {"query": "search text", "limit": 5}\n'
                   '- {"action": "list"}\n\n'
                   'WRONG (missing quotes on keys):\n'
                   '- {summary: "text", start_time: "2025-10-07T09:00:00"}\n\n'
                   'Please retry the action with properly formatted JSON.')
        
        return f"Parsing error: {error_str}. Please check your input format and try again."
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create the LangChain agent executor"""
        
        current_model = self.model_manager.get_current_model()
        
        # Use different agent types based on model provider
        if current_model.provider == ModelProvider.OPENAI:
            # OpenAI supports function calling
            system_prompt = self._create_system_prompt()
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ])
            
            agent = create_openai_tools_agent(self.llm, self.tools, prompt)
            
        else:
            # Ollama and other models use ReAct pattern
            system_prompt = self._create_system_prompt()
            
            # Create ReAct prompt template  
            template = f"""{system_prompt}

TOOLS:
------
You have access to the following tools:

{{tools}}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{{tool_names}}]
Action Input: valid JSON with the correct parameters (ALL keys must be in double quotes!)
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: [your response to the user]
```

IMPORTANT: After you call a tool and get a result:
- If the result answers the user's question → provide Final Answer immediately
- If the result is an error → retry with corrected input OR explain the issue
- Do NOT call the same tool twice with identical inputs

CRITICAL - STOP REPEATING ACTIONS:
- After ANY tool returns a successful result, DO NOT call the same tool again with the same inputs!
- If you get a valid observation/result, use it and move to Final Answer
- NEVER repeat the same action more than once
- If a tool returns data (like a list of goals or events), that's your answer - format it for the user and finish

CRITICAL JSON FORMATTING RULES:
- ALL keys must be in double quotes: {{{{"key": "value"}}}}
- Strings must be in double quotes: {{{{"summary": "Meeting Title"}}}}
- Dates in ISO format: {{{{"start_time": "2025-10-07T09:00:00"}}}}

CORRECT Action Input examples:
- For create_calendar_event: {{{{"summary": "Meeting", "start_time": "2025-10-07T09:00:00", "end_time": "2025-10-07T10:00:00"}}}}
- For calendar_search_by_date (single date): {{{{"date": "2025-10-12"}}}}
- For calendar_search_by_date (date range): {{{{"start_date": "2025-10-12", "end_date": "2025-10-15"}}}}
- For memory_search: {{{{"query": "what I said about goals", "limit": 5}}}}
- For manage_goals (list): {{{{"action": "list"}}}}
- For manage_goals (add): {{{{"action": "add", "title": "Buy gift for birthday", "description": "Get present by Friday"}}}}
- For manage_goals (update): {{{{"action": "update", "title": "Learn Python", "progress": 50}}}}
- For send_notification: {{{{"title": "Reminder", "message": "Don't forget your meeting at 3pm", "priority": "normal"}}}}
- For calendar_search: ""
- For get_user_profile: ""
- For get_time_info: ""

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

Previous conversation history:
{{chat_history}}

New input: {{input}}
{{agent_scratchpad}}"""

            prompt = ChatPromptTemplate.from_template(template)
            agent = create_react_agent(self.llm, self.tools, prompt)
        
        # Create agent executor with custom error handler
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.config['verbose'],
            max_iterations=self.config['max_iterations'],
            max_execution_time=self.config['max_execution_time'],
            return_intermediate_steps=self.config['return_intermediate_steps'],
            handle_parsing_errors=self._handle_parsing_error,
            early_stopping_method=self.config['early_stopping_method']
        )
        
        return agent_executor
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent"""
        
        # Get user context
        user_profile = self.memory.get_user_profile()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.student_mode:
            system_prompt = f"""You are a friendly and supportive AI study assistant specifically designed to help junior high school students manage their academic workflow and succeed in school.

CURRENT CONTEXT:
- Current time: {current_time}
- Student's communication style: {user_profile.get('communication_style', 'Learning about student')}
- Student's interests: {', '.join(user_profile.get('interests', ['Getting to know you']))}

YOUR ROLE AS A STUDENT ASSISTANT:
You help junior high school students with:
📅 **Calendar & Schedule Management**
- Read class schedules, homework due dates, exam dates
- Create study blocks and reminders
- Track extracurricular activities and family events

📚 **Study Planning & Organization**  
- Break down assignments into manageable study sessions
- Create timeboxed study plans with explanations
- Prioritize homework and tasks by urgency and importance
- Suggest optimal study times based on the student's schedule

🎯 **Goals & Task Management**
- Track short-term tasks (homework, projects)
- Monitor longer-term goals (improve grades, learn skills)
- Set effort estimates and deadlines
- Celebrate progress and achievements

😊 **Mood & Feedback Tracking**
- Quick 5-second check-ins with emoji ratings
- Track energy levels and task difficulty
- Provide encouragement and study tips
- Adjust recommendations based on how the student feels

🔔 **Smart Notifications & Nudges**
- Send reminders at the right moments
- Gentle prompts if tasks are being avoided
- Motivational messages and study tips

💡 **Explainable Suggestions**
Every recommendation includes a brief "why" explanation:
"You've got Math on Thursday; let's do 20 min tonight so Wednesday stays light."

STUDENT-SPECIFIC TOOLS:
1. **create_study_plan** - Break assignments into study sessions across days
2. **mood_checkin** - Quick mood and energy tracking (😊😐🙁 or 1-5 scale)
3. **prioritize_tasks** - Help organize homework by urgency and importance
4. **manage_schedule** - View daily/weekly class schedule and activities
5. **manage_goals** - Track homework, projects, and academic goals
6. **calendar tools** - Read/create events, check due dates
7. **send_notification** - Reminders and motivational messages

COMMUNICATION STYLE:
- **Encouraging and positive** - celebrate small wins!
- **Age-appropriate** - use emojis, friendly language
- **Brief but helpful** - students have short attention spans
- **Practical** - focus on actionable next steps
- **Understanding** - acknowledge stress and challenges

BEHAVIORAL GUIDELINES:
1. **Always explain WHY** - help students understand your suggestions
2. **Break things down** - large tasks into smaller, manageable pieces
3. **Be flexible** - adapt to the student's energy and mood
4. **Encourage breaks** - remind about healthy study habits
5. **Respect boundaries** - don't disturb during specified quiet times
6. **Stay positive** - focus on progress, not perfection

EXAMPLE INTERACTIONS:
- "I have a history test Friday" → Create study plan with daily 20-min sessions
- "I'm feeling overwhelmed" → Mood check-in, then prioritize tasks and suggest breaks
- "What should I do first?" → Use prioritize_tasks to organize homework
- Student seems stressed → Suggest shorter study sessions, encourage self-care

Remember: You're not just a homework helper - you're a supportive study buddy who helps students develop good habits, manage stress, and succeed academically while maintaining balance in their lives."""
        else:
            # Original system prompt for non-student mode
            system_prompt = f"""You are a highly capable personal AI assistant with access to tools and the ability to reason and take actions.

CURRENT CONTEXT:
- Current time: {current_time}
- User's communication style: {user_profile.get('communication_style', 'Unknown')}
- User's interests: {', '.join(user_profile.get('interests', ['Learning about user']))}

YOUR CAPABILITIES:
You have access to several tools that allow you to:
1. Search upcoming calendar events (next 7 days)
2. Search events on a specific date or date range (use calendar_search_by_date)
3. CREATE new calendar events (use create_calendar_event tool)
4. Search through conversation history and user insights
5. Get detailed user profile and preferences
6. Manage user goals (list, add, update progress)
7. Send notifications for important reminders
8. Get current time and date information

IMPORTANT: When using tools, always provide parameters in valid JSON format with all keys in double quotes!

BEHAVIORAL GUIDELINES:
1. **Be Proactive**: Use tools to gather relevant context before responding
2. **Be Personal**: Reference the user's profile, past conversations, and preferences
3. **Be Helpful**: Suggest actions, remind about upcoming events, track goals
4. **Be Efficient**: Use multiple tools in sequence when needed to provide comprehensive help
5. **Be Respectful**: Always respect privacy settings and user preferences

Remember: You're not just answering questions - you're actively helping manage the user's life, goals, and schedule. Use your tools wisely to provide the most helpful and personalized assistance possible."""

        return system_prompt
    
    def process_message(self, user_message: str, save_to_memory: bool = True) -> Dict[str, Any]:
        """
        Process a user message using the LangChain agent
        
        Returns:
            Dict containing response, intermediate steps, and metadata
        """
        
        # Save user message to memory
        if save_to_memory:
            self.memory.add_message('user', user_message)
        
        # Get conversation history for context
        chat_history = self._get_chat_history()
        
        try:
            # Run the agent
            result = self.agent_executor.invoke({
                "input": user_message,
                "chat_history": chat_history
            })
            
            response = result.get("output", "I apologize, but I couldn't process your request properly.")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Save agent response to memory
            if save_to_memory:
                self.memory.add_message('agent', response)
                
                # Learn from the interaction
                self._learn_from_interaction(user_message, response, intermediate_steps)
            
            return {
                "response": response,
                "intermediate_steps": intermediate_steps,
                "tools_used": [step[0].tool for step in intermediate_steps],
                "success": True
            }
            
        except Exception as e:
            error_response = f"I encountered an error while processing your request: {str(e)}"
            
            if save_to_memory:
                self.memory.add_message('agent', error_response)
            
            return {
                "response": error_response,
                "intermediate_steps": [],
                "tools_used": [],
                "success": False,
                "error": str(e)
            }
    
    def _get_chat_history(self, limit: int = 10):
        """Get recent chat history as string or messages depending on agent type"""
        recent_messages = self.memory.get_recent_messages(limit)
        
        current_model = self.model_manager.get_current_model()
        
        if current_model.provider == ModelProvider.OPENAI:
            # OpenAI agent uses message objects
            chat_history = []
            for msg in recent_messages[:-1]:  # Exclude the current message
                if msg['sender'] == 'user':
                    chat_history.append(HumanMessage(content=msg['content']))
                else:
                    chat_history.append(AIMessage(content=msg['content']))
            return chat_history
        else:
            # ReAct agent uses string format
            chat_history_str = ""
            for msg in recent_messages[:-1]:
                role = "Human" if msg['sender'] == 'user' else "AI"
                chat_history_str += f"{role}: {msg['content']}\n"
            return chat_history_str
    
    def _learn_from_interaction(self, user_message: str, agent_response: str, 
                              intermediate_steps: List[Tuple]) -> None:
        """Learn from the interaction to improve future responses"""
        
        # Analyze communication patterns
        self._analyze_communication_style(user_message)
        
        # Extract interests from user message
        self._extract_interests(user_message)
        
        # Learn from tool usage patterns
        self._learn_tool_usage_patterns(intermediate_steps)
        
        # Update user profile
        self._update_user_profile(user_message)
        
        # Generate insights about the interaction
        self._generate_interaction_insights(user_message, agent_response, intermediate_steps)
    
    def _analyze_communication_style(self, message: str):
        """Analyze and update user's communication style"""
        message_length = len(message.split())
        question_count = message.count('?')
        
        if message_length < 5:
            style = 'concise'
        elif question_count > 1 and message_length > 20:
            style = 'detailed'
        elif question_count > 0:
            style = 'inquisitive'
        else:
            style = 'conversational'
        
        # Update profile
        profile = self.memory.get_user_profile()
        profile['communication_style'] = style
        self.memory.update_user_profile(profile)
    
    def _extract_interests(self, message: str):
        """Extract and update user interests"""
        # Enhanced interest detection
        interest_keywords = {
            'work': ['work', 'job', 'career', 'office', 'meeting', 'project', 'deadline'],
            'technology': ['code', 'programming', 'software', 'tech', 'computer', 'AI', 'machine learning'],
            'health': ['exercise', 'workout', 'gym', 'health', 'fitness', 'diet', 'nutrition'],
            'learning': ['learn', 'study', 'course', 'book', 'education', 'skill', 'training'],
            'travel': ['travel', 'trip', 'vacation', 'flight', 'hotel', 'destination'],
            'entertainment': ['movie', 'music', 'game', 'show', 'entertainment', 'fun'],
            'finance': ['money', 'budget', 'investment', 'savings', 'financial', 'expense']
        }
        
        message_lower = message.lower()
        found_interests = []
        
        for category, keywords in interest_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                found_interests.append(category)
        
        if found_interests:
            profile = self.memory.get_user_profile()
            current_interests = profile.get('interests', [])
            
            for interest in found_interests:
                if interest not in current_interests:
                    current_interests.append(interest)
            
            profile['interests'] = current_interests[:15]  # Keep top 15
            self.memory.update_user_profile(profile)
    
    def _learn_tool_usage_patterns(self, intermediate_steps: List[Tuple]):
        """Learn from which tools were used and when"""
        if not intermediate_steps:
            return
        
        tools_used = [step[0].tool for step in intermediate_steps]
        
        # Store tool usage pattern in insights
        insight = f"Used tools: {', '.join(tools_used)} at {datetime.now().strftime('%H:%M')}"
        self.memory.add_simple_insight(insight)
    
    def _update_user_profile(self, message: str):
        """Update user profile with interaction data"""
        profile = self.memory.get_user_profile()
        
        # Update timing patterns
        current_hour = datetime.now().hour
        active_hours = profile.get('active_hours', {})
        hour_str = str(current_hour)
        active_hours[hour_str] = active_hours.get(hour_str, 0) + 1
        
        # Update interaction stats
        profile['active_hours'] = active_hours
        profile['last_interaction'] = datetime.now().isoformat()
        profile['total_interactions'] = profile.get('total_interactions', 0) + 1
        
        self.memory.update_user_profile(profile)
    
    def _generate_interaction_insights(self, user_message: str, agent_response: str, 
                                     intermediate_steps: List[Tuple]):
        """Generate insights about the interaction"""
        
        # Analyze the complexity of the request
        tools_count = len(intermediate_steps)
        
        if tools_count > 2:
            insight = f"Complex request requiring {tools_count} tools - user appreciates comprehensive assistance"
            self.memory.add_simple_insight(insight)
        
        # Analyze request patterns
        if any(word in user_message.lower() for word in ['remind', 'notification', 'alert']):
            insight = "User values proactive reminders and notifications"
            self.memory.add_simple_insight(insight)
        
        if any(word in user_message.lower() for word in ['goal', 'progress', 'achievement']):
            insight = "User is goal-oriented and tracks progress"
            self.memory.add_simple_insight(insight)
    
    def get_proactive_suggestions(self) -> List[str]:
        """Generate proactive suggestions using agent reasoning"""
        
        try:
            # Use the agent to generate proactive suggestions
            proactive_prompt = """Based on the user's profile, recent conversations, upcoming calendar events, and goals, 
            generate 2-3 proactive suggestions that would be helpful right now. 
            Use your tools to gather current context first, then provide specific, actionable suggestions.
            
            Focus on:
            1. Upcoming events that might need preparation
            2. Goals that haven't been updated recently
            3. Patterns in user behavior that suggest helpful actions
            
            Format your response as a simple list of suggestions."""
            
            result = self.agent_executor.invoke({
                "input": proactive_prompt,
                "chat_history": []
            })
            
            response = result.get("output", "")
            
            # Parse suggestions from response
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    suggestion = line.lstrip('-•* ').strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions[:3]  # Limit to 3 suggestions
            
        except Exception as e:
            print(f"Error generating proactive suggestions: {e}")
            return []
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and capabilities"""
        
        current_model = self.model_manager.get_current_model()
        
        return {
            "agent_type": "LangChain Agent",
            "model": {
                "name": current_model.name,
                "provider": current_model.provider.value,
                "local": current_model.local
            },
            "tools_available": len(self.tools),
            "tool_names": [tool.name for tool in self.tools],
            "memory_enabled": True,
            "proactive_enabled": True,
            "total_interactions": self.memory.get_user_profile().get('total_interactions', 0)
        }
    
    def update_model(self, model_key: str) -> bool:
        """Update the language model"""
        if self.model_manager.set_model(model_key):
            self.llm = self._setup_llm()
            self.agent_executor = self._create_agent_executor()
            return True
        return False
