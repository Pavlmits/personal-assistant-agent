# Thesis Demo Guide - Student Study Assistant

## Quick Overview

This guide will help you set up and demo the **Student Study Assistant** for your thesis committee. Everything runs **locally on your laptop** - no internet required (except for downloading models).

## What You'll Demo

A working AI-powered study assistant that:
- ✅ Helps students plan their study sessions
- ✅ Tracks academic goals and progress
- ✅ Integrates with Google Calendar (optional)
- ✅ Learns student preferences over time
- ✅ Provides proactive study reminders
- ✅ Uses **local AI** (Ollama) for privacy

## Pre-Demo Setup Checklist

### 1. Install Ollama and Download Model (One-time, 10 minutes)

```bash
# Install Ollama (Mac)
brew install ollama

# OR download from https://ollama.ai

# Start Ollama
ollama serve &

# Download Llama 3.1 (4.7GB - takes 5-10 min on good internet)
ollama pull llama3.1

# Verify it works
ollama list
```

Expected output:
```
NAME            ID              SIZE
llama3.1:latest abc123def456   4.7GB
```

### 2. Set Up Python Environment (5 minutes)

```bash
# Navigate to project
cd /path/to/personal-assistant-agent

# Create virtual environment
pyenv virtualenv 3.11.9 student-assistant
pyenv local student-assistant

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import streamlit; print(f'Streamlit {streamlit.__version__} installed')"
```

### 3. Test the Application (2 minutes)

```bash
# Start the app
python run_streamlit.py

# Should open browser at http://localhost:8501
# You should see the student setup wizard
```

### 4. Create Demo Student Profile (2 minutes)

On first run, fill out the setup wizard:
- **Student Name**: Demo Student (or your name)
- **Grade**: 12 (or any grade)
- **Subjects**: Math, Physics, Computer Science
- **Study Hours**: 9:00 - 11:00 (or your preference)

Click "Complete Setup" and you're ready!

## Demo Script for Committee

### Introduction (1 minute)

> "I've developed an AI-powered study assistant designed to help students manage their academic workload more effectively. The system demonstrates three key capabilities: adaptation, prediction, and proactive interaction."

### Demo Flow (10-15 minutes)

#### Part 1: Basic Interaction (3 minutes)

**Show the interface:**
- Point out the clean, student-friendly UI
- Show the sidebar with student profile and goals

**Demo conversation:**
```
You: "Hi! I have a math test next Friday. Can you help me prepare?"

Agent: [Shows response with study plan]

You: "I also have a physics assignment due in 3 days."

Agent: [Helps prioritize and create schedule]
```

**Highlight:**
- Natural language understanding
- Context awareness (remembers previous messages)
- Tool usage indicators (shows which tools the agent used)

#### Part 2: Goal Tracking (3 minutes)

**Create a goal:**
```
You: "I want to improve my math grade from B to A by the end of semester"
```

**Show:**
- Goal appears in sidebar
- Progress tracking
- Agent references goal in future conversations

**Highlight:**
- Persistent memory across sessions
- Goal-oriented assistance
- Progress monitoring

#### Part 3: Adaptation & Learning (3 minutes)

**Show profile sidebar:**
- Communication style learned
- Active hours detected
- Interest areas identified

**Demo adaptation:**
```
You: "Keep responses brief please, I'm in a hurry"

[Agent adapts to shorter responses]

You: "Actually, I prefer detailed explanations"

[Agent switches to longer, more detailed responses]
```

**Highlight:**
- Learning from interaction patterns
- Preference adaptation
- Stored in local SQLite database

#### Part 4: Calendar Integration (2 minutes - Optional)

If you set up Google Calendar:

**Show:**
```
You: "What classes do I have today?"

Agent: [Lists classes from Google Calendar]

You: "When is my next assignment due?"

Agent: [Checks calendar for deadlines]
```

**Highlight:**
- Real-world integration
- Automatic deadline tracking

#### Part 5: Privacy & Architecture (2 minutes)

**Show the backend:**
- Open `user_memory.db` in DB Browser for SQLite
- Show conversations, goals, profile tables
- Emphasize: All data stays local, never sent to cloud

**Explain:**
- Uses Ollama (local LLM) - no data leaves your computer
- SQLite for data storage
- Privacy-preserving design

### Q&A Preparation

#### Expected Questions & Answers

**Q: Why use local models instead of GPT-4?**
> A: Privacy and cost. Student data stays on their device, no recurring API costs, works offline. Perfect for educational use. I could switch to GPT-4 with minimal code changes if needed.

**Q: How does the learning/adaptation work?**
> A: The system tracks interaction patterns, communication preferences, and topics of interest. It stores insights in a learning database and adjusts responses based on confidence levels. For example, if a student consistently asks questions at 9 AM, the system learns this is their active study time.

**Q: Can multiple students use this?**
> A: Current version is single-user (ideal for personal laptop deployment). For school-wide deployment, I'd need to add user authentication and migrate to PostgreSQL. The architecture supports this with minimal changes.

