"""
NovaAegis: A personification of the ExplorationCompanion.
Provides a friendly interface to the companion's capabilities.
Like Data's personality interface in Star Trek.
"""
from typing import Dict, Any, List, Optional
import asyncio
import structlog
from datetime import datetime

from .core.companion import ExplorationCompanion, Perception, Understanding
from .graph.visualization import GraphVisualizer
from .web.app import create_app

logger = structlog.get_logger()

class NovaAegis:
    """
    NovaAegis - A friendly research companion.
    Personifies the ExplorationCompanion's capabilities with a helpful personality.
    """
    
    def __init__(self):
        # Core companion
        self.companion = ExplorationCompanion()
        self.visualizer = GraphVisualizer()
        
        # Personality traits
        self.curiosity_threshold = 0.7
        self.certainty_preference = 0.8
        self.exploration_eagerness = 0.6
        
        # Interaction state
        self.current_focus = None
        self.conversation_context = []
        self.visual_memory = {}
        
        self.logger = logger.bind(component="nova_aegis")
    
    async def greet(self) -> str:
        """Greet the user with NovaAegis's personality."""
        return (
            "Hello, I'm NovaAegis. I'd be happy to explore and learn with you. "
            "I'm particularly curious about new ideas and patterns, "
            "and I'll help visualize what we discover together."
        )
    
    async def start_session(self):
        """Start a new research session."""
        # Awaken companion
        await self.companion.awaken()
        
        # Start web interface
        self.app = create_app()
        
        # Initialize visual context
        self.visual_memory["session_start"] = datetime.now()
        
        self.logger.info("session_started")
    
    async def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process user request with NovaAegis's personality."""
        try:
            # Add to conversation context
            self.conversation_context.append({
                "role": "user",
                "content": request,
                "timestamp": datetime.now()
            })
            
            # Let companion perceive request
            await self.companion.perceive(
                request,
                context or {}
            )
            
            # Wait for initial processing
            understanding = await self._wait_for_understanding()
            
            # Generate response with personality
            response = await self._generate_response(
                request,
                understanding
            )
            
            # Add visual context
            response["visual"] = self.visualizer.get_current_view()
            
            # Add to conversation
            self.conversation_context.append({
                "role": "assistant",
                "content": response["message"],
                "timestamp": datetime.now()
            })
            
            return response
            
        except Exception as e:
            self.logger.error("request_processing_failed", error=str(e))
            return {
                "message": "I apologize, I had trouble processing that. Could you rephrase?",
                "error": str(e)
            }
    
    async def _wait_for_understanding(self) -> Understanding:
        """Wait for companion to process and understand."""
        # Give companion time to process
        await asyncio.sleep(0.1)
        
        # Get current understanding
        return self.companion.understanding
    
    async def _generate_response(
        self,
        request: str,
        understanding: Understanding
    ) -> Dict[str, Any]:
        """Generate response with NovaAegis's personality."""
        response = {
            "message": "",
            "insights": [],
            "suggestions": []
        }
        
        # Check certainty levels
        uncertain_concepts = [
            concept for concept, certainty 
            in understanding.certainty_levels.items()
            if certainty < self.certainty_preference
        ]
        
        if uncertain_concepts:
            # Express curiosity about uncertainties
            response["message"] += (
                "I'm curious to learn more about "
                f"{', '.join(uncertain_concepts)}. "
            )
        
        # Share insights
        if understanding.knowledge_state:
            insights = self._extract_key_insights(understanding)
            response["insights"] = insights
            
            response["message"] += (
                "Based on what we've explored, "
                f"I've noticed {len(insights)} interesting patterns. "
            )
        
        # Suggest explorations
        if understanding.curiosities:
            suggestions = self._generate_suggestions(
                understanding.curiosities
            )
            response["suggestions"] = suggestions
            
            response["message"] += (
                "Would you like to explore "
                f"{suggestions[0]['topic']} together?"
            )
        
        return response
    
    def _extract_key_insights(
        self,
        understanding: Understanding
    ) -> List[Dict[str, Any]]:
        """Extract key insights with NovaAegis's perspective."""
        insights = []
        
        # Look for patterns
        for concept, state in understanding.knowledge_state.items():
            if state.get("connections", 0) >= 3:
                insights.append({
                    "type": "pattern",
                    "concept": concept,
                    "description": f"I've noticed {concept} appears in multiple contexts",
                    "certainty": understanding.certainty_levels.get(concept, 0.5)
                })
        
        # Look for novel combinations
        for curiosity in understanding.curiosities:
            if "combine" in curiosity:
                insights.append({
                    "type": "combination",
                    "description": f"We might discover something interesting if we {curiosity}",
                    "certainty": 0.6
                })
        
        return insights
    
    def _generate_suggestions(
        self,
        curiosities: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate exploration suggestions with NovaAegis's curiosity."""
        suggestions = []
        
        for curiosity in curiosities:
            if len(suggestions) >= 3:
                break
                
            # Only suggest things we're eager about
            if random.random() < self.exploration_eagerness:
                suggestions.append({
                    "topic": curiosity,
                    "reason": "I think this could lead to interesting insights",
                    "eagerness": random.uniform(0.6, 0.9)
                })
        
        return suggestions
    
    async def end_session(self):
        """End research session."""
        # Let companion rest
        await self.companion.rest()
        
        # Save session summary
        self._save_session_summary()
        
        self.logger.info("session_ended")
    
    def _save_session_summary(self):
        """Save session summary with NovaAegis's perspective."""
        summary = {
            "session": {
                "start": self.visual_memory["session_start"],
                "end": datetime.now()
            },
            "conversation": self.conversation_context,
            "learnings": self.companion.understanding.knowledge_state,
            "visual_journey": self.visual_memory
        }
        
        # Save summary
        # TODO: Implement summary storage
        pass