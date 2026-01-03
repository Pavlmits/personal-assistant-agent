#!/usr/bin/env python3
"""
Streamlit Web Interface for Personal AI Agent
A modern web interface for the LangChain-based personal assistant
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List, Any
import json
import traceback

# Import your existing agent components
from agent.langchain_agent import LangChainPersonalAgent
from agent.memory import UserMemory
from agent.clients.calendar_integration import CalendarManager
from agent.model_manager import ModelManager
from agent.proactive_manager import ProactiveManager, ProactiveConfig
from agent.system_service import SystemServiceManager
from agent.notification_system import NotificationSystem

# Import student setup
from student_setup import show_student_setup

# Page configuration
st.set_page_config(
    page_title="Student Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling and readability
st.markdown("""
<style>
    /* Force light theme and high contrast */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Main content area */
    .main .block-container {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background-color: #f8f9fa !important;
        color: #000000 !important;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50 !important;
        text-align: center;
        margin-bottom: 2rem;
        background-color: #ffffff !important;
    }
    
    /* Chat message containers */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
        color: #000000 !important;
        border: 1px solid #dee2e6;
    }
    
    .user-message {
        background-color: #e8f4fd !important;
        margin-left: auto;
        text-align: right;
        border-left: 4px solid #007bff;
        color: #000000 !important;
    }
    
    .agent-message {
        background-color: #f8f9fa !important;
        margin-right: auto;
        border-left: 4px solid #28a745;
        color: #000000 !important;
    }
    
    /* Tool usage indicators */
    .tool-usage {
        background-color: #fff3cd !important;
        color: #856404 !important;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        border: 1px solid #ffeaa7;
    }
    
    /* Sidebar sections */
    .sidebar-section {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    /* Metrics and text */
    .metric-container {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Ensure all text is readable */
    .stMarkdown, .stText, .stMetric, .stSelectbox, .stButton {
        color: #000000 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #007bff !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 5px !important;
    }
    
    .stButton > button:hover {
        background-color: #0056b3 !important;
        color: #ffffff !important;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ced4da !important;
    }
    
    /* Chat input styling */
    .stChatInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ced4da !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        color: #000000 !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background-color: #28a745 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Footer styling */
    .footer {
        background-color: #f8f9fa !important;
        color: #6c757d !important;
        text-align: center;
        padding: 1rem;
        border-top: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_agent():
    """Initialize the agent (cached to avoid re-initialization)"""
    try:
        # Initialize components
        memory = UserMemory()
        calendar_mgr = CalendarManager()
        model_mgr = ModelManager()
        notification_system = NotificationSystem()
        
        # Setup default model if none selected
        current_model = model_mgr.setup_default_model()
        
        # Create LangChain agent (in student mode)
        agent = LangChainPersonalAgent(
            memory=memory,
            calendar_manager=calendar_mgr,
            model_manager=model_mgr,
            notification_system=notification_system,
            student_mode=True
        )
        
        # Initialize proactive manager
        proactive_config = ProactiveConfig(
            enabled=True,
            check_interval=900,  # 15 minutes
            max_notifications_per_hour=6,
            learning_enabled=True,
            calendar_integration=calendar_mgr.is_available(),
            goal_tracking=True,
            pattern_analysis=True
        )
        
        agent.proactive_manager = ProactiveManager(
            memory=memory,
            calendar_manager=calendar_mgr,
            config=proactive_config,
            agent=agent
        )
        
        return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None

def display_chat_message(sender: str, content: str, tools_used: List[str] = None):
    """Display a chat message with proper styling"""
    if sender == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message agent-message">
            <strong>🤖 Agent:</strong> {content}
        </div>
        """, unsafe_allow_html=True)
        
        # Show tools used if any
        if tools_used:
            tools_str = ", ".join(tools_used)
            st.markdown(f"""
            <div class="tool-usage">
                🔧 <strong>Tools used:</strong> {tools_str}
            </div>
            """, unsafe_allow_html=True)

def display_agent_status(agent):
    """Display agent status in sidebar"""
    if agent is None:
        st.sidebar.error("Agent not initialized")
        return
    
    status = agent.get_agent_status()
    
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <h3>🤖 Agent Status</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.metric("Agent Type", status['agent_type'])
    st.sidebar.metric("Model", f"{status['model']['name']} ({status['model']['provider']})")
    st.sidebar.metric("Tools Available", status['tools_available'])
    st.sidebar.metric("Total Interactions", status['total_interactions'])
    
    # Show model type
    model_type = "🟢 Local" if status['model']['local'] else "🔵 Cloud"
    st.sidebar.metric("Model Type", model_type)
    

def display_user_profile(agent):
    """Display user profile information"""
    if agent is None:
        return
    
    profile = agent.memory.get_user_profile()
    
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <h3>👤 Your Profile</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.write(f"**Communication Style:** {profile.get('communication_style', 'Learning...')}")
    
    interests = profile.get('interests', [])
    if interests:
        st.sidebar.write(f"**Interests:** {', '.join(interests[:5])}")
    
    # Active hours
    active_hours = profile.get('active_hours', {})
    if active_hours:
        most_active = max(active_hours.items(), key=lambda x: x[1])
        st.sidebar.write(f"**Most Active:** {most_active[0]}:00 ({most_active[1]} times)")

def display_goals(agent):
    """Display user goals"""
    if agent is None:
        return
    
    goals = agent.memory.get_goals()
    
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <h3>🎯 Your Goals</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if goals:
        for goal in goals[:3]:  # Show top 3 goals
            progress = goal.get('progress', 0)
            st.sidebar.progress(progress / 100, text=f"{goal['title']} ({progress}%)")
    else:
        st.sidebar.write("No goals set yet. Ask the agent to help you create some!")

def main():
    """Main Streamlit application"""
    
    # Check if student setup is needed
    try:
        memory = UserMemory()
        profile = memory.get_user_profile()
        setup_complete = profile.get("setup_complete", False)
    except:
        setup_complete = False
    
    # Show setup screen if not completed
    if not setup_complete:
        show_student_setup()
        return
    
    # Header
    st.markdown('<h1 class="main-header">🎓 Student Study Assistant</h1>', unsafe_allow_html=True)
    
    # Initialize agent
    agent = initialize_agent()
    
    if agent is None:
        st.error("Failed to initialize the AI agent. Please check your configuration.")
        return
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent_initialized" not in st.session_state:
        st.session_state.agent_initialized = True
        # Add student-focused welcome message
        try:
            profile = agent.memory.get_user_profile()
            student_name = profile.get("student_name", "there")
            grade = profile.get("grade", "")
            grade_text = f" (Grade {grade})" if grade else ""
        except:
            student_name = "there"
            grade_text = ""
            
        welcome_msg = f"""
        👋 Hi {student_name}{grade_text}! I'm your study assistant, ready to help you succeed in school!
        
        I can help you with:
        📚 **Study Planning** - Break down assignments into manageable sessions
        📅 **Schedule Management** - Track classes, homework, and activities  
        🎯 **Goal Tracking** - Monitor your academic progress
        😊 **Mood Check-ins** - Quick 5-second check-ins to adjust your plan
        📋 **Task Prioritization** - Figure out what to do first
        🔔 **Smart Reminders** - Get nudged at the right time
        
        What would you like to work on today? 📖✨
        """
        st.session_state.messages.append({
            "sender": "agent",
            "content": welcome_msg,
            "tools_used": [],
            "timestamp": datetime.now()
        })
    
    # Sidebar with student info
    with st.sidebar:
        st.title("📚 Study Dashboard")
        
        # Agent status
        display_agent_status(agent)
        
        # User profile
        display_user_profile(agent)
        
        # Goals
        display_goals(agent)
        
        # Student-focused quick actions
        st.markdown("### Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📅 Today's Schedule"):
                st.session_state.quick_message = "What classes do I have today?"
            if st.button("📚 Study Plan"):
                st.session_state.quick_message = "Help me create a study plan for my upcoming assignments"
        
        with col2:
            if st.button("🎯 My Goals"):
                st.session_state.quick_message = "Show me my academic goals and progress"
            if st.button("😊 Mood Check"):
                st.session_state.quick_message = "I want to do a quick mood check-in"
        
        # Additional student actions
        col3, col4 = st.columns(2)
        with col3:
            if st.button("📋 Prioritize Tasks"):
                st.session_state.quick_message = "Help me prioritize my homework and tasks"
        
        with col4:
            if st.button("⚡ Quick Help"):
                st.session_state.quick_message = "I need help with something urgent"

        # Profile management
        st.markdown("---")
        st.markdown("### Settings")

        col_settings1, col_settings2 = st.columns(2)
        with col_settings1:
            if st.button("👤 Edit Profile", use_container_width=True):
                # Delete setup_complete from database to trigger setup wizard
                import sqlite3
                conn = sqlite3.connect("user_memory.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_profile WHERE key = 'setup_complete'")
                conn.commit()
                conn.close()
                # Clear cached agent so it re-initializes after setup
                st.cache_resource.clear()
                st.rerun()

        with col_settings2:
            if st.button("🗑️ Clear Chat", type="secondary", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        # Model selection
        st.markdown("### Model Settings")
        model_status = agent.model_manager.get_model_status()
        current_model = model_status['current_model_info']
        
        st.write(f"**Current Model:** {current_model.name}")
        st.write(f"**Provider:** {current_model.provider.value}")
        
        # Show available models
        available_models = list(model_status['available_models'].keys())
        if len(available_models) > 1:
            selected_model = st.selectbox(
                "Switch Model:",
                available_models,
                index=available_models.index(current_model.name.lower().replace(' ', '_')) if current_model.name.lower().replace(' ', '_') in available_models else 0
            )
            
            if st.button("Switch Model"):
                if agent.update_model(selected_model):
                    st.success(f"Switched to {selected_model}")
                    st.rerun()
                else:
                    st.error(f"Failed to switch to {selected_model}")
    
    # Main chat interface
    st.markdown("### 💬 Chat with Your Agent")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            display_chat_message(
                message["sender"], 
                message["content"],
                message.get("tools_used", [])
            )
    
    # Handle quick actions
    if hasattr(st.session_state, 'quick_message'):
        user_input = st.session_state.quick_message
        del st.session_state.quick_message
    else:
        # Chat input
        user_input = st.chat_input("Type your message here...")
    
    # Process user input
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({
            "sender": "user",
            "content": user_input,
            "tools_used": [],
            "timestamp": datetime.now()
        })
        
        # Display user message immediately
        with chat_container:
            display_chat_message("user", user_input)
        
        # Show thinking indicator
        with st.spinner("🤔 Agent thinking..."):
            try:
                # Process message with agent
                result = agent.process_message(user_input, save_to_memory=True)
                
                if result['success']:
                    response = result['response']
                    tools_used = result.get('tools_used', [])
                    
                    # Add agent response to chat
                    st.session_state.messages.append({
                        "sender": "agent",
                        "content": response,
                        "tools_used": tools_used,
                        "timestamp": datetime.now()
                    })
                    
                    # Display agent response
                    with chat_container:
                        display_chat_message("agent", response, tools_used)
                    
                else:
                    error_msg = f"I encountered an error: {result['response']}"
                    st.session_state.messages.append({
                        "sender": "agent",
                        "content": error_msg,
                        "tools_used": [],
                        "timestamp": datetime.now()
                    })
                    
                    with chat_container:
                        display_chat_message("agent", error_msg)
                
            except Exception as e:
                error_msg = f"An unexpected error occurred: {str(e)}"
                st.error(error_msg)
                
                # Add error to chat history
                st.session_state.messages.append({
                    "sender": "agent",
                    "content": error_msg,
                    "tools_used": [],
                    "timestamp": datetime.now()
                })
        
        # Rerun to update the interface
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        🎓 Student Study Assistant - Powered by LangChain & Streamlit<br>
        <em>Your AI study buddy for academic success and better study habits</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
