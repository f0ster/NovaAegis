#!/usr/bin/env python3
"""
Visualize knowledge accumulation and learning progress.
Shows real-time evolution of system understanding through research chains.
"""
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import structlog
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from nova_aegis.research_engine import ResearchEngine
from nova_aegis.tuning.confidence_crew import ConfidenceCrew
from nova_aegis.llm_interface import LLMInterface

logger = structlog.get_logger()
console = Console()

class LearningVisualizer:
    """Visualizes knowledge accumulation process."""
    
    def __init__(self):
        self.engine = ResearchEngine()
        self.llm = LLMInterface()
        self.crew = ConfidenceCrew(self.llm)
        
        # Tracking state
        self.knowledge_states = []
        self.confidence_history = []
        self.pattern_counts = []
        self.relationship_counts = []
        self.timestamps = []
        
        # Visualization
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(15, 6))
        plt.ion()  # Interactive mode
    
    def capture_state(self):
        """Capture current knowledge state."""
        state = {
            "patterns": len(self.engine.get_stored_patterns()),
            "relationships": len(self.engine.get_relationships()),
            "confidence": self.engine.get_average_confidence(),
            "coherence": self.engine.get_knowledge_coherence(),
            "timestamp": datetime.now()
        }
        self.knowledge_states.append(state)
        
        # Update tracking
        self.confidence_history.append(state["confidence"])
        self.pattern_counts.append(state["patterns"])
        self.relationship_counts.append(state["relationships"])
        self.timestamps.append(state["timestamp"])
    
    def update_plots(self, frame):
        """Update visualization plots."""
        # Clear previous
        self.ax1.clear()
        self.ax2.clear()
        
        # Plot confidence over time
        self.ax1.plot(self.timestamps, self.confidence_history, 'b-')
        self.ax1.set_title("Confidence Evolution")
        self.ax1.set_ylabel("Average Confidence")
        self.ax1.grid(True)
        
        # Plot knowledge growth
        self.ax2.plot(self.timestamps, self.pattern_counts, 'g-', label="Patterns")
        self.ax2.plot(self.timestamps, self.relationship_counts, 'r-', label="Relationships")
        self.ax2.set_title("Knowledge Growth")
        self.ax2.set_ylabel("Count")
        self.ax2.legend()
        self.ax2.grid(True)
        
        plt.tight_layout()
    
    def show_metrics_table(self):
        """Show current metrics table."""
        if not self.knowledge_states:
            return
        
        current = self.knowledge_states[-1]
        table = Table(title="Current Knowledge State")
        
        table.add_column("Metric")
        table.add_column("Value")
        table.add_column("Trend")
        
        # Add rows
        for metric, value in current.items():
            if metric != "timestamp":
                trend = self._get_trend(metric)
                table.add_row(
                    metric.replace("_", " ").title(),
                    f"{value:.2f}" if isinstance(value, float) else str(value),
                    trend
                )
        
        console.print(table)
    
    def _get_trend(self, metric: str) -> str:
        """Calculate trend for metric."""
        if len(self.knowledge_states) < 2:
            return "⟷"
        
        previous = self.knowledge_states[-2][metric]
        current = self.knowledge_states[-1][metric]
        
        if isinstance(current, (int, float)):
            if current > previous:
                return "↑"
            elif current < previous:
                return "↓"
        return "⟷"

async def run_learning_visualization(topics: List[str]):
    """Run and visualize learning process."""
    visualizer = LearningVisualizer()
    
    try:
        with Live(console=console, refresh_per_second=1):
            for topic in topics:
                console.print(f"\n[bold blue]Researching: {topic}")
                
                # Initial research
                results = await visualizer.engine.research_code(
                    query=topic,
                    min_relevance=0.5
                )
                
                # Extract and research concepts
                concepts = await visualizer.llm.extract_concepts(
                    [r.code_segment for r in results]
                )
                
                for concept in concepts:
                    console.print(f"[cyan]Exploring concept: {concept}")
                    
                    # Research concept
                    concept_results = await visualizer.engine.research_code(
                        query=f"{concept} implementation patterns",
                        min_relevance=0.7
                    )
                    
                    # Analyze and store
                    await visualizer.engine.analyze_implementation_patterns(
                        concept_results
                    )
                    
                    # Update visualization
                    visualizer.capture_state()
                    visualizer.show_metrics_table()
                    
                    # Allow time to view progress
                    await asyncio.sleep(1)
                
                # Show relationship graph
                if visualizer.engine.get_relationships():
                    console.print("\n[bold]Knowledge Graph Structure:")
                    graph = visualizer.engine.get_knowledge_graph()
                    nx.draw(
                        graph,
                        with_labels=True,
                        node_color='lightblue',
                        node_size=500,
                        font_size=8
                    )
                    plt.show()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Learning visualization stopped")
    
    finally:
        # Show final state
        console.print("\n[bold green]Final Knowledge State:")
        visualizer.show_metrics_table()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Visualize knowledge accumulation"
    )
    parser.add_argument(
        "--topics",
        nargs="+",
        default=[
            "error handling patterns",
            "async programming",
            "state management",
            "data validation"
        ],
        help="Topics to research"
    )
    
    args = parser.parse_args()
    
    # Run visualization
    asyncio.run(run_learning_visualization(args.topics))

if __name__ == "__main__":
    main()