"""
ResearchScientist: Specialized cognitive actor for research tasks.
Analyzes information, builds knowledge, and explores topics systematically.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

from .cognitive_actor import CognitiveActor, Action
from ..graph.schema import SchemaManager
from ..graph.query_builder import QueryBuilder
from ..research_engine import ResearchEngine
from ..llm_interface import LLMInterface
from ..graph.visualization import GraphVisualizer

logger = structlog.get_logger()

class ResearchScientist(CognitiveActor):
    """Research-specialized cognitive actor."""
    
    def __init__(self):
        super().__init__()
        # Research capabilities
        self.knowledge = SchemaManager()
        self.curiosity = QueryBuilder()
        self.analysis = ResearchEngine()
        self.communication = LLMInterface()
        self.perception = GraphVisualizer()
        
        self.logger = logger.bind(component="scientist")
    
    async def _process_perception(self, perception: Perception) -> Dict[str, Any]:
        """Process perception using research capabilities."""
        try:
            # Extract initial understanding
            concepts = await self.communication.extract_concepts(
                perception.stimulus
            )
            
            # Create knowledge structure
            nodes = await self.knowledge.create_concept_nodes(concepts)
            
            # Queue for deeper processing
            return {
                "perception": perception,
                "initial_nodes": nodes
            }
            
        except Exception as e:
            self.logger.error("perception_failed", error=str(e))
            raise
    
    async def _generate_action(self, processed: Dict[str, Any]) -> Action:
        """Generate research actions from processed understanding."""
        try:
            perception = processed["perception"]
            initial_nodes = processed["initial_nodes"]
            
            # Analyze connections
            connections = await self.analysis.analyze_relationships(
                perception.stimulus,
                initial_nodes
            )
            
            # Integrate into knowledge
            knowledge_updates = await self.knowledge.create_relationships(
                connections
            )
            
            # Generate insights
            insights = await self.analysis.generate_insights(
                initial_nodes,
                connections
            )
            
            # Update understanding
            self._update_understanding(insights)
            
            # Generate responses
            responses = self._generate_responses(insights)
            
            # Choose highest priority response
            response = responses[0] if responses else {
                "type": "investigate",
                "query": "Tell me more about this topic"
            }
            
            return Action(
                response_type=response["type"],
                content=response.get("insight") or response.get("topic") or response["query"],
                confidence=self.understanding.certainty_levels.get(
                    response.get("insight", {}).get("id", ""), 0.5
                ),
                reasoning=insights,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error("action_failed", error=str(e))
            raise
    
    def _update_understanding(self, insights: List[Dict[str, Any]]):
        """Update current understanding."""
        # Update knowledge state
        self.understanding.knowledge_state = self.knowledge.get_current_state()
        
        # Update certainty levels
        for insight in insights:
            self.understanding.certainty_levels[insight["id"]] = insight["certainty"]
        
        # Update visual memory
        self.understanding.visual_memory = self.perception.get_current_view()
    
    def _generate_responses(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate responses based on insights."""
        responses = []
        
        # Generate investigations
        queries = self.curiosity.build_queries(insights)
        for query in queries:
            responses.append({
                "type": "investigate",
                "query": query
            })
        
        # Generate verifications
        for insight in insights:
            if insight["certainty"] < 0.8:
                responses.append({
                    "type": "verify",
                    "insight": insight
                })
        
        # Generate explorations
        topics = self.curiosity.suggest_explorations(insights)
        for topic in topics:
            responses.append({
                "type": "explore",
                "topic": topic
            })
        
        return responses
    
    async def rest(self) -> None:
        """Integrate knowledge during rest."""
        await self.knowledge.apply_updates(
            self.understanding.knowledge_state
        )