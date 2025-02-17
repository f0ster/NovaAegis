"""
Core service providers for NovaAegis.
Defines the essential services required for intelligent execution.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any

class ServiceState(Enum):
    """States a service can be in."""
    UNKNOWN = auto()
    STARTING = auto()
    READY = auto()
    DEGRADED = auto()
    ERROR = auto()

@dataclass
class ServiceHealth:
    """Health information for a service."""
    state: ServiceState
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    last_error: Optional[str] = None

class CoreService(ABC):
    """Base interface for all core services."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service and its resources."""
        pass
        
    @abstractmethod
    async def check_health(self) -> ServiceHealth:
        """Check service health and availability."""
        pass
        
    @abstractmethod
    async def shutdown(self) -> bool:
        """Clean shutdown of the service."""
        pass

class KnowledgeStore(CoreService):
    """
    Graph database service for storing knowledge and relationships.
    Typically implemented with Neo4j.
    
    Responsibilities:
    - Store code patterns and their relationships
    - Track learning progress and insights
    - Maintain context graphs for research paths
    """
    
    @abstractmethod
    async def store_pattern(self, pattern: Dict[str, Any]) -> bool:
        """Store a new code pattern with relationships."""
        pass
        
    @abstractmethod
    async def query_patterns(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query relevant patterns based on context."""
        pass
        
    @abstractmethod
    async def update_relationships(self, updates: List[Dict[str, Any]]) -> bool:
        """Update pattern relationships."""
        pass

class ParameterStore(CoreService):
    """
    Relational database service for structured data.
    Typically implemented with PostgreSQL.
    
    Responsibilities:
    - Store configuration parameters
    - Track execution metrics and states
    - Maintain service profiles and settings
    """
    
    @abstractmethod
    async def store_parameters(self, params: Dict[str, Any]) -> bool:
        """Store configuration parameters."""
        pass
        
    @abstractmethod
    async def get_parameters(self, profile: str) -> Dict[str, Any]:
        """Get parameters for a service profile."""
        pass
        
    @abstractmethod
    async def update_metrics(self, metrics: Dict[str, float]) -> bool:
        """Update execution metrics."""
        pass

class LLMInterface(CoreService):
    """
    Language model service for intelligent operations.
    Can be configured for different providers (OpenAI, Anthropic, etc).
    
    Responsibilities:
    - Handle intelligent code analysis
    - Generate code and documentation
    - Provide reasoning capabilities
    """
    
    @abstractmethod
    async def analyze_code(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code with context."""
        pass
        
    @abstractmethod
    async def generate_code(self, spec: Dict[str, Any]) -> str:
        """Generate code based on specification."""
        pass
        
    @abstractmethod
    async def explain_pattern(self, pattern: Dict[str, Any]) -> str:
        """Explain a code pattern."""
        pass

# Service provider registry maps service types to implementations
SERVICE_REGISTRY = {
    "knowledge_store": {
        "neo4j": "nova_aegis.services.neo4j_store.Neo4jKnowledgeStore",
        "memory": "nova_aegis.services.memory_store.InMemoryKnowledgeStore"
    },
    "parameter_store": {
        "postgres": "nova_aegis.services.postgres_store.PostgresParameterStore",
        "sqlite": "nova_aegis.services.sqlite_store.SQLiteParameterStore"
    },
    "llm_interface": {
        "openai": "nova_aegis.services.openai_llm.OpenAIInterface",
        "anthropic": "nova_aegis.services.anthropic_llm.AnthropicInterface",
        "local": "nova_aegis.services.local_llm.LocalLLMInterface"
    }
}