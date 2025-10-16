#!/usr/bin/env python3
"""
Demo script for the Streamlit Web Interface
Shows how to launch and use the web interface
"""

import subprocess
import sys
import time
import webbrowser
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    """Demo the Streamlit web interface"""
    
    console.print(Panel(
        "[bold blue]🌐 Personal AI Agent - Web Interface Demo[/bold blue]\n\n"
        "[bold]What you'll see:[/bold]\n"
        "• Modern chat interface with your AI agent\n"
        "• Real-time agent status and capabilities\n"
        "• Your learned user profile and preferences\n"
        "• Goal tracking with progress bars\n"
        "• Tool usage indicators\n"
        "• Model switching capabilities\n"
        "• Quick action buttons\n\n"
        "[bold yellow]Features:[/bold yellow]\n"
        "✅ All your existing agent functionality\n"
        "✅ Visual dashboard and metrics\n"
        "✅ Responsive design (works on mobile)\n"
        "✅ Session persistence\n"
        "✅ Real-time updates\n\n"
        "[dim]The web interface will launch at http://localhost:8501[/dim]",
        title="🚀 Streamlit Demo"
    ))
    
    # Check if streamlit is installed
    try:
        import streamlit
        console.print("[green]✓ Streamlit is installed[/green]")
    except ImportError:
        console.print("[red]✗ Streamlit not found. Installing...[/red]")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit>=1.28.0"])
    
    console.print("\n[blue]Starting the web interface...[/blue]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")
    
    # Wait a moment
    time.sleep(2)
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "run_streamlit.py"
        ])
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo stopped. Thanks for trying the web interface![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]You can also run it manually with:[/yellow]")
        console.print("[cyan]python run_streamlit.py[/cyan]")
        console.print("[cyan]streamlit run streamlit_app.py[/cyan]")

if __name__ == "__main__":
    main()
