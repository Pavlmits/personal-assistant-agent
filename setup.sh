#!/bin/bash
# Quick Setup Script for Student Study Assistant (Local Deployment)

set -e  # Exit on error

echo "=================================="
echo "Student Study Assistant Setup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $python_version found${NC}"
echo ""

# Check if Ollama is installed
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"

    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓ Ollama is running${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama is not running. Starting it...${NC}"
        ollama serve &
        sleep 2
        echo -e "${GREEN}✓ Ollama started${NC}"
    fi

    # Check if llama3.1 is downloaded
    echo ""
    echo "Checking for Llama 3.1 model..."
    if ollama list | grep -q "llama3.1"; then
        echo -e "${GREEN}✓ Llama 3.1 model is already downloaded${NC}"
    else
        echo -e "${YELLOW}⚠ Llama 3.1 not found. Downloading (this will take 5-10 minutes)...${NC}"
        ollama pull llama3.1
        echo -e "${GREEN}✓ Llama 3.1 downloaded successfully${NC}"
    fi
else
    echo -e "${RED}✗ Ollama is not installed${NC}"
    echo ""
    echo "Please install Ollama first:"
    echo "  Mac:     brew install ollama"
    echo "  Other:   Visit https://ollama.ai"
    echo ""
    exit 1
fi

echo ""
echo "Installing Python dependencies..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing packages from requirements.txt..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓ All dependencies installed${NC}"

echo ""
echo "=================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=================================="
echo ""
echo "To start the application:"
echo "  1. source .venv/bin/activate"
echo "  2. python run_streamlit.py"
echo ""
echo "Or use the quick start script:"
echo "  ./start.sh"
echo ""
echo "For thesis demo, see: THESIS_DEMO_GUIDE.md"
echo ""