**Q: What about scalability?**
> A: For 1-10 users: Current SQLite setup works perfectly. For 50+ users: Would migrate to PostgreSQL and deploy on a server. For 500+: Would add Redis caching and load balancing. The system is designed with these tiers in mind.

**Q: How accurate is the AI?**
> A: Llama 3.1 8B performs well for study assistance tasks. For critical academic content, I recommend students verify information. The system focuses on study planning and organization rather than providing factual answers.

**Q: What happens if the student closes the app?**
> A: All data persists in SQLite databases. When they return, the agent remembers their goals, preferences, and conversation history. Session continuity is maintained.

**Q: Could this work for different subjects/grade levels?**
> A: Absolutely. The student setup wizard customizes the experience. The agent adapts to different subjects and academic levels through its learning system.

## Technical Details to Mention

### Architecture Highlights

```
Frontend (Streamlit)
    ↓
Agent Layer (LangChain)
    ↓
Tools: [Calendar, Goals, Memory, Notifications]
    ↓
Storage (SQLite) | LLM (Ollama - Llama 3.1)
```

### Key Technologies

- **Streamlit**: Web interface framework
- **LangChain**: Agent orchestration and tool calling
- **Ollama + Llama 3.1**: Local LLM (privacy-preserving)
- **SQLite**: Lightweight database (perfect for single-user)
- **Google Calendar API**: Optional calendar integration

### Research Contributions

1. **Privacy-preserving personalization**: Demonstrates that effective AI assistance doesn't require cloud processing
2. **Student-focused UX**: Designed specifically for academic use cases
3. **Proactive assistance**: System can anticipate needs rather than just responding
4. **Transparent learning**: Students can see what the system learns about them

## Troubleshooting Before Demo

### Test 1: Ollama is Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If error, start Ollama
ollama serve &
```

### Test 2: Database is Working

```bash
# Check databases exist
ls -lh *.db

# Should see:
# user_memory.db
# agent_cache.db
```

### Test 3: App Starts Without Errors

```bash
# Run app
python run_streamlit.py

# Watch terminal for errors
# Should see: "You can now view your Streamlit app in your browser"
```

### Common Issues

**"Ollama connection error"**
- Solution: `ollama serve` in a terminal and keep it running

**"Model not found"**
- Solution: `ollama pull llama3.1`

**"Port 8501 already in use"**
- Solution: Kill other Streamlit processes: `pkill -f streamlit`

**"Database locked"**
- Solution: Close any DB browser tools, restart app

## Demo Day Checklist

**Night Before:**
- [ ] Full system test
- [ ] Ollama model downloaded and tested
- [ ] Demo student profile created with sample data
- [ ] Laptop fully charged
- [ ] Backup: Screenshots of working app (in case of live demo issues)

**Morning Of:**
- [ ] Start Ollama: `ollama serve`
- [ ] Test app: `python run_streamlit.py`
- [ ] Do a practice run-through
- [ ] Close unnecessary apps (for performance)

**During Presentation:**
- [ ] Disable notifications/alerts on laptop
- [ ] Turn off WiFi (to show it works offline) - optional but impressive
- [ ] Have terminal window visible (shows local execution)
- [ ] Keep this guide open for reference

## Backup Plan

If live demo fails (Murphy's Law):

1. **Screenshots**: Have screenshots of each feature ready
2. **Video**: Record a 5-minute video walkthrough beforehand
3. **Code walkthrough**: Show the code and explain architecture instead

## After Demo - Cleanup

```bash
# Stop Ollama
pkill ollama

# Stop Streamlit
pkill -f streamlit

# Keep databases for future demos
# To reset data:
# rm user_memory.db agent_cache.db
```

## Extending for Committee Questions

If they want to see code:

**Show key files:**
1. `streamlit_app.py` - Main interface (lines 172-232: chat logic)
2. `agent/langchain_agent.py` - Agent implementation
3. `agent/memory.py` - Learning system
4. `agent/student_tools.py` - Student-specific tools

**Database schema:**
```bash
# Open database in browser
sqlite3 user_memory.db

# Show tables
.tables

# Show sample data
SELECT * FROM user_profile LIMIT 5;
SELECT * FROM goals;
SELECT * FROM conversations LIMIT 10;
```

## Presentation Tips

1. **Keep it student-focused**: Emphasize how it helps students, not just technical features
2. **Show, don't tell**: Live interaction is more impressive than explaining
3. **Highlight privacy**: Local execution is a unique selling point
4. **Be honest about limitations**: Mention what would be needed for production
5. **Connect to research questions**: Tie features back to adaptation/prediction/interaction

## Time Allocation

- Setup/Introduction: 2 min
- Live Demo: 10 min
- Architecture Explanation: 3 min
- Q&A: 10-15 min
- **Total: 25-30 minutes**

---

**Good luck with your thesis defense! 🎓**

You've built a working, privacy-preserving AI study assistant. That's impressive.
