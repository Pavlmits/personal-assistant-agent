#!/usr/bin/env python3
"""
Streamlit Runner Script
Convenience script to run the Streamlit web interface
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit application"""
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    streamlit_app_path = os.path.join(script_dir, "streamlit_app.py")
    
    print("🚀 Starting Personal AI Agent Web Interface...")
    print("📱 The web interface will open in your browser automatically")
    print("🔗 URL: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            streamlit_app_path,
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down the web interface...")
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")
        print("\n💡 Try installing Streamlit first:")
        print("   pip install streamlit>=1.28.0")

if __name__ == "__main__":
    main()
