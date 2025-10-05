#!/usr/bin/env python3
"""
Demo Script for Proactive AI Agent Thesis
Demonstrates key features and capabilities
"""

import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from datetime import datetime

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.agent import ProactiveAgent
from agent.memory import UserMemory
from agent.clients.calendar_integration import CalendarManager
from agent.privacy import PrivacyManager
from agent.model_manager import ModelManager
from agent.evaluation import AgentEvaluator

console = Console()

def demo_header():
    """Display demo header"""
    console.print(Panel(
        "[bold blue]Personal and Proactive AI Agent Demo[/bold blue]\n"
        "[dim]Thesis: Adaptation, Prediction, and Interaction with GenAI[/dim]\n\n"
        "This demonstration showcases:\n"
        "• [green]Adaptive Learning[/green] - Agent learns user preferences\n"
        "• [yellow]Proactive Suggestions[/yellow] - Agent anticipates needs\n"
        "• [cyan]Privacy Controls[/cyan] - Transparent data management\n"
        "• [magenta]Evaluation Framework[/magenta] - Performance measurement",
        title="🤖 Thesis Demo",
        border_style="blue"
    ))

def simulate_user_interactions(agent):
    """Simulate realistic user interactions to demonstrate learning"""
    console.print("\n[bold]Simulating User Interactions...[/bold]")
    
    # Simulate a series of interactions that show learning
    interactions = [
        ("Hello! I'm working on my thesis project today.", "greeting_work"),
        ("I prefer short, direct responses please.", "communication_preference"),
        ("I'm interested in machine learning and AI research.", "interests"),
        ("My goal is to finish my thesis by December.", "goal_setting"),
        ("I usually work best in the mornings around 9-11 AM.", "timing_preference"),
        ("Can you help me organize my research tasks?", "task_management"),
        ("I have a meeting with my advisor tomorrow at 2 PM.", "calendar_info"),
        ("I'm feeling a bit overwhelmed with all the work.", "emotional_state"),
        ("Thanks for the help! This is really useful.", "positive_feedback"),
        ("How's my progress on the thesis goal?", "goal_check")
    ]
    
    for i, (user_message, interaction_type) in enumerate(track(interactions, description="Processing interactions...")):
        console.print(f"\n[dim]Interaction {i+1}:[/dim]")
        console.print(f"[green]User:[/green] {user_message}")
        
        # Process the message
        response = agent.process_message(user_message)
        console.print(f"[blue]Agent:[/blue] {response}")
        
        time.sleep(0.5)  # Brief pause for demonstration

def demonstrate_adaptation(agent):
    """Demonstrate the agent's adaptation capabilities"""
    console.print("\n[bold yellow]🧠 Adaptation Demonstration[/bold yellow]")
    
    # Show learned profile
    profile = agent.memory.get_user_profile()
    
    table = Table(title="Learned User Profile")
    table.add_column("Aspect", style="cyan")
    table.add_column("Learned Value", style="green")
    
    table.add_row("Communication Style", profile.get('communication_style', 'Learning...'))
    table.add_row("Interests", ', '.join(profile.get('interests', ['Discovering...'])[:3]))
    table.add_row("Total Interactions", str(profile.get('total_interactions', 0)))
    table.add_row("Primary Goals", ', '.join(profile.get('primary_goals', ['None set'])[:2]))
    
    console.print(table)
    
    # Show learning insights
    insights = agent.memory.get_recent_insights()
    if insights:
        console.print("\n[yellow]Recent Learning Insights:[/yellow]")
        for insight in insights[-3:]:
            console.print(f"  • {insight}")

def demonstrate_proactivity(agent):
    """Demonstrate proactive suggestions"""
    console.print("\n[bold magenta]🔮 Proactive Suggestions Demonstration[/bold magenta]")
    
    suggestions = agent.get_proactive_suggestions()
    
    if suggestions:
        console.print("[yellow]Current Proactive Suggestions:[/yellow]")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"  {i}. {suggestion}")
    else:
        console.print("[dim]No proactive suggestions at this time.[/dim]")
        
        # Simulate conditions for proactive suggestions
        console.print("\n[dim]Simulating conditions for proactive suggestions...[/dim]")
        
        # Add a goal that might trigger suggestions
        agent.memory.add_goal("Complete thesis literature review", "Review 20 papers on proactive AI", "2024-12-15")
        
        # Get suggestions again
        suggestions = agent.get_proactive_suggestions()
        if suggestions:
            console.print("\n[yellow]Generated Proactive Suggestions:[/yellow]")
            for i, suggestion in enumerate(suggestions, 1):
                console.print(f"  {i}. {suggestion}")

