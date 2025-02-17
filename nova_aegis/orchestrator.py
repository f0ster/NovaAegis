"""
Development environment orchestrator for NovaAegis.
Handles Docker service lifecycle and health monitoring.
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional

import docker
from docker.models.containers import Container
from rich.console import Console
from rich.logging import RichHandler

from .environment_forge import EnvironmentForge

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("nova_aegis")
console = Console()

class DevOrchestrator:
    """Manages local development services using Docker."""
    
    def __init__(self, profile_name: Optional[str] = None):
        self.docker = docker.from_env()
        self.forge = EnvironmentForge()
        if profile_name:
            self.forge.set_active_profile(profile_name)
        self.profile = self.forge.get_profile()
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.containers: Dict[str, Container] = {}
        
    async def _check_health(self, name: str, container: Container) -> bool:
        """Check if a service is healthy based on its configuration."""
        service_config = self.profile.services[name]
        try:
            # Try basic health check first
            if not container.status == "running":
                return False
                
            # Service-specific health checks
            if "postgres" in service_config.image:
                result = await asyncio.to_thread(
                    container.exec_run,
                    "pg_isready",
                    user="postgres"
                )
                return result.exit_code == 0
                
            elif "redis" in service_config.image:
                result = await asyncio.to_thread(
                    container.exec_run,
                    "redis-cli ping"
                )
                return result.exit_code == 0 and b"PONG" in result.output
                
            # Default to just checking running status
            return True
            
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return False
            
    async def start_service(self, name: str) -> bool:
        """Start a Docker service."""
        if name not in self.profile.services:
            logger.error(f"Unknown service: {name}")
            return False
            
        service_config = self.profile.services[name]
        container_name = service_config.container_name or f"novaaegis-{name}-1"
        
        try:
            # Remove existing container if it exists
            try:
                container = self.docker.containers.get(container_name)
                await asyncio.to_thread(container.remove, force=True)
            except docker.errors.NotFound:
                pass
                
            # Start new container
            container = await asyncio.to_thread(
                self.docker.containers.run,
                service_config.image,
                name=container_name,
                detach=True,
                environment=service_config.environment,
                ports={f"{port}/tcp": host_port for port, host_port in service_config.ports.items()},
                volumes=service_config.volumes
            )
            
            self.containers[name] = container
            
            # Stream logs to file
            log_file = self.logs_dir / f"{name}.log"
            with open(log_file, "wb") as f:
                for log in container.logs(stream=True):
                    f.write(log)
                    
            # Wait for service to be healthy
            for _ in range(service_config.healthcheck_timeout):
                if await self._check_health(name, container):
                    return True
                await asyncio.sleep(service_config.healthcheck_interval)
                
            logger.error(f"{name} failed health check")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return False
            
    async def stop_service(self, name: str) -> bool:
        """Stop a Docker service."""
        try:
            if name in self.containers:
                container = self.containers[name]
                await asyncio.to_thread(container.stop)
                await asyncio.to_thread(container.remove)
                del self.containers[name]
            logger.info(f"Stopped {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop {name}: {e}")
            return False
            
    async def start_all(self) -> bool:
        """Start all services in profile's auto-start order."""
        if not self.profile.auto_start:
            logger.warning("No services configured for auto-start")
            return True
            
        for name in self.profile.auto_start:
            if not await self.start_service(name):
                logger.error("Failed to start services")
                await self.stop_all()
                return False
        return True
        
    async def stop_all(self):
        """Stop all running services."""
        if self.profile.auto_start:
            for name in reversed(self.profile.auto_start):
                await self.stop_service(name)
                
    def get_logs(self, service: Optional[str] = None) -> Dict[str, str]:
        """Get logs for one or all services."""
        logs = {}
        services = [service] if service else self.profile.services.keys()
        
        for name in services:
            log_file = self.logs_dir / f"{name}.log"
            if log_file.exists():
                with open(log_file) as f:
                    logs[name] = f.read()
            else:
                logs[name] = ""
                
        return logs