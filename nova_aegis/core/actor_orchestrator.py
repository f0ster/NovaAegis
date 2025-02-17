"""
ActorOrchestrator: Coordinates cognitive actors with LangChain ReAct pattern.
Manages tool configurations and knowledge building.
"""
from typing import Dict, Any, Optional, AsyncIterator, List
import asyncio
from datetime import datetime
import uuid
from dataclasses import asdict

from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.agents import AgentExecutor
from langchain.agents import initialize_agent, AgentType

from .cognitive_actor import Action, CognitiveActor
from ..environment_forge import EnvironmentForge
from ..knowledge_store import KnowledgeStore
from ..database import AsyncDatabaseManager
from ..domain import (
    CodePattern,
    PatternRelation,
    ResearchResult,
    SearchHistory
)

class ActorOrchestrator:
    """Orchestrates cognitive actors with ReAct pattern."""
    
    def __init__(self):
        # Initialize database
        self.db_manager = AsyncDatabaseManager()
        
        # Core systems
        self.forge = EnvironmentForge()
        
        # Initialize knowledge store with database session
        self.knowledge = None  # Will be initialized in setup()
        
        # Active actors
        self.actors: Dict[str, CognitiveActor] = {}
        self.actor_states: Dict[str, str] = {}
        self.actor_profiles: Dict[str, str] = {}  # actor_id -> profile_name
        self.actor_operations: Dict[str, List[Dict[str, Any]]] = {}
        self.actor_focus: Dict[str, Optional[str]] = {}  # actor_id -> focus_area
    
    async def setup(self):
        """Initialize database session and knowledge store."""
        self.knowledge = KnowledgeStore(self.db_manager.get_async_db)
        await self.knowledge.initialize()
    
    async def initialize_actor(self, profile_name: Optional[str] = None, focus_area: Optional[str] = None) -> str:
        """Initialize actor with environment profile and optional focus."""
        if self.knowledge is None:
            await self.setup()
            
        actor_id = str(uuid.uuid4())
        
        # Get environment profile
        profile = self.forge.get_profile(profile_name)
        
        # Create actor
        actor = CognitiveActor()
        await actor.awaken()
        
        # Get focus area context
        patterns = await self.knowledge.get_patterns(focus_area)
        
        # Configure services with LangChain settings
        services = {}
        for name, config in profile.services.items():
            service_config = asdict(config)
            
            # Add ReAct prompts if defined
            if "prompts" in service_config:
                service_config["react_prompts"] = {
                    name: PromptTemplate.from_template(template)
                    for name, template in service_config["prompts"].items()
                }
                
            # Add tool permissions if defined
            if "tools" in service_config:
                service_config["allowed_tools"] = [
                    Tool(**tool_config)
                    for tool_config in service_config["tools"]
                ]
                
            services[name] = service_config
        
        # Initialize actor with configured services and focus
        await actor.perceive({
            "type": "initialization",
            "services": services,
            "patterns": patterns,
            "focus_area": focus_area
        })
        
        # Track actor
        self.actors[actor_id] = actor
        self.actor_states[actor_id] = "ready"
        self.actor_profiles[actor_id] = profile.name
        self.actor_operations[actor_id] = []
        self.actor_focus[actor_id] = focus_area
        
        return actor_id
    
    async def handle_perception(self, actor_id: str, perception: Any, context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Action]:
        """Handle perception with profile context."""
        if actor_id not in self.actors:
            raise ValueError(f"Unknown actor: {actor_id}")
            
        actor = self.actors[actor_id]
        profile_name = self.actor_profiles[actor_id]
        focus_area = self.actor_focus[actor_id]
        
        # Track operation
        operation_id = str(uuid.uuid4())
        operation = {
            "id": operation_id,
            "type": "perception",
            "content": perception,
            "profile": profile_name,
            "focus_area": focus_area,
            "timestamp": datetime.now().isoformat(),
            "actions": []
        }
        self.actor_operations[actor_id].append(operation)
        
        # Add profile and focus context
        full_context = {
            "timestamp": datetime.now().isoformat(),
            "profile": profile_name,
            "focus_area": focus_area,
            "operation_id": operation_id,
            "knowledge_state": await self.knowledge.get_current_state()
        }
        if context:
            full_context.update(context)
        
        # Process with profile
        self.actor_states[actor_id] = "processing"
        await actor.perceive(perception, full_context)
        
        try:
            while True:
                try:
                    action = await actor.action_stream.get()
                    
                    # Track action
                    operation["actions"].append({
                        "type": action.response_type,
                        "content": action.content,
                        "confidence": action.confidence,
                        "timestamp": action.timestamp.isoformat()
                    })
                    
                    # Special handling for research actions
                    if action.response_type in ["insight", "connection", "pattern"]:
                        await self.knowledge.integrate_finding({
                            "type": action.response_type,
                            "content": action.content,
                            "confidence": action.confidence,
                            "reasoning": action.reasoning,
                            "focus_area": focus_area,
                            "timestamp": action.timestamp
                        })
                    else:
                        # Index other knowledge
                        await self.knowledge.index_finding({
                            "type": action.response_type,
                            "content": action.content,
                            "confidence": action.confidence,
                            "context": {
                                "reasoning": action.reasoning,
                                "profile": profile_name,
                                "focus_area": focus_area,
                                "operation_id": operation_id
                            },
                            "timestamp": action.timestamp
                        })
                    
                    yield action
                    
                except asyncio.QueueEmpty:
                    break
                    
            self.actor_states[actor_id] = "ready"
            
        except Exception as e:
            self.actor_states[actor_id] = "error"
            operation["error"] = str(e)
            raise
    
    async def get_actor_state(self, actor_id: str) -> Dict[str, Any]:
        """Get actor's processing state."""
        if actor_id not in self.actors:
            raise ValueError(f"Unknown actor: {actor_id}")
            
        actor = self.actors[actor_id]
        focus_area = self.actor_focus[actor_id]
        
        return {
            "status": self.actor_states[actor_id],
            "forge_profile": self.actor_profiles[actor_id],
            "focus_area": focus_area,
            "knowledge": actor.understanding.knowledge_state,
            "certainty": actor.understanding.certainty_levels,
            "operation_count": len(self.actor_operations[actor_id]),
            "focus_areas": await self.knowledge.get_focus_areas(actor_id)
        }
    
    async def get_knowledge_state(self) -> Dict[str, Any]:
        """Get overall knowledge state."""
        return {
            "patterns": await self.knowledge.get_all_patterns(),
            "connections": await self.knowledge.get_all_connections(),
            "focus_areas": await self.knowledge.get_all_focus_areas(),
            "confidence": await self.knowledge.get_confidence_metrics()
        }
    
    async def terminate_actor(self, actor_id: str):
        """Clean up actor."""
        if actor_id not in self.actors:
            raise ValueError(f"Unknown actor: {actor_id}")
            
        # Save final knowledge with profile context
        actor = self.actors[actor_id]
        profile_name = self.actor_profiles[actor_id]
        focus_area = self.actor_focus[actor_id]
        
        await self.knowledge.integrate_understanding(
            actor.understanding.knowledge_state,
            {
                "profile": profile_name,
                "focus_area": focus_area,
                "actor_id": actor_id
            }
        )
        
        # Cleanup
        await actor.rest()
        del self.actors[actor_id]
        del self.actor_states[actor_id]
        del self.actor_profiles[actor_id]
        del self.actor_operations[actor_id]
        del self.actor_focus[actor_id]
    
    async def cleanup(self):
        """Clean up all actors."""
        for actor_id in list(self.actors.keys()):
            await self.terminate_actor(actor_id)
        await self.knowledge.save_state()