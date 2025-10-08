# Personal and Proactive AI Agent

A research implementation for the thesis: "Personal and Proactive Artificial Intelligence Agents with GenAI: Adaptation, Prediction, and Interaction"

## Overview

This CLI-based AI agent demonstrates:
- **Adaptation**: Learning user preferences and communication patterns
- **Prediction**: Anticipating user needs based on historical data and context  
- **Proactive Interaction**: Initiating conversations, reminders, and suggestions autonomously

## Features

### Core Capabilities
- **Personal memory and preference learning**
- **Proactive reminders and suggestions** 
- **Calendar integration** (Google Calendar)
- **Goal tracking and progress monitoring**
- **Emotional state awareness**
- **Privacy-preserving data handling**

### Hybrid Architecture (Advanced)
- **Background notification system** - OS-native notifications
- **Lightweight scheduler** - Minimal resource usage
- **On-demand AI processing** - Smart model loading
- **Local cache database** - Fast proactive checks
- **System service integration** - Auto-start on boot
- **Cross-platform support** - macOS, Linux, Windows

## Quick Start (TL;DR)

```bash
pyenv virtualenv 3.11.9 agent-assistant
pyenv local agent-assistant
pip install -r requirements.txt --index-url https://pypi.org/simple/

python main.py chat
```
## Usage

```bash
# Start interactive chat
python main.py chat
python main.py chat --verbose  # Show reasoning steps

# View available AI models
python main.py models

# Set AI model (local models recommended)
python main.py set-model llama3.1

# Setup local AI models
python main.py setup-ollama

# Set up calendar integration
python main.py setup-calendar

# View learned preferences
python main.py profile

# Enable/disable proactive features
python main.py config --proactive true

# Clean up database (fresh start)
python main.py cleanup --all          # Clear everything (with confirmation)
python main.py cleanup --goals        # Clear only goals
python main.py cleanup --conversations # Clear only conversation history
python main.py cleanup -c -g          # Clear conversations and goals

# Background notification system (advanced)
python main.py service install    # Install as system service
python main.py proactive test     # Test notifications
python main.py background-service # Run background service

# Install once
python main.py service install

# Then control it with launchctl
python main.py service start    # Start
python main.py service stop     # Stop (but stays installed)
python main.py service uninstall  # Remove completely
python main.py service status
```