#!/bin/bash
# Quick start script for Student Study Assistant

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "Starting Student Study Assistant..."
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${YELLOW}⚠ Ollama is not running. Starting it...${NC}"
    ollama serve &
    sleep 2
fi

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment not found. Run ./setup.sh first${NC}"
    exit 1
fi

# Start Streamlit
echo -e "${GREEN}✓ Starting Streamlit app...${NC}"
echo ""
python run_streamlit.py
