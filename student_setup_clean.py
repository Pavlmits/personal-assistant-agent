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
        color: #000000;
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
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
        -webkit-text-fill-color: #000000;
    }
    
    input:focus, select:focus, textarea:focus {
        background-color: #ffffff;
        color: #000000;
        -webkit-text-fill-color: #000000;
    }
    
    /* Placeholder text */
    input::placeholder, textarea::placeholder {
        color: #999999;
        -webkit-text-fill-color: #999999;
    }
    
    /* Widget labels */
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] * {
        color: #000000;
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
        color: #000000;
    }
    
    /* Exception: buttons should have white text */
    .stButton > button,
    button[kind="primary"],
    button[kind="secondary"] {
        color: #ffffff;
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
    
    # Re-apply CSS for dynamic content
    st.markdown("""
    <style>
        .stTextInput label, .stSelectbox label {
            color: #000000;
        }
        [data-testid="stWidgetLabel"] {
            color: #000000;
        }
        .stTextInput input, .stSelectbox select {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            -webkit-text-fill-color: #000000;
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
    """School schedule setup - placeholder"""
    st.markdown("### 📅 Your School Schedule")
    st.info("Schedule setup coming soon!")

def show_activities_setup():
    """Activities setup - placeholder"""
    st.markdown("### 🏃 Activities & Commitments")
    st.info("Activities setup coming soon!")

def show_preferences_setup():
    """Preferences setup - placeholder"""
    st.markdown("### ⚙️ Study Preferences & Constraints")
    st.info("Preferences setup coming soon!")

def show_goals_setup():
    """Goals setup - placeholder"""
    st.markdown("### 🎯 Your Academic Goals")
    st.info("Goals setup coming soon!")

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


