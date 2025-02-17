#!/usr/bin/env python3
"""
Run integration tests with real-time monitoring.
Shows test progress, metrics, and knowledge accumulation.
"""
import asyncio
import pytest
import time
from pathlib import Path
import structlog
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn
import plotly.graph_objects as go
from datetime import datetime

logger = structlog.get_logger()
console = Console()

class TestMonitor:
    """Monitor integration test execution and metrics."""
    
    def __init__(self):
        self.metrics = {
            "research_results": [],
            "confidence_scores": [],
            "pattern_counts": [],
            "relationship_counts": [],
            "timestamps": []
        }
        
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def update_metrics(self, metrics: dict):
        """Update test metrics."""
        self.metrics["research_results"].append(metrics.get("results_count", 0))
        self.metrics["confidence_scores"].append(metrics.get("confidence", 0))
        self.metrics["pattern_counts"].append(metrics.get("patterns", 0))
        self.metrics["relationship_counts"].append(metrics.get("relationships", 0))
        self.metrics["timestamps"].append(datetime.now())
    
    def show_progress(self):
        """Show current test progress."""
        table = Table(title="Integration Test Progress")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Trend", style="yellow")
        
        # Add current metrics
        if self.metrics["confidence_scores"]:
            current_confidence = self.metrics["confidence_scores"][-1]
            confidence_trend = self._get_trend(self.metrics["confidence_scores"])
            table.add_row(
                "Confidence",
                f"{current_confidence:.2f}",
                confidence_trend
            )
        
        if self.metrics["pattern_counts"]:
            current_patterns = self.metrics["pattern_counts"][-1]
            pattern_trend = self._get_trend(self.metrics["pattern_counts"])
            table.add_row(
                "Patterns",
                str(current_patterns),
                pattern_trend
            )
        
        if self.metrics["relationship_counts"]:
            current_relations = self.metrics["relationship_counts"][-1]
            relation_trend = self._get_trend(self.metrics["relationship_counts"])
            table.add_row(
                "Relationships",
                str(current_relations),
                relation_trend
            )
        
        # Add test results
        table.add_row(
            "Tests Passed",
            str(self.test_results["passed"]),
            "✓" if self.test_results["passed"] > 0 else "-"
        )
        
        table.add_row(
            "Tests Failed",
            str(self.test_results["failed"]),
            "✗" if self.test_results["failed"] > 0 else "-"
        )
        
        console.print(table)
    
    def plot_metrics(self):
        """Plot metrics over time."""
        fig = go.Figure()
        
        # Confidence trend
        fig.add_trace(go.Scatter(
            x=self.metrics["timestamps"],
            y=self.metrics["confidence_scores"],
            name="Confidence",
            line=dict(color="blue")
        ))
        
        # Pattern growth
        fig.add_trace(go.Scatter(
            x=self.metrics["timestamps"],
            y=self.metrics["pattern_counts"],
            name="Patterns",
            line=dict(color="green")
        ))
        
        # Relationship growth
        fig.add_trace(go.Scatter(
            x=self.metrics["timestamps"],
            y=self.metrics["relationship_counts"],
            name="Relationships",
            line=dict(color="red")
        ))
        
        fig.update_layout(
            title="Knowledge Growth During Tests",
            xaxis_title="Time",
            yaxis_title="Count",
            hovermode="x unified"
        )
        
        # Save plot
        fig.write_html("test_metrics.html")
    
    def _get_trend(self, values: list) -> str:
        """Calculate trend indicator."""
        if len(values) < 2:
            return "⟷"
        
        if values[-1] > values[-2]:
            return "↑"
        elif values[-1] < values[-2]:
            return "↓"
        return "⟷"

async def run_tests():
    """Run integration tests with monitoring."""
    monitor = TestMonitor()
    
    try:
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            console=console
        ) as progress:
            
            # Find test files
            test_dir = Path("tests/integration")
            test_files = list(test_dir.glob("test_*.py"))
            
            task = progress.add_task(
                "Running integration tests...",
                total=len(test_files)
            )
            
            for test_file in test_files:
                console.print(f"\nRunning tests in {test_file.name}")
                
                # Run tests and capture output
                result = pytest.main([
                    "-v",
                    "--capture=no",
                    str(test_file)
                ])
                
                # Update results
                if result == 0:
                    monitor.test_results["passed"] += 1
                else:
                    monitor.test_results["failed"] += 1
                
                # Show progress
                monitor.show_progress()
                progress.advance(task)
                
                # Brief pause to show progress
                await asyncio.sleep(1)
            
            console.print("\n[green]Integration tests completed!")
            
            # Generate final metrics
            monitor.plot_metrics()
            console.print(
                "\nMetrics visualization saved to test_metrics.html"
            )
    
    except Exception as e:
        logger.error("test_execution_failed", error=str(e))
        raise

def main():
    """Main entry point."""
    start_time = time.time()
    
    try:
        asyncio.run(run_tests())
        
        duration = time.time() - start_time
        console.print(f"\nTotal duration: {duration:.2f} seconds")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Test execution interrupted")
        return 1
    
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())