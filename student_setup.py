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

# Apply consistent dark text styling for all elements
st.markdown("""
<style>
    /* Application base */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    
    .main .block-container {
        background-color: #ffffff;
        color: #ffffff;
    }
    
    /* Text elements */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #000000;
    }
    
    /* Tab navigation */
    .stTabs [data-baseweb="tab-list"] button,
    .stTabs [data-baseweb="tab-list"] button *,
    [role="tablist"], [role="tablist"] *,
    [role="tab"], [role="tab"] *,
    [data-baseweb="tab"], [data-baseweb="tab"] *,
    [data-baseweb="tab-list"], [data-baseweb="tab-list"] * {
        color: #000000;
        -webkit-text-fill-color: #000000;
    }
    
    /* Input fields */
    input, select, textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    input:focus, input:active, input:hover,
    select:focus, select:active, select:hover,
    textarea:focus, textarea:active, textarea:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Dropdown menu options */
    select option {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Streamlit selectbox dropdown - comprehensive targeting */
    .stSelectbox [data-baseweb="popover"],
    .stSelectbox [data-baseweb="popover"] *,
    .stSelectbox [role="listbox"],
    .stSelectbox [role="listbox"] *,
    .stSelectbox [role="option"],
    .stSelectbox [role="option"] *,
    .stSelectbox ul,
    .stSelectbox ul *,
    .stSelectbox li,
    .stSelectbox li * {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Selectbox menu - all variations */
    [data-baseweb="menu"],
    [data-baseweb="menu"] *,
    [data-baseweb="popover"],
    [data-baseweb="popover"] *,
    [data-baseweb="select"],
    [data-baseweb="select"] * {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* List items in dropdown */
    [role="listbox"],
    [role="listbox"] *,
    [role="option"],
    [role="option"] * {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Hover state for dropdown items */
    [role="option"]:hover,
    [role="option"]:hover *,
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] li:hover * {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
    }
    
    /* Placeholder text */
    input::placeholder, textarea::placeholder {
        color: #999999 !important;
        -webkit-text-fill-color: #999999 !important;
    }
    
    /* Ensure typed text stays black */
    input:not(:placeholder-shown),
    textarea:not(:placeholder-shown) {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Streamlit specific inputs */
    [data-testid="stTextInput"] input,
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextInput"] input:active,
    [data-testid="stSelectbox"] select,
    [data-testid="stTimeInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* Widget labels */
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] * {
        color: #000000 !important;
    }
    
    /* Buttons */
    .stButton > button {
        color: #ffffff;
        background-color: #007bff;
        border: none;
        border-radius: 5px;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        color: #000000;
    }
    
    /* File uploader */
    .stFileUploader > div {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
    }
    
    /* Ensure consistent text color */
    * {
        color: #000000 !important;
    }
    
    /* Exception: buttons should have white text */
    .stButton > button,
    button[kind="primary"],
    button[kind="secondary"] {
        color: #ffffff !important;
    }
    
    /* Override for input text specifically */
    input, select, textarea,
    input *, select *, textarea * {
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
            "grade": "1st Junior High School",
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
    
    # Re-apply CSS for dynamic content after every interaction
    st.markdown("""
    <style>
        /* Reapply all critical styling */
        * {
            color: #000000 !important;
        }
        
        .stButton > button,
        button[kind="primary"],
        button[kind="secondary"] {
            color: #ffffff !important;
        }
        
        input, select, textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #cccccc !important;
            -webkit-text-fill-color: #000000 !important;
        }
        
        input:focus, select:focus, textarea:focus,
        input:active, select:active, textarea:active {
            background-color: #ffffff !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }
        
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] * {
            color: #000000 !important;
        }
        
        .stTabs [data-baseweb="tab-list"] button,
        .stTabs [data-baseweb="tab-list"] button *,
        [role="tablist"], [role="tablist"] *,
        [role="tab"], [role="tab"] * {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
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
        
        grade_options = [
            "1st Junior High School",
            "2nd Junior High School", 
            "3rd Junior High School",
            "1st High School",
            "2nd High School",
            "3rd High School"
        ]
        
        # Find current index, default to 0 if not found
        try:
            current_index = grade_options.index(st.session_state.setup_data["grade"])
        except (ValueError, KeyError):
            current_index = 0
            st.session_state.setup_data["grade"] = grade_options[0]
        
        st.session_state.setup_data["grade"] = st.selectbox(
            "What grade are you in?",
            options=grade_options,
            index=current_index,
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

def show_schedule_setup():
    """School schedule setup"""
    st.markdown("### 📅 Your School Schedule")
    st.markdown("Add your class schedule so I can help you plan study time around your classes.")
    
    # File upload option
    st.markdown("#### 📤 Upload Schedule (Optional)")
    uploaded_file = st.file_uploader(
        "Upload your weekly schedule (CSV, Excel, or image)",
        type=['csv', 'xlsx', 'png', 'jpg', 'jpeg'],
        help="You can upload a file with your class schedule, or enter it manually below."
    )
    
    if uploaded_file is not None:
        st.success("Schedule uploaded! You can review and edit below if needed.")
    
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
                    "room": ""
                })
                st.rerun()
            
            # Display existing classes
            for i, class_info in enumerate(st.session_state.setup_data["schedule"][day]):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.markdown('<p style="color: black; font-size: 0.875rem; margin-bottom: 0.25rem;">Subject</p>', unsafe_allow_html=True)
                    class_info["subject"] = st.text_input(
                        "Subject", 
                        value=class_info["subject"],
                        key=f"{day}_subject_{i}",
                        placeholder="Math, Greek, etc.",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown('<p style="color: white; font-size: 0.875rem; margin-bottom: 0.25rem;">Start</p>', unsafe_allow_html=True)
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
    with st.expander("➕ Add New Activity", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            activity_name = st.text_input("Activity name", placeholder="Soccer practice, Piano lessons, etc.", key="new_activity_name")
            activity_type = st.selectbox(
                "Type",
                ["Sport", "Music", "Club", "Tutoring", "Family time", "Other"],
                key="new_activity_type"
            )
        
        with col2:
            activity_days = st.multiselect(
                "Days of the week",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                key="new_activity_days"
            )
            
            col_start, col_end = st.columns(2)
            with col_start:
                activity_start = st.time_input("Start time", value=time(15, 0), key="new_activity_start")
            with col_end:
                activity_end = st.time_input("End time", value=time(16, 0), key="new_activity_end")
        
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
            default=st.session_state.setup_data["preferences"].get("best_study_times", ["After school (3-6 PM)", "Evening (6-9 PM)"])
        )
        
        # Bedtime
        bedtime_value = st.session_state.setup_data["preferences"].get("bedtime", "22:00")
        bedtime = st.time_input("Bedtime", value=time.fromisoformat(bedtime_value))
        
        # Screen time limits
        screen_start_value = st.session_state.setup_data["preferences"].get("screen_time", {}).get("start", "15:00")
        screen_end_value = st.session_state.setup_data["preferences"].get("screen_time", {}).get("end", "21:00")
        
        screen_time_start = st.time_input("Screen time starts", value=time.fromisoformat(screen_start_value))
        screen_time_end = st.time_input("Screen time ends", value=time.fromisoformat(screen_end_value))
        
        st.session_state.setup_data["preferences"]["best_study_times"] = best_times
        st.session_state.setup_data["preferences"]["bedtime"] = bedtime.strftime("%H:%M")
        st.session_state.setup_data["preferences"]["screen_time"] = {
            "start": screen_time_start.strftime("%H:%M"),
            "end": screen_time_end.strftime("%H:%M")
        }
    
    with col2:
        st.markdown("#### 📚 Study Preferences")
        
        # Study session length
        session_length = st.slider(
            "Preferred study session length (minutes)", 
            15, 60, 
            st.session_state.setup_data["preferences"].get("session_length", 30)
        )
        
        # Break length
        break_length = st.slider(
            "Preferred break length (minutes)", 
            5, 20, 
            st.session_state.setup_data["preferences"].get("break_length", 10)
        )
        
        # Notification style
        notification_style = st.selectbox(
            "How should I remind you?",
            ["Gentle nudges", "Standard reminders", "Persistent (for procrastinators)", "Minimal"],
            index=["Gentle nudges", "Standard reminders", "Persistent (for procrastinators)", "Minimal"].index(
                st.session_state.setup_data["preferences"].get("notification_style", "Standard reminders")
            )
        )
        
        # Difficulty preference
        difficulty_pref = st.selectbox(
            "How do you like to tackle hard subjects?",
            ["Break into tiny steps", "Mix easy and hard tasks", "Get hard stuff done first", "Save hard for when I'm fresh"],
            index=["Break into tiny steps", "Mix easy and hard tasks", "Get hard stuff done first", "Save hard for when I'm fresh"].index(
                st.session_state.setup_data["preferences"].get("difficulty_approach", "Break into tiny steps")
            )
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
        default=st.session_state.setup_data["preferences"].get("do_not_disturb", ["During classes", "Before 7 AM"])
    )
    
    st.session_state.setup_data["preferences"]["do_not_disturb"] = dnd_times

def show_goals_setup():
    """Initial academic goals"""
    st.markdown("### 🎯 Your Academic Goals")
    st.markdown("What would you like to achieve this semester? I'll help you track progress!")
    
    # Add new goal
    with st.expander("➕ Add New Goal", expanded=True):
        goal_text = st.text_input("What's your goal?", placeholder="e.g., Improve my math grade", key="new_goal_text")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            goal_category = st.selectbox(
                "Category",
                ["📊 Grades", "📚 Study Habits", "🧠 Skills", "📖 Subjects", "🏆 Achievements"],
                key="new_goal_category"
            )
        
        with col2:
            target_date = st.date_input("Target date", key="new_goal_date")
        
        with col3:
            importance = st.selectbox(
                "How important?", 
                ["Low", "Medium", "High", "Critical"],
                index=1,
                key="new_goal_importance"
            )
        
        if st.button("Add Goal") and goal_text:
            st.session_state.setup_data["goals"].append({
                "title": goal_text,
                "category": goal_category,
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
    else:
        st.info("No goals added yet. Add your first goal above!")

def validate_setup() -> bool:
    """Validate setup data"""
    data = st.session_state.setup_data
    return bool(data["student_name"])

def save_setup_data():
    """Save setup data"""
    try:
        from agent.memory import UserMemory
        memory = UserMemory()
        setup_data = st.session_state.setup_data
        profile = memory.get_user_profile()
        profile.update({
            "student_name": setup_data["student_name"],
            "grade": setup_data["grade"],
            "school_name": setup_data["school_name"],
            "setup_complete": True,
            "setup_date": datetime.now().isoformat(),
            "student_mode": True
        })
        memory.update_user_profile(profile)
        st.success("Setup data saved successfully!")
    except Exception as e:
        st.error(f"Error saving setup data: {e}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Student Setup",
        page_icon="🎓",
        layout="wide"
    )
    show_student_setup()

