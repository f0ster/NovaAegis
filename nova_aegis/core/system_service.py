"""
System service manager for NovaAegis.
Handles core service lifecycle and health monitoring.
"""
import asyncio
import importlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Type, Any

from rich.console import Console
from rich.logging import RichHandler

from .service_provider import (
    CoreService,
    ServiceHealth,
    ServiceState,
    KnowledgeStore,
    ParameterStore,
    LLMInterface,
    SERVICE_REGISTRY
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("nova_aegis")
console = Console()

class SystemService:
    """
    Manages core service lifecycle and health monitoring.
    
    This class handles:
    - Starting required services (Knowledge Store, Parameter Store, LLM)
    - Monitoring service health
    - Service configuration and profiles
    """
    
    def __init__(self):
        self.services: Dict[str, CoreService] = {}
        self.health_cache: Dict[str, ServiceHealth] = {}
        self.stop_event = asyncio.Event()
        self.monitor_task = None
        
    def _import_service_class(self, service_path: str) -> Type[CoreService]:
        """Dynamically import a service class."""
        module_path, class_name = service_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
        
    async def start_service(self, service_type: str, provider: str, config: Dict[str, Any]) -> bool:
        """Start a core service with the specified provider."""
        if service_type in self.services:
            logger.warning(f"{service_type} is already running")
            return False
            
        service_path = SERVICE_REGISTRY.get(service_type, {}).get(provider)
        if not service_path:
            logger.error(f"Unknown service type/provider: {service_type}/{provider}")
            return False
            
        try:
            service_class = self._import_service_class(service_path)
            service = service_class()
            
            if await service.initialize():
                self.services[service_type] = service
                # Start monitoring if this is the first service
                if len(self.services) == 1:
                    self.monitor_task = asyncio.create_task(self._monitor_services())
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to start {service_type}: {e}")
            return False
            
    async def stop_service(self, service_type: str) -> bool:
        """Stop a core service."""
        if service_type not in self.services:
            logger.warning(f"{service_type} is not running")
            return False
            
        service = self.services[service_type]
        try:
            if await service.shutdown():
                del self.services[service_type]
                if service_type in self.health_cache:
                    del self.health_cache[service_type]
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop {service_type}: {e}")
            return False
            
    async def stop_all(self):
        """Stop all services."""
        self.stop_event.set()
        if self.monitor_task:
            await self.monitor_task
            
        for service_type in list(self.services.keys()):
            await self.stop_service(service_type)
            
    async def _monitor_services(self):
        """Monitor health of all services."""
        while not self.stop_event.is_set():
            for service_type, service in self.services.items():
                try:
                    health = await service.check_health()
                    self.health_cache[service_type] = health
                    
                    if health.state in (ServiceState.ERROR, ServiceState.DEGRADED):
                        logger.warning(f"{service_type} health check failed: {health.last_error}")
                        
                except Exception as e:
                    logger.error(f"Error checking {service_type} health: {e}")
                    
            await asyncio.sleep(30)  # Check every 30 seconds
            
    def get_service_status(self, service_type: Optional[str] = None) -> Dict[str, ServiceHealth]:
        """Get health status of one or all services."""
        if service_type:
            health = self.health_cache.get(service_type)
            return {service_type: health} if health else {}
        return self.health_cache.copy()
        
    def get_service(self, service_type: str) -> Optional[CoreService]:
        """Get a running service instance."""
        return self.services.get(service_type)