#!/usr/bin/env python3
"""
Personal and Proactive AI Agent
Thesis Implementation: Adaptation, Prediction, and Interaction
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
import sys
import time
from typing import Optional

from agent.langchain_agent import LangChainPersonalAgent
from agent.memory import UserMemory
from agent.clients.calendar_integration import CalendarManager
from agent.model_manager import ModelManager
from agent.proactive_manager import ProactiveManager, ProactiveConfig
from agent.system_service import SystemServiceManager
from agent.notification_system import NotificationSystem

app = typer.Typer(help="Personal and Proactive AI Agent for Thesis Research")
console = Console()

# Global agent instance
agent = None

def initialize_agent():
    """Initialize the LangChain agent with all components"""
    global agent
    if agent is None:
        return initialize_langchain_agent()
    return agent

def initialize_langchain_agent():
    """Initialize the LangChain agent with all components"""
    console.print("[blue]Initializing Personal AI Agent...[/blue]")
    
    # Initialize components
    memory = UserMemory()
    calendar_mgr = CalendarManager()
    model_mgr = ModelManager()
    notification_system = NotificationSystem()
    
    # Setup default model if none selected
    current_model = model_mgr.setup_default_model()
    if current_model:
        console.print(f"[green]✓ Using model: {model_mgr.get_current_model().name}[/green]")
    else:
        console.print("[yellow]⚠ No AI models available - agent may not work properly[/yellow]")
    
    try:
        # Create LangChain agent
        agent = LangChainPersonalAgent(
            memory=memory,
            calendar_manager=calendar_mgr,
            model_manager=model_mgr,
            notification_system=notification_system
        )
        
        # Initialize proactive manager for background notifications
        proactive_config = ProactiveConfig(
            enabled=True,
            check_interval=900,  # 15 minutes
            max_notifications_per_hour=6,
            learning_enabled=True,
            calendar_integration=calendar_mgr.is_available(),
            goal_tracking=True,
            pattern_analysis=True
        )
        
        agent.proactive_manager = ProactiveManager(
            memory=memory,
            calendar_manager=calendar_mgr,
            config=proactive_config,
            agent=agent
        )
        
        console.print("[green]✓ Agent initialized successfully[/green]")
        return agent
        
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize agent: {e}[/red]")
        raise

def show_agent_status(agent):
    """Show agent status information"""
    status = agent.get_agent_status()
    
    table = Table(title="🤖 Agent Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Agent Type", status['agent_type'])
    table.add_row("Model", f"{status['model']['name']} ({status['model']['provider']})")
    table.add_row("Local Model", "✅ Yes" if status['model']['local'] else "❌ No")
    table.add_row("Tools Available", str(status['tools_available']))
    table.add_row("Memory Enabled", "✅ Yes" if status['memory_enabled'] else "❌ No")
    table.add_row("Proactive Enabled", "✅ Yes" if status['proactive_enabled'] else "❌ No")
    table.add_row("Total Interactions", str(status['total_interactions']))
    
    console.print(table)
    
    # Show available tools
    console.print(f"\n[cyan]Available Tools:[/cyan]")
    for tool_name in status['tool_names']:
        console.print(f"  • {tool_name}")

@app.command()
def chat(
    save_session: bool = typer.Option(True, help="Save conversation to memory"),
    verbose: bool = typer.Option(False, help="Show agent reasoning steps")
):
    """Start an interactive chat session with the AI agent"""
    agent = initialize_agent()
    
    # Show current model info
    status = agent.get_agent_status()
    console.print(Panel(
        f"[bold blue]Personal AI Agent[/bold blue]\n"
        f"[dim]Model: {status['model']['name']} ({status['model']['provider']})[/dim]\n"
        f"[dim]Tools Available: {status['tools_available']} ({', '.join(status['tool_names'][:3])}...)[/dim]\n\n"
        "I'm your AI agent with reasoning capabilities and access to tools.\n"
        "I can search your calendar, manage goals, access memory, and take actions.\n"
        "[dim]Type 'quit' to exit, 'help' for commands[/dim]",
        title="🤖 Agent Ready"
    ))
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                console.print("[blue]Goodbye! I'll remember our conversation.[/blue]")
                break
            elif user_input.lower() == 'help':
                show_help()
                continue
            elif user_input.lower() == 'status':
                show_agent_status(agent)
                continue
            
            # Process user input with LangChain agent
            with console.status("[bold blue]Agent thinking...", spinner="dots"):
                result = agent.process_message(user_input, save_to_memory=save_session)
            
            if result['success']:
                console.print(f"\n[bold blue]Agent[/bold blue]: {result['response']}")
                
                # Show intermediate steps if verbose
                if verbose and result['intermediate_steps']:
                    console.print("\n[dim cyan]🔧 Tools Used:[/dim cyan]")
                    for i, (action, observation) in enumerate(result['intermediate_steps'], 1):
                        console.print(f"[dim]  {i}. {action.tool}: {action.tool_input}[/dim]")
            else:
                console.print(f"\n[red]Error: {result['response']}[/red]")
                        
        except KeyboardInterrupt:
            console.print("\n[blue]Session paused. Type 'quit' to exit properly.[/blue]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def models():
    """View and manage AI models"""
    agent = initialize_agent()
    show_models_info(agent.model_manager)

def show_models_info(model_mgr):
    """Display model information"""
    status = model_mgr.get_model_status()
    current_config = status['current_model_info']
    
    # Show current model
    console.print(Panel(
        f"[bold]Current Model:[/bold] {current_config.name}\n"
        f"[bold]Provider:[/bold] {current_config.provider.value}\n"
        f"[bold]Local:[/bold] {'Yes' if current_config.local else 'No'}\n"
        f"[bold]Description:[/bold] {current_config.description}",
        title="🤖 Current AI Model"
    ))
    
    # Show available models
    table = Table(title="Available Models")
    table.add_column("Key", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Provider", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Type", style="blue")
    
    for key, model_info in status['available_models'].items():
        status_emoji = "✅" if model_info['available'] else "❌"
        type_label = "Local" if model_info['local'] else "Cloud"
        
        table.add_row(
            key,
            model_info['name'],
            model_info['provider'],
            status_emoji,
            type_label
        )
    
    console.print(table)
    
    # Show provider status
    console.print("\n[cyan]Provider Status:[/cyan]")
    for provider, available in status['providers_status'].items():
        status_emoji = "✅" if available else "❌"
        console.print(f"  {status_emoji} {provider.title()}")
    
    # Show setup instructions if no local models available
    if not status['providers_status'].get('ollama', False):
        console.print("\n[yellow]💡 Tip: Install Ollama for free local AI models![/yellow]")
        console.print("Run: [cyan]python main.py setup-ollama[/cyan] for instructions")

@app.command()
def set_model(model_key: str = typer.Argument(..., help="Model key to use")):
    """Set the AI model to use"""
    agent = initialize_agent()
    model_mgr = agent.model_manager
    
    if model_mgr.set_model(model_key):
        config = model_mgr.get_current_model()
        console.print(f"[green]✓ Switched to {config.name}[/green]")
    else:
        console.print(f"[red]✗ Failed to switch to {model_key}[/red]")
        console.print("Use 'python main.py models' to see available models")

@app.command()
def download_model(model_key: str = typer.Argument(..., help="Model key to download")):
    """Download a model (for local models)"""
    agent = initialize_agent()
    model_mgr = agent.model_manager
    
    console.print(f"[blue]Downloading {model_key}...[/blue]")
    
    if model_mgr.download_model(model_key):
        console.print(f"[green]✓ Successfully downloaded {model_key}[/green]")
    else:
        console.print(f"[red]✗ Failed to download {model_key}[/red]")

@app.command()
def setup_ollama():
    """Setup instructions for Ollama (local AI models)"""
    console.print(Panel(
        "[bold blue]Setting up Ollama for Local AI Models[/bold blue]\n\n"
        "[bold]1. Install Ollama (Mac users - choose one):[/bold]\n"
        "   • Download app: https://ollama.ai (easiest)\n"
        "   • Homebrew: brew install ollama\n"
        "   • Curl: curl -fsSL https://ollama.ai/install.sh | sh\n\n"
        "[bold]2. Start Ollama:[/bold]\n"
        "   • If using the app: it starts automatically\n"
        "   • If using command line: ollama serve\n\n"
        "[bold]3. Download a model:[/bold]\n"
        "   python main.py download-model llama3.1\n\n"
        "[bold]4. Set as default:[/bold]\n"
        "   python main.py set-model llama3.1\n\n"
        "[dim]Recommended models:[/dim]\n"
        "• llama3.1 - Best overall performance (4.7GB)\n"
        "• mistral - Fast and efficient (4.1GB)\n"
        "• phi3 - Compact but capable (2.3GB)\n\n"
        "[bold yellow]Why use local models?[/bold yellow]\n"
        "• Complete privacy - data never leaves your computer\n"
        "• No API costs or rate limits\n"
        "• Works offline\n"
        "• Perfect for research and experimentation",
        title="🦙 Ollama Setup"
    ))

@app.command()
def background_service(daemon: bool = typer.Option(False, help="Run as daemon process")):
    """Start the background proactive service"""
    console.print("[blue]Starting Proactive AI Agent Background Service...[/blue]")
    
    try:
        # Initialize agent
        agent = initialize_agent()
        
        # Setup system service if running as daemon
        if daemon:
            service_manager = SystemServiceManager()
            service_manager.create_daemon_process()
            console.print("[green]✓ Daemon process created[/green]")
        
        # Start proactive system
        agent.proactive_manager.start_proactive_system()
        console.print("[green]✓ Proactive system started[/green]")
        
        # Keep running
        try:
            while True:
                time.sleep(60)  # Check every minute
                
                # Show status periodically
                if daemon and int(time.time()) % 3600 == 0:  # Every hour
                    status = agent.proactive_manager.get_proactive_status()
                    console.print(f"[dim]Status: {status['notifications_sent']} notifications sent[/dim]")
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down background service...[/yellow]")
        
        # Cleanup
        agent.proactive_manager.stop_proactive_system()
        console.print("[green]Background service stopped[/green]")
        
    except Exception as e:
        console.print(f"[red]Error in background service: {e}[/red]")
        sys.exit(1)

@app.command()
def service(action: str = typer.Argument(..., help="Action: install, uninstall, start, stop, status")):
    """Manage system service installation"""
    service_manager = SystemServiceManager()
    
    if action == "install":
        console.print("[blue]Installing system service...[/blue]")
        success = service_manager.install_service(auto_start=True)
        if success:
            console.print("[green]✓ Service installed successfully[/green]")
            console.print("[dim]The agent will now start automatically on system boot[/dim]")
        else:
            console.print("[red]✗ Service installation failed[/red]")
    
    elif action == "uninstall":
        console.print("[blue]Uninstalling system service...[/blue]")
        success = service_manager.uninstall_service()
        if success:
            console.print("[green]✓ Service uninstalled successfully[/green]")
        else:
            console.print("[red]✗ Service uninstallation failed[/red]")
    
    elif action == "start":
        console.print("[blue]Starting service...[/blue]")
        success = service_manager.start_service()
        if success:
            console.print("[green]✓ Service started[/green]")
        else:
            console.print("[red]✗ Failed to start service[/red]")
    
    elif action == "stop":
        console.print("[blue]Stopping service...[/blue]")
        success = service_manager.stop_service()
        if success:
            console.print("[green]✓ Service stopped[/green]")
        else:
            console.print("[red]✗ Failed to stop service[/red]")
    
    elif action == "status":
        status = service_manager.get_service_status()
        
        table = Table(title="🔧 Service Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Platform", status['platform'])
        table.add_row("Service Name", status['service_name'])
        table.add_row("Installed", "✅ Yes" if status['installed'] else "❌ No")
        table.add_row("Running", "✅ Yes" if status['running'] else "❌ No")
        
        if status['pid']:
            table.add_row("Process ID", str(status['pid']))
        
        if status['uptime']:
            uptime_hours = status['uptime'] / 3600
            table.add_row("Uptime", f"{uptime_hours:.1f} hours")
        
        console.print(table)
        
        # Show recent logs
        logs = service_manager.get_logs(10)
        if logs:
            console.print("\n[cyan]Recent Logs:[/cyan]")
            for log in logs[-5:]:  # Show last 5 lines
                console.print(f"[dim]{log.strip()}[/dim]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Available actions: install, uninstall, start, stop, status")

@app.command()
def proactive(action: str = typer.Argument("status", help="Action: status, enable, disable, test")):
    """Manage proactive notifications"""
    agent = initialize_agent()
    
    if action == "status":
        status = agent.proactive_manager.get_proactive_status()
        
        console.print(Panel(
            f"[bold]Enabled:[/bold] {'✅ Yes' if status['enabled'] else '❌ No'}\n"
            f"[bold]Running:[/bold] {'✅ Yes' if status['running'] else '❌ No'}\n"
            f"[bold]Notifications Sent:[/bold] {status['metrics']['notifications_sent']}\n"
            f"[bold]User Interactions:[/bold] {status['metrics']['user_interactions']}\n"
            f"[bold]Active Notifications:[/bold] {status['active_notifications']}\n"
            f"[bold]Trigger Rules:[/bold] {status['trigger_rules_count']}",
            title="🔮 Proactive System Status"
        ))
        
        # Show recent notifications
        history = agent.proactive_manager.get_notification_history(7)
        if history:
            console.print("\n[cyan]Recent Activity:[/cyan]")
            for record in history[:3]:
                console.print(f"  • {record}")
    
    elif action == "enable":
        agent.proactive_manager.update_proactive_config({'enabled': True})
        console.print("[green]✓ Proactive notifications enabled[/green]")
    
    elif action == "disable":
        agent.proactive_manager.update_proactive_config({'enabled': False})
        console.print("[yellow]Proactive notifications disabled[/yellow]")
    
    elif action == "test":
        console.print("[blue]Sending test notification...[/blue]")
        notification_id = agent.proactive_manager.send_immediate_notification(
            title="Test Notification",
            message="This is a test of your proactive AI agent notification system!",
            priority="normal"
        )
        
        if notification_id:
            console.print(f"[green]✓ Test notification sent: {notification_id}[/green]")
        else:
            console.print("[red]✗ Failed to send test notification[/red]")
    
    elif action == "force-check":
        console.print("[blue]Forcing immediate proactive check...[/blue]")
        console.print("[dim]This simulates what the background service does every 15 minutes[/dim]")
        
        import subprocess
        result = subprocess.run([sys.executable, "trigger_proactive.py", "--action", "check"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Proactive check completed[/green]")
            console.print("[yellow]Check your macOS Notification Center for new notifications![/yellow]")
        else:
            console.print(f"[red]Error in proactive check: {result.stderr}[/red]")
    
    elif action == "demo":
        console.print("[blue]Running notification demo...[/blue]")
        console.print("[dim]This will send several example notifications[/dim]")
        
        import subprocess
        result = subprocess.run([sys.executable, "test_notifications.py", "--type", "scenarios"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Demo notifications sent[/green]")
            console.print("[yellow]Check your macOS Notification Center![/yellow]")
        else:
            console.print(f"[red]Error in demo: {result.stderr}[/red]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Available actions: status, enable, disable, test, force-check, demo")

@app.command()
def profile():
    """View learned user profile and preferences"""
    agent = initialize_agent()
    profile_data = agent.memory.get_user_profile()
    
    table = Table(title="📊 Your AI Agent Profile")
    table.add_column("Aspect", style="cyan")
    table.add_column("Learned Preferences", style="green")
    
    table.add_row("Communication Style", profile_data.get('communication_style', 'Learning...'))
    table.add_row("Preferred Topics", ', '.join(profile_data.get('interests', ['Discovering...'])))
    
    # Format active hours dict as string
    active_hours = profile_data.get('active_hours', {})
    if isinstance(active_hours, dict) and active_hours:
        # Sort by hour and format nicely
        hours_str = ', '.join([f"{h}:00 ({count}x)" for h, count in sorted(active_hours.items(), key=lambda x: int(x[0]))])
        table.add_row("Active Hours", hours_str)
    else:
        table.add_row("Active Hours", 'Observing patterns...')
    
    # Format primary goals
    primary_goals = profile_data.get('primary_goals', [])
    if isinstance(primary_goals, list) and primary_goals:
        table.add_row("Goal Focus", ', '.join(primary_goals))
    else:
        table.add_row("Goal Focus", 'Setting up...')
    
    table.add_row("Interaction Frequency", profile_data.get('interaction_preference', 'Adaptive'))
    
    console.print(table)
    
    # Show recent learning
    recent_insights = agent.memory.get_recent_insights()
    if recent_insights:
        console.print("\n[yellow]🧠 Recent Learning:[/yellow]")
        for insight in recent_insights[-3:]:
            console.print(f"  • {insight}")

@app.command()
def setup_calendar():
    """Set up Google Calendar integration"""
    agent = initialize_agent()
    
    console.print("[blue]Setting up Google Calendar integration...[/blue]")
    
    if Confirm.ask("Do you want to connect your Google Calendar?"):
        try:
            agent.calendar_manager.setup_oauth()
            console.print("[green]✓ Calendar connected successfully![/green]")
            
            # Test calendar access
            upcoming = agent.calendar_manager.get_upcoming_events(limit=3)
            if upcoming:
                console.print("\n[cyan]📅 Your upcoming events:[/cyan]")
                for event in upcoming:
                    console.print(f"  • {event['summary']} - {event['start']}")
        except Exception as e:
            console.print(f"[red]Calendar setup failed: {e}[/red]")
    else:
        console.print("[yellow]Calendar integration skipped.[/yellow]")

@app.command()
def goals(action: str = typer.Argument("list", help="Action: list, add, update, remove")):
    """Manage personal goals and tracking"""
    agent = initialize_agent()
    
    if action == "list":
        goals = agent.memory.get_goals()
        if goals:
            table = Table(title="🎯 Your Goals")
            table.add_column("Goal", style="cyan")
            table.add_column("Progress", style="green")
            table.add_column("Target Date", style="yellow")
            
            for goal in goals:
                table.add_row(
                    goal['title'],
                    f"{goal['progress']}%",
                    goal.get('target_date', 'No deadline')
                )
            console.print(table)
        else:
            console.print("[yellow]No goals set yet. Use 'goals add' to create one.[/yellow]")
    
    elif action == "add":
        title = Prompt.ask("Goal title")
        description = Prompt.ask("Description (optional)", default="")
        target_date = Prompt.ask("Target date (YYYY-MM-DD, optional)", default="")
        
        agent.memory.add_goal(title, description, target_date)
        console.print(f"[green]✓ Goal '{title}' added![/green]")

@app.command()
def config(
    proactive: Optional[bool] = typer.Option(None, help="Enable/disable proactive features")
):
    """Configure agent behavior settings"""
    agent = initialize_agent()
    
    if proactive is not None:
        agent.config['proactive_enabled'] = proactive
        console.print(f"[green]Proactive features {'enabled' if proactive else 'disabled'}[/green]")
    
    # Show current config
    console.print("\n[cyan]Current Configuration:[/cyan]")
    for key, value in agent.config.items():
        console.print(f"  {key}: {value}")

@app.command()
def cleanup(
    conversations: bool = typer.Option(False, "--conversations", "-c", help="Clear conversation history"),
    goals: bool = typer.Option(False, "--goals", "-g", help="Clear all goals"),
    profile: bool = typer.Option(False, "--profile", "-p", help="Clear user profile"),
    insights: bool = typer.Option(False, "--insights", "-i", help="Clear learning insights"),
    patterns: bool = typer.Option(False, "--patterns", help="Clear interaction patterns"),
    all: bool = typer.Option(False, "--all", "-a", help="Clear everything (requires confirmation)")
):
    """Clean up user data and reset the database"""
    
    # Initialize memory
    memory = UserMemory()
    
    # If no options specified, show help
    if not any([conversations, goals, profile, insights, patterns, all]):
        console.print("[yellow]Please specify what to clean up:[/yellow]")
        console.print("  --all, -a           Clear everything")
        console.print("  --conversations, -c Clear conversation history")
        console.print("  --goals, -g         Clear all goals")
        console.print("  --profile, -p       Clear user profile")
        console.print("  --insights, -i      Clear learning insights")
        console.print("  --patterns          Clear interaction patterns")
        console.print("\n[cyan]Example:[/cyan] python main.py cleanup --all")
        return
    
    # Confirm if clearing everything
    if all:
        console.print("[red]⚠️  WARNING: This will delete ALL data including:[/red]")
        console.print("  • Conversation history")
        console.print("  • Goals and progress")
        console.print("  • User profile and preferences")
        console.print("  • Learning insights")
        console.print("  • Interaction patterns")
        
        if not Confirm.ask("\n[bold red]Are you sure you want to continue?[/bold red]", default=False):
            console.print("[yellow]Cleanup cancelled.[/yellow]")
            return
        
        memory.clear_data('all')
        console.print("[green]✓ All data cleared successfully![/green]")
        return
    
    # Clear specific data types
    cleared = []
    
    if conversations:
        memory.clear_data('conversations')
        cleared.append("conversation history")
    
    if goals:
        memory.clear_data('goals')
        cleared.append("goals")
    
    if profile:
        memory.clear_data('profile')
        cleared.append("user profile")
    
    if insights:
        memory.clear_data('insights')
        cleared.append("learning insights")
    
    if patterns:
        memory.clear_data('patterns')
        cleared.append("interaction patterns")
    
    if cleared:
        console.print(f"[green]✓ Cleared: {', '.join(cleared)}[/green]")
    else:
        console.print("[yellow]Nothing to clear.[/yellow]")

def show_help():
    """Show available commands during chat"""
    console.print("\n[cyan]Available Commands:[/cyan]")
    console.print("  help - Show this help")
    console.print("  status - Show agent status and capabilities")
    console.print("  quit/exit/bye - End conversation")
    console.print("  profile - View learned preferences")
    console.print("  goals - Quick goal check")
    console.print("  models - View AI models")

if __name__ == "__main__":
    app()
