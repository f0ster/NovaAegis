"""
CLI interface to the cognitive actor system.
Uses PerceptionGateway to interact with core functionality.
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.live import Live
from rich.layout import Layout
from rich.markdown import Markdown
from rich.table import Table

from .core.perception_gateway import PerceptionGateway

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("nova_aegis")
console = Console()

@click.group()
def cli():
    """NovaAegis research assistant."""
    pass

@cli.command()
@click.argument("query")
def research(query: str):
    """Run a research task."""
    gateway = PerceptionGateway()
    
    layout = Layout()
    layout.split_column(
        Layout(name="output", ratio=3),
        Layout(name="status", ratio=1)
    )
    
    try:
        with Live(layout, refresh_per_second=4):
            async def run():
                # Process task
                async for action in gateway.submit_input(query, {
                    "type": "research",
                    "timestamp": datetime.now().isoformat()
                }):
                    # Display action
                    layout["output"].update(
                        Markdown(
                            f"### {action.response_type.title()} ({action.confidence:.0%})\n"
                            f"{action.content}\n"
                        )
                    )
                    
                    # Display understanding
                    understanding = await gateway.get_understanding()
                    status_md = ["### Current Understanding"]
                    for topic, certainty in understanding["certainty"].items():
                        status_md.append(f"- {topic}: {certainty:.0%}")
                    layout["status"].update(Markdown("\n".join(status_md)))
            
            asyncio.run(run())
            
    except KeyboardInterrupt:
        console.print("[yellow]Task cancelled")
    finally:
        asyncio.run(gateway.cleanup())

@cli.command()
def history():
    """View task history."""
    gateway = PerceptionGateway()
    try:
        async def show_history():
            tasks = await gateway.get_task_history()
            
            table = Table(title="Research Tasks")
            table.add_column("Time")
            table.add_column("Input")
            table.add_column("Status")
            table.add_column("Actions")
            
            for task in tasks:
                # Count actions by type
                action_counts = {}
                if task["status"] == "completed":
                    for action in task["actions"]:
                        action_counts[action["type"]] = action_counts.get(action["type"], 0) + 1
                
                table.add_row(
                    datetime.fromisoformat(task["timestamp"]).strftime("%Y-%m-%d %H:%M"),
                    task["input"],
                    f"[green]{task['status']}" if task["status"] == "completed" else f"[red]{task['status']}",
                    ", ".join(f"{count} {type_}" for type_, count in action_counts.items()) or "-"
                )
            
            console.print(table)
        
        asyncio.run(show_history())
        
    finally:
        asyncio.run(gateway.cleanup())

if __name__ == "__main__":
    cli()