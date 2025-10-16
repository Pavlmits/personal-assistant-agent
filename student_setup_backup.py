#!/usr/bin/env python3
"""
Student Setup Screen for Streamlit
Helps students configure their schedule, preferences, and constraints
"""

import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
import io
from typing import Dict, List, Any

# Add CSS for better visibility
st.markdown("""
<style>
    /* Ensure all text is visible on white background */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Fix input field text - multiple selectors for dynamic content */
    .stTextInput > div > div > input,
    .stTextInput input,
    input[type="text"],
    input[type="email"],
    input[type="number"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Fix selectbox text - multiple selectors */
    .stSelectbox > div > div,
    .stSelectbox select,
    .stSelectbox > div > div > div,
    select {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Fix selectbox dropdown options */
    .stSelectbox > div > div > div > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Fix labels and text - comprehensive selectors */
    .stMarkdown, .stText, label, 
    .stTextInput label,
    .stSelectbox label,
    .stTimeInput label,
    .stDateInput label,
    .stMultiSelect label,
    .stSlider label,
    .stFileUploader label,
    .stTextArea label,
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stText"],
    .stTextInput > label,
    .stSelectbox > label,
    .stTimeInput > label,
    .stDateInput > label,
    [data-testid="stTextInput"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stTimeInput"] label,
    [data-testid="stDateInput"] label,
    .stTextInput div[data-testid="stWidgetLabel"],
    .stSelectbox div[data-testid="stWidgetLabel"],
    .stTimeInput div[data-testid="stWidgetLabel"],
    .stDateInput div[data-testid="stWidgetLabel"] {
        color: #000000 !important;
    }
    
    /* Fix tab text - comprehensive targeting */
    .stTabs [data-baseweb="tab-list"] button,
    .stTabs [data-baseweb="tab-list"] button span,
    .stTabs [data-baseweb="tab-list"] button div,
    .stTabs button,
    .stTabs button span,
    .stTabs button div,
    [data-testid="stTabs"] button,
    [data-testid="stTabs"] button span,
    [data-testid="stTabs"] button div {
        color: #000000 !important;
    }
    
    /* Fix active tab text */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] span,
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] div {
        color: #000000 !important;
    }
    
    /* Fix expander headers */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        color: #000000 !important;
    }
    
    /* Fix time input - multiple selectors */
    .stTimeInput > div > div > input,
    .stTimeInput input,
    input[type="time"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Fix date input */
    .stDateInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Fix multiselect */
    .stMultiSelect > div > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Fix slider text */
    .stSlider > div > div > div {
        color: #000000 !important;
    }
    
    /* Fix file uploader */
    .stFileUploader > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Fix text area */
    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Fix button text */
    .stButton > button {
        color: #ffffff !important;
        background-color: #007bff !important;
    }
    
    /* Fix headers */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }
    
    /* Fix container text */
    .element-container {
        color: #000000 !important;
    }
    
    /* Universal text color fix for all elements */
    * {
        color: #000000 !important;
    }
    
    /* Override for buttons to keep white text */
    .stButton > button, 
    button[kind="primary"],
    button[kind="secondary"] {
        color: #ffffff !important;
    }
    
    /* Fix any remaining input elements - FORCE black text when typing */
    input, select, textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Force input text to be black - override all states */
    input:focus, input:active, input:hover,
    select:focus, select:active, select:hover,
    textarea:focus, textarea:active, textarea:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Target input value specifically */
    input[type="text"]::placeholder,
    input[type="email"]::placeholder,
    input[type="number"]::placeholder,
    input[type="time"]::placeholder,
    textarea::placeholder {
        color: #999999 !important;
        -webkit-text-fill-color: #999999 !important;
    }
    
    /* Ensure typed text is black */
    input:not(:placeholder-shown) {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Fix dynamic content containers */
    .stContainer, .stColumn, .stExpander {
        color: #000000 !important;
    }
    
    /* Fix specific Streamlit test IDs - FORCE black text */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] select,
    [data-testid="stTimeInput"] input,
    [data-testid="stDateInput"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Force Streamlit input text to be black when typing */
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextInput"] input:active,
    [data-testid="stSelectbox"] select:focus,
    [data-testid="stTimeInput"] input:focus,
    [data-testid="stDateInput"] input:focus {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Aggressive label fixing - target all possible label elements */
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] > div,
    [data-testid="stWidgetLabel"] p,
    .stTextInput [data-testid="stWidgetLabel"],
    .stSelectbox [data-testid="stWidgetLabel"],
    .stTimeInput [data-testid="stWidgetLabel"],
    .stDateInput [data-testid="stWidgetLabel"],
    .stMultiSelect [data-testid="stWidgetLabel"],
    .stSlider [data-testid="stWidgetLabel"],
    .stFileUploader [data-testid="stWidgetLabel"],
    .stTextArea [data-testid="stWidgetLabel"] {
        color: #000000 !important;
    }
    
    /* Target paragraph elements that might contain labels */
    p, span, div {
        color: #000000 !important;
    }
    
    /* NUCLEAR OPTION - Force ALL tabs to be black */
    .stTabs * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Fix tab container */
    .stTabs {
        color: #000000 !important;
    }
    
    /* Fix tab list container */
    [role="tablist"],
    [role="tablist"] *,
    [role="tablist"] button,
    [role="tablist"] button * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Fix individual tabs */
    [role="tab"],
    [role="tab"] *,
    [role="tab"] span,
    [role="tab"] div {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Fix tab content */
    [role="tabpanel"] {
        color: #000000 !important;
    }
    
    /* Fix base web tab component */
    [data-baseweb="tab"],
    [data-baseweb="tab"] *,
    [data-baseweb="tab-list"],
    [data-baseweb="tab-list"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

def show_student_setup():
    """Display the student setup screen"""
    
    st.markdown("# 🎓 Student Assistant Setup")
    st.markdown("Let's set up your personal study assistant! This will help me understand your schedule and preferences.")
    
    # Initialize session state for setup data
    if "setup_data" not in st.session_state:
        st.session_state.setup_data = {
            "student_name": "",
            "grade": 7,
            "school_name": "",
            "schedule": {},
            "activities": [],
            "constraints": {},
            "preferences": {},
            "goals": []
        }
    
    # Setup tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Basic Info", 
        "📅 School Schedule", 
        "🏃 Activities", 
        "⚙️ Preferences", 
        "🎯 Goals"
    ])
    
    with tab1:
        show_basic_info_setup()
    
    with tab2:
        show_schedule_setup()
    
    with tab3:
        show_activities_setup()
    
    with tab4:
        show_preferences_setup()
    
    with tab5:
        show_goals_setup()
    
    # Setup completion
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Complete Setup", type="primary", use_container_width=True):
            if validate_setup():
                save_setup_data()
                st.success("🎉 Setup complete! Your student assistant is ready to help!")
                st.session_state.setup_complete = True
                st.rerun()
            else:
                st.error("Please complete all required fields before finishing setup.")

def show_basic_info_setup():
    """Basic student information"""
    st.markdown("### 👤 Tell me about yourself")
    
    # Re-apply CSS after each interaction
    st.markdown("""
    <style>
        /* Force all text to be black - applied inline */
        .stTextInput label, .stSelectbox label, .stTimeInput label, .stDateInput label {
            color: #000000 !important;
        }
        [data-testid="stWidgetLabel"] {
            color: #000000 !important;
        }
        .stTextInput input, .stSelectbox select, .stTimeInput input, .stDateInput input {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #cccccc !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p style="color: black; font-weight: 500; margin-bottom: 0.25rem;">What\'s your name?</p>', unsafe_allow_html=True)
        st.session_state.setup_data["student_name"] = st.text_input(
            "What's your name?", 
            value=st.session_state.setup_data["student_name"],
            placeholder="Enter your first name",
            label_visibility="collapsed"
        )
        
        st.markdown('<p style="color: black; font-weight: 500; margin-bottom: 0.25rem;">What grade are you in?</p>', unsafe_allow_html=True)
        st.session_state.setup_data["grade"] = st.selectbox(
            "What grade are you in?",
            options=[6, 7, 8, 9],
            index=[6, 7, 8, 9].index(st.session_state.setup_data["grade"]),
            format_func=lambda x: f"Grade {x}",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<p style="color: black; font-weight: 500; margin-bottom: 0.25rem;">School name (optional)</p>', unsafe_allow_html=True)
        st.session_state.setup_data["school_name"] = st.text_input(
            "School name (optional)",
            value=st.session_state.setup_data["school_name"],
            placeholder="Your school name",
            label_visibility="collapsed"
        )
        
        st.markdown('<p style="color: black; font-weight: 500; margin-bottom: 0.25rem;">Time zone</p>', unsafe_allow_html=True)
        timezone = st.selectbox(
            "Time zone",
            options=["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "Europe/London"],
            index=0,
            label_visibility="collapsed"
        )
        st.session_state.setup_data["timezone"] = timezone

def show_schedule_setup():
    """School schedule setup"""
    st.markdown("### 📅 Your School Schedule")
    st.markdown("Add your class schedule so I can help you plan study time around your classes.")
    
    # Option to upload schedule file
    st.markdown("#### 📤 Upload Schedule (Optional)")
    uploaded_file = st.file_uploader(
        "Upload your weekly schedule (CSV, Excel, or text file)",
        type=['csv', 'xlsx', 'txt'],
        help="You can upload a file with your class schedule, or enter it manually below."
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                st.success("Schedule uploaded! Review and edit below if needed.")
                st.dataframe(df)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
                st.success("Schedule uploaded! Review and edit below if needed.")
                st.dataframe(df)
            else:
                # Text file
                content = str(uploaded_file.read(), "utf-8")
                st.text_area("Schedule content:", value=content, height=200)
                st.info("I'll help you parse this schedule. For now, please enter your classes manually below.")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # Manual schedule entry
    st.markdown("#### ✏️ Enter Your Classes")
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    for day in days:
        with st.expander(f"📚 {day} Classes"):
            if day not in st.session_state.setup_data["schedule"]:
                st.session_state.setup_data["schedule"][day] = []
            
            # Add new class button
            if st.button(f"➕ Add Class", key=f"add_class_{day}"):
                st.session_state.setup_data["schedule"][day].append({
                    "subject": "",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "room": "",
                    "teacher": ""
                })
                st.rerun()
            
            # Re-apply CSS for dynamic content
            st.markdown("""
            <style>
                .stTextInput label, .stTimeInput label {
                    color: #000000 !important;
                }
                [data-testid="stWidgetLabel"] {
                    color: #000000 !important;
                }
                .stTextInput input, .stTimeInput input {
                    background-color: #ffffff !important;
                    color: #000000 !important;
                    border: 1px solid #cccccc !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Display existing classes
            for i, class_info in enumerate(st.session_state.setup_data["schedule"][day]):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.markdown('<p style="color: black; font-size: 0.875rem; margin-bottom: 0.25rem;">Subject</p>', unsafe_allow_html=True)
                    class_info["subject"] = st.text_input(
                        "Subject", 
                        value=class_info["subject"],
                        key=f"{day}_subject_{i}",
                        placeholder="Math, English, etc.",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown('<p style="color: black; font-size: 0.875rem; margin-bottom: 0.25rem;">Start</p>', unsafe_allow_html=True)
                    class_info["start_time"] = st.time_input(
                        "Start", 
                        value=time.fromisoformat(class_info["start_time"]),
                        key=f"{day}_start_{i}",
                        label_visibility="collapsed"
                    ).strftime("%H:%M")
                
                with col3:
                    st.markdown('<p style="color: black; font-size: 0.875rem; margin-bottom: 0.25rem;">End</p>', unsafe_allow_html=True)
                    class_info["end_time"] = st.time_input(
                        "End", 
                        value=time.fromisoformat(class_info["end_time"]),
                        key=f"{day}_end_{i}",
                        label_visibility="collapsed"
                    ).strftime("%H:%M")
                
                with col4:
                    st.markdown('<p style="color: black; font-size: 0.875rem; margin-bottom: 0.25rem;">Room</p>', unsafe_allow_html=True)
                    class_info["room"] = st.text_input(
                        "Room", 
                        value=class_info["room"],
                        key=f"{day}_room_{i}",
                        placeholder="101",
                        label_visibility="collapsed"
                    )
                
                with col5:
                    st.markdown('<p style="color: black; font-size: 0.875rem; margin-bottom: 0.25rem;">&nbsp;</p>', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"delete_{day}_{i}", help="Delete class"):
                        st.session_state.setup_data["schedule"][day].pop(i)
                        st.rerun()

def show_activities_setup():
    """Extracurricular activities and commitments"""
    st.markdown("### 🏃 Activities & Commitments")
    st.markdown("Tell me about your sports, clubs, music lessons, or other regular activities.")
    
    # Add new activity
    with st.expander("➕ Add New Activity"):
        col1, col2 = st.columns(2)
        
        with col1:
            activity_name = st.text_input("Activity name", placeholder="Soccer practice, Piano lessons, etc.")
            activity_type = st.selectbox(
                "Type",
                ["Sport", "Music", "Club", "Tutoring", "Family time", "Other"]
            )
        
        with col2:
            activity_days = st.multiselect(
                "Days of the week",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
            
            col_start, col_end = st.columns(2)
            with col_start:
                activity_start = st.time_input("Start time", value=time(15, 0))
            with col_end:
                activity_end = st.time_input("End time", value=time(16, 0))
        
        if st.button("Add Activity") and activity_name and activity_days:
            st.session_state.setup_data["activities"].append({
                "name": activity_name,
                "type": activity_type,
                "days": activity_days,
                "start_time": activity_start.strftime("%H:%M"),
                "end_time": activity_end.strftime("%H:%M")
            })
            st.success(f"Added {activity_name}!")
            st.rerun()
    
    # Display existing activities
    if st.session_state.setup_data["activities"]:
        st.markdown("#### Your Activities")
        for i, activity in enumerate(st.session_state.setup_data["activities"]):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{activity['name']}** ({activity['type']})")
                
                with col2:
                    days_str = ", ".join(activity['days'])
                    st.write(f"{days_str} • {activity['start_time']}-{activity['end_time']}")
                
                with col3:
                    if st.button("🗑️", key=f"delete_activity_{i}"):
                        st.session_state.setup_data["activities"].pop(i)
                        st.rerun()

def show_preferences_setup():
    """Study preferences and constraints"""
    st.markdown("### ⚙️ Study Preferences & Constraints")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🕐 Time Preferences")
        
        # Best study times
        best_times = st.multiselect(
            "When do you study best?",
            ["Early morning (6-8 AM)", "Morning (8-10 AM)", "Late morning (10-12 PM)", 
             "Afternoon (12-3 PM)", "After school (3-6 PM)", "Evening (6-9 PM)", "Night (9-11 PM)"],
            default=["After school (3-6 PM)", "Evening (6-9 PM)"]
        )
        
        # Bedtime
        bedtime = st.time_input("Bedtime", value=time(22, 0))
        
        # Screen time limits
        screen_time_start = st.time_input("Screen time starts", value=time(15, 0))
        screen_time_end = st.time_input("Screen time ends", value=time(21, 0))
        
        st.session_state.setup_data["preferences"]["best_study_times"] = best_times
        st.session_state.setup_data["preferences"]["bedtime"] = bedtime.strftime("%H:%M")
        st.session_state.setup_data["preferences"]["screen_time"] = {
            "start": screen_time_start.strftime("%H:%M"),
            "end": screen_time_end.strftime("%H:%M")
        }
    
    with col2:
        st.markdown("#### 📚 Study Preferences")
        
        # Study session length
        session_length = st.slider("Preferred study session length (minutes)", 15, 60, 30)
        
        # Break length
        break_length = st.slider("Preferred break length (minutes)", 5, 20, 10)
        
        # Notification style
        notification_style = st.selectbox(
            "How should I remind you?",
            ["Gentle nudges", "Standard reminders", "Persistent (for procrastinators)", "Minimal"]
        )
        
        # Difficulty preference
        difficulty_pref = st.selectbox(
            "How do you like to tackle hard subjects?",
            ["Break into tiny steps", "Mix easy and hard tasks", "Get hard stuff done first", "Save hard for when I'm fresh"]
        )
        
        st.session_state.setup_data["preferences"]["session_length"] = session_length
        st.session_state.setup_data["preferences"]["break_length"] = break_length
        st.session_state.setup_data["preferences"]["notification_style"] = notification_style
        st.session_state.setup_data["preferences"]["difficulty_approach"] = difficulty_pref
    
    # Do not disturb times
    st.markdown("#### 🔕 Do Not Disturb")
    st.markdown("When should I NOT send you notifications?")
    
    dnd_times = st.multiselect(
        "Quiet times",
        ["During classes", "Family dinner", "Before 7 AM", "After 9 PM", "Weekends", "Study time"],
        default=["During classes", "Before 7 AM"]
    )
    
    st.session_state.setup_data["preferences"]["do_not_disturb"] = dnd_times

def show_goals_setup():
    """Initial academic goals"""
    st.markdown("### 🎯 Your Academic Goals")
    st.markdown("What would you like to achieve this semester? I'll help you track progress!")
    
    # Goal categories
    goal_categories = {
        "📊 Grades": ["Improve math grade", "Get A's in English", "Raise overall GPA"],
        "📚 Study Habits": ["Study every day", "Finish homework before dinner", "Read 30 min daily"],
        "🧠 Skills": ["Learn better note-taking", "Improve time management", "Get better at presentations"],
        "📖 Subjects": ["Master fractions", "Improve writing", "Learn Spanish vocabulary"],
        "🏆 Achievements": ["Make honor roll", "Join academic team", "Win science fair"]
    }
    
    for category, examples in goal_categories.items():
        with st.expander(f"{category} Goals"):
            st.markdown(f"*Examples: {', '.join(examples[:2])}...*")
            
            goal_text = st.text_input(f"Add a {category.split()[1].lower()} goal", key=f"goal_{category}")
            
            col1, col2 = st.columns(2)
            with col1:
                target_date = st.date_input(f"Target date", key=f"date_{category}")
            with col2:
                importance = st.selectbox(
                    "How important?", 
                    ["Low", "Medium", "High", "Critical"],
                    index=1,
                    key=f"importance_{category}"
                )
            
            if st.button(f"Add Goal", key=f"add_{category}") and goal_text:
                st.session_state.setup_data["goals"].append({
                    "title": goal_text,
                    "category": category,
                    "target_date": target_date.isoformat(),
                    "importance": importance,
                    "progress": 0
                })
                st.success(f"Added goal: {goal_text}")
                st.rerun()
    
    # Display current goals
    if st.session_state.setup_data["goals"]:
        st.markdown("#### Your Goals")
        for i, goal in enumerate(st.session_state.setup_data["goals"]):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{goal['title']}** ({goal['category']})")
                st.write(f"Target: {goal['target_date']} • Priority: {goal['importance']}")
            
            with col2:
                st.write(f"Progress: {goal['progress']}%")
            
            with col3:
                if st.button("🗑️", key=f"delete_goal_{i}"):
                    st.session_state.setup_data["goals"].pop(i)
                    st.rerun()

def validate_setup() -> bool:
    """Validate that required setup fields are completed"""
    data = st.session_state.setup_data
    
    # Check required fields
    if not data["student_name"]:
        return False
    
    # Check that at least some schedule is entered
    has_classes = any(
        len(classes) > 0 for classes in data["schedule"].values()
    )
    
    if not has_classes:
        return False
    
    return True

def save_setup_data():
    """Save setup data to the agent's memory system"""
    try:
        # Import here to avoid circular imports
        from agent.memory import UserMemory
        
        memory = UserMemory()
        setup_data = st.session_state.setup_data
        
        # Update user profile with student information
        profile = memory.get_user_profile()
        profile.update({
            "student_name": setup_data["student_name"],
            "grade": setup_data["grade"],
            "school_name": setup_data["school_name"],
            "setup_complete": True,
            "setup_date": datetime.now().isoformat(),
            "student_mode": True,
            "preferences": setup_data["preferences"],
            "schedule": setup_data["schedule"],
            "activities": setup_data["activities"]
        })
        
        memory.update_user_profile(profile)
        
        # Add goals to the goals system
        for goal in setup_data["goals"]:
            memory.add_goal(
                title=goal["title"],
                description=f"{goal['category']} goal - Priority: {goal['importance']}",
                target_date=goal["target_date"]
            )
        
        # Add setup completion insight
        memory.add_simple_insight(f"Student setup completed for {setup_data['student_name']}, Grade {setup_data['grade']}")
        
        st.success("Setup data saved successfully!")
        
    except Exception as e:
        st.error(f"Error saving setup data: {e}")

def export_setup_data():
    """Export setup data as JSON for backup"""
    data = st.session_state.setup_data
    json_str = json.dumps(data, indent=2, default=str)
    
    st.download_button(
        label="📥 Download Setup Data",
        data=json_str,
        file_name=f"student_setup_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json"
    )

if __name__ == "__main__":
    # For testing the setup screen standalone
    st.set_page_config(
        page_title="Student Setup",
        page_icon="🎓",
        layout="wide"
    )
    
    show_student_setup()
