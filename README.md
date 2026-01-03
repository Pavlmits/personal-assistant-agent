# Student Study Assistant - AI-Powered Learning Companion

A thesis implementation: **"Personal and Proactive Artificial Intelligence Agents with GenAI: Adaptation, Prediction, and Interaction"**

## Overview

This is an AI-powered **student study assistant** built with **Streamlit** that helps students manage their academic life effectively. The system demonstrates:
- **Adaptation**: Learning student preferences and study patterns
- **Prediction**: Anticipating student needs based on schedules and behavior
- **Proactive Interaction**: Providing timely reminders, study suggestions, and support

## What It Does

The Student Study Assistant helps students with:
- 📚 **Study Planning** - Breaking down assignments into manageable study sessions
- 📅 **Schedule Management** - Tracking classes, homework deadlines, and extracurricular activities
- 🎯 **Goal Tracking** - Monitoring academic progress and achievements
- 😊 **Mood Check-ins** - Quick emotional state tracking to adjust study plans
- 📋 **Task Prioritization** - Figuring out what homework to do first
- 🔔 **Smart Reminders** - Getting nudged at the right time for study sessions

## Quick Start

### Installation

```bash
# Create virtual environment
pyenv virtualenv 3.11.9 student-assistant
pyenv local student-assistant

# Install dependencies
pip install -r requirements.txt --index-url https://pypi.org/simple/
```

### Running the Application

```bash
# Start the web interface (recommended)
python run_streamlit.py

# Or directly with streamlit
streamlit run streamlit_app.py
```

The web application will open at `http://localhost:8501`

## Features

### Student-Focused Capabilities
- **Interactive Setup** - First-time setup wizard to configure student profile (name, grade, subjects)
- **Study Dashboard** - Visual overview of upcoming classes, assignments, and goals
- **AI Chat Assistant** - Natural language interface to ask questions and get help
- **Calendar Integration** - Sync with Google Calendar for class schedules and deadlines
- **Mood Tracking** - Quick check-ins to adjust study recommendations
- **Goal Management** - Set and track academic goals with progress monitoring

### Technical Features
- **Memory System** - Learns from student interactions to provide personalized suggestions
- **Proactive Notifications** - Sends timely reminders for study sessions and deadlines
- **Multiple AI Models** - Support for both local (Ollama) and cloud-based (OpenAI, Anthropic) models
- **Privacy-Preserving** - All student data stored locally in SQLite database
- **Responsive Design** - Works on desktop, tablet, and mobile devices

## AI Model Configuration

The assistant supports multiple AI models:

### Local Models (Recommended for Privacy)
Using Ollama for completely local, private AI:

1. **Install Ollama**:
   - Mac: Download from [ollama.ai](https://ollama.ai) or `brew install ollama`
   - Other platforms: See [ollama.ai/download](https://ollama.ai/download)

2. **Start Ollama**:
   ```bash
   ollama serve
   ```

3. **Download a model**:
   ```bash
   ollama pull llama3.1  # Recommended - 4.7GB
   # or
   ollama pull mistral   # Fast alternative - 4.1GB
   ```

### Cloud Models
Configure API keys in your environment or through the web interface:
- **OpenAI** - Set `OPENAI_API_KEY`
- **Anthropic Claude** - Set `ANTHROPIC_API_KEY`

The assistant will automatically detect available models and use the best one available.

## Google Calendar Integration (Optional)

To enable calendar integration for class schedules and deadlines:

1. Create a Google Cloud Project and enable the Calendar API
2. Download OAuth credentials as `credentials.json` in the project root
3. On first use, you'll be prompted to authorize the application
4. The system will create `token.pickle` for subsequent access

## Project Structure

```
student-assistant/
├── streamlit_app.py          # Main Streamlit web interface
├── run_streamlit.py          # Streamlit launcher script
├── student_setup.py          # First-time student setup wizard
├── requirements.txt          # Python dependencies
├── agent/                    # Core agent functionality
│   ├── langchain_agent.py    # Main LangChain agent implementation
│   ├── memory.py             # User memory and learning system
│   ├── student_tools.py      # Student-specific tools
│   ├── model_manager.py      # AI model configuration
│   ├── proactive_manager.py  # Proactive notification system
│   ├── notification_system.py # OS notification integration
│   └── clients/
│       └── calendar_integration.py  # Google Calendar integration
├── credentials.json          # Google Calendar OAuth (if using calendar)
├── token.pickle              # Google Calendar auth token (generated)
├── agent_cache.db            # Cache database for fast lookups
└── user_memory.db            # Student data and learning history
```

## Thesis Context

This application is part of a thesis exploring:

### Research Questions
1. How can AI agents adapt to individual student learning patterns?
2. What makes proactive assistance effective for academic success?
3. How can AI systems predict student needs before they're explicitly stated?

### Key Research Areas
- **Personalization** - Learning individual student preferences, study habits, and communication styles
- **Proactive Intelligence** - Anticipating needs based on calendar, goals, and behavioral patterns
- **Educational Technology** - Applying AI to improve student outcomes and reduce academic stress
- **Privacy-Preserving AI** - Demonstrating that powerful personalization can work with local-only data

### Evaluation Metrics
The system tracks various metrics for research purposes:
- **Adaptation**: How quickly the system learns student preferences
- **Prediction Accuracy**: How often proactive suggestions are relevant and timely
- **Student Engagement**: Interaction frequency and satisfaction
- **Academic Outcomes**: Correlation with improved study habits and goal completion

## Data Privacy

All student data is stored **locally** in SQLite databases:
- `user_memory.db` - Student profile, conversations, goals, and learning history
- `agent_cache.db` - Cached data for faster proactive checks

**No data is sent to external servers** except:
- AI model API calls (if using cloud models like OpenAI/Anthropic)
- Google Calendar API (if calendar integration is enabled)

For maximum privacy, use local Ollama models and skip calendar integration.

## Development

### Dependencies
Key Python packages:
- `streamlit>=1.28.0` - Web interface framework
- `langchain>=0.1.0` - LLM orchestration and agent framework
- `langchain-community` - Community integrations
- `ollama` - Local model support
- `google-api-python-client` - Google Calendar integration
- `rich` - Terminal formatting (for scripts)

### Database Schema
The system uses SQLite for data persistence:
- **User Profile** - Student information, preferences, learning patterns
- **Conversations** - Chat history for context and learning
- **Goals** - Academic goals with progress tracking
- **Insights** - Learned patterns and preferences
- **Notifications** - Proactive notification history

## Acknowledgments

This thesis implementation builds on:
- **LangChain** - For agent orchestration and tool integration
- **Streamlit** - For rapid web application development
- **Ollama** - For privacy-preserving local AI models
- Research in proactive AI systems, personalized learning, and educational technology

## License

This is a research project developed as part of a thesis. For academic and educational purposes.

---

**Thesis Author**: Pavlina Mitsou
**Project Type**: Streamlit Web Application
**Focus**: AI-Powered Student Study Assistant with Proactive Features
