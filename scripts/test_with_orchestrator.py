"""
Example script showing how to use the orchestrator with different environment profiles.
"""
import asyncio
import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from nova_aegis.environment_forge import EnvironmentForge, EnvironmentProfile, ServiceConfig
from nova_aegis.orchestrator import DevOrchestrator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("nova_aegis")
console = Console()

async def setup_test_profile():
    """Create a test environment profile if it doesn't exist."""
    forge = EnvironmentForge()
    
    if "test" not in forge.list_profiles():
        test_profile = EnvironmentProfile(
            name="test",
            description="Test environment with minimal services",
            services={
                "postgres": ServiceConfig(
                    image="postgres:latest",
                    environment={
                        "POSTGRES_USER": "test",
                        "POSTGRES_PASSWORD": "test",
                        "POSTGRES_DB": "test_db"
                    },
                    ports={"5432": 5433}  # Use different port for test env
                ),
                "redis": ServiceConfig(
                    image="redis:latest",
                    environment={},
                    ports={"6379": 6380}  # Use different port for test env
                )
            },
            auto_start=["postgres", "redis"],
            auto_cleanup=True,
            log_retention_days=1
        )
        forge.forge_profile(test_profile)
        logger.info("Created test environment profile")

async def show_environment_status(orchestrator: DevOrchestrator):
    """Display current environment status in a rich table."""
    table = Table(title=f"Environment Status: {orchestrator.profile.name}")
    table.add_column("Service")
    table.add_column("Status")
    table.add_column("Ports")
    
    for name, config in orchestrator.profile.services.items():
        status = "[green]Running" if name in orchestrator.containers else "[red]Stopped"
        ports = ", ".join(f"{container}→{host}" for container, host in config.ports.items())
        table.add_row(name, status, ports)
    
    console.print(table)

async def run_test():
    """Run tests with orchestrated services."""
    # Create test profile if needed
    await setup_test_profile()
    
    try:
        # Start services using test profile
        console.rule("[bold blue]Starting Test Environment")
        orchestrator = DevOrchestrator(profile_name="test")
        
        if not await orchestrator.start_all():
            logger.error("Failed to start services")
            return
            
        # Show environment status
        await show_environment_status(orchestrator)
        
        # Run tests
        console.rule("[bold blue]Running Tests")
        import pytest
        test_result = pytest.main([
            "tests/e2e/test_exploration_companion.py",
            "-v",
            "--log-cli-level=INFO"
        ])
        
        if test_result == 0:
            console.print("\n[bold green]Tests passed!")
        else:
            console.print("\n[bold red]Tests failed!")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user")
    except Exception as e:
        logger.exception("Test run failed")
    finally:
        # Stop services
        console.rule("[bold blue]Stopping Services")
        await orchestrator.stop_all()
        
        # Show logs
        console.rule("[bold blue]Service Logs")
        logs = orchestrator.get_logs()
        for name, content in logs.items():
            if content:
                console.print(Panel(
                    "\n".join(content.splitlines()[-10:]),  # Last 10 lines
                    title=f"{name} logs",
                    title_align="left"
                ))

def main():
    """Main entry point."""
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...")
    finally:
        console.print("\n[green]Done!")

if __name__ == "__main__":
    main()