def demonstrate_privacy_controls(privacy_manager):
    """Demonstrate privacy management features"""
    console.print("\n[bold cyan]🔒 Privacy Controls Demonstration[/bold cyan]")
    
    # Show privacy report
    privacy_report = privacy_manager.generate_privacy_report()
    
    console.print(Panel(
        f"[bold]Privacy Level:[/bold] {privacy_report['privacy_level']}\n"
        f"[bold]Data Collection:[/bold] {privacy_report['data_collection']}\n"
        f"[bold]Data Usage:[/bold] {privacy_report['data_usage']}\n"
        f"[bold]Retention:[/bold] {privacy_report['data_retention']}\n"
        f"[bold]Storage:[/bold] {privacy_report['storage_location']}",
        title="Privacy Overview"
    ))
    
    # Show data categories
    categories = privacy_report.get('data_categories', [])
    if categories:
        table = Table(title="Data Categories")
        table.add_column("Category", style="cyan")
        table.add_column("Purpose", style="yellow")
        table.add_column("Retention", style="green")
        
        for category in categories[:3]:  # Show first 3
            table.add_row(
                category['category'],
                category['purpose'],
                category['retention']
            )
        
        console.print(table)

def demonstrate_evaluation(evaluator):
    """Demonstrate evaluation framework"""
    console.print("\n[bold red]📊 Evaluation Framework Demonstration[/bold red]")
    
    console.print("[dim]Running comprehensive evaluation...[/dim]")
    
    # Run evaluation
    metrics = evaluator.run_comprehensive_evaluation()
    
    # Display results
    table = Table(title="Agent Performance Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Description", style="dim")
    
    table.add_row(
        "Adaptation", 
        f"{metrics.adaptation_score:.3f}",
        "How well agent learns preferences"
    )
    table.add_row(
        "Proactivity", 
        f"{metrics.proactivity_score:.3f}",
        "Quality of proactive suggestions"
    )
    table.add_row(
        "User Satisfaction", 
        f"{metrics.user_satisfaction:.3f}",
        "Estimated user satisfaction"
    )
    table.add_row(
        "Privacy Compliance", 
        f"{metrics.privacy_compliance:.3f}",
        "Privacy controls effectiveness"
    )
    table.add_row(
        "[bold]Overall Score[/bold]", 
        f"[bold]{metrics.overall_score:.3f}[/bold]",
        "[bold]Weighted average performance[/bold]"
    )
    
    console.print(table)
    
    # Generate evaluation report
    report = evaluator.generate_evaluation_report()
    
    if report['recommendations']:
        console.print("\n[yellow]Recommendations for Improvement:[/yellow]")
        for rec in report['recommendations']:
            console.print(f"  • {rec}")

def demonstrate_research_applications():
    """Demonstrate research applications and thesis relevance"""
    console.print("\n[bold green]🎓 Research Applications & Thesis Relevance[/bold green]")
    
    applications = [
        {
            "area": "Adaptive Learning",
            "description": "Agent learns communication preferences, interests, and patterns",
            "thesis_relevance": "Demonstrates personalization through preference adaptation"
        },
        {
            "area": "Proactive Interaction", 
            "description": "Agent initiates conversations and suggests actions autonomously",
            "thesis_relevance": "Shows evolution from reactive to proactive AI assistance"
        },
        {
            "area": "Context Integration",
            "description": "Combines calendar, goals, and emotional feedback for suggestions",
            "thesis_relevance": "Illustrates multi-source data integration for enhanced interaction"
        },
        {
            "area": "Privacy Framework",
            "description": "Transparent data usage with user control and compliance",
            "thesis_relevance": "Addresses ethical considerations in personal AI systems"
        }
    ]
    
    for app in applications:
        console.print(Panel(
            f"[bold]{app['description']}[/bold]\n\n"
            f"[dim]Thesis Relevance:[/dim] {app['thesis_relevance']}",
            title=f"📋 {app['area']}"
        ))

def main():
    """Run the complete demonstration"""
    demo_header()
    
    console.print("\n[dim]Initializing agent components...[/dim]")
    
    # Initialize components
    memory = UserMemory()
    calendar_mgr = CalendarManager()
    privacy_mgr = PrivacyManager()
    model_mgr = ModelManager()
    
    # Setup default model
    current_model = model_mgr.setup_default_model()
    if current_model:
        console.print(f"[green]✓ Using model: {model_mgr.get_current_model().name}[/green]")
    else:
        console.print("[yellow]⚠ No AI models available - using fallback responses[/yellow]")
    
    # Create agent
    agent = ProactiveAgent(
        memory=memory,
        calendar_manager=calendar_mgr,
        privacy_manager=privacy_mgr,
        model_manager=model_mgr
    )
    
    # Create evaluator
    evaluator = AgentEvaluator(memory, privacy_mgr)
    
    console.print("[green]✓ Agent initialized successfully[/green]")
    
    # Run demonstrations
    simulate_user_interactions(agent)
    demonstrate_adaptation(agent)
    demonstrate_proactivity(agent)
    demonstrate_privacy_controls(privacy_mgr)
    demonstrate_evaluation(evaluator)
    demonstrate_research_applications()
    
    # Final summary
    console.print(Panel(
        "[bold green]Demo Complete![/bold green]\n\n"
        "This demonstration showed how a personal AI agent can:\n"
        "• Learn and adapt to user preferences over time\n"
        "• Provide proactive suggestions based on context\n"
        "• Maintain privacy and transparency\n"
        "• Be evaluated for effectiveness\n\n"
        "[dim]To interact with the agent directly, run:[/dim]\n"
        "[cyan]python main.py chat[/cyan]",
        title="🎯 Summary"
    ))

if __name__ == "__main__":
    main()
