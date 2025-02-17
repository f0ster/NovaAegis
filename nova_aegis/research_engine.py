"""
Core research engine for executing tasks and accumulating knowledge.
Handles task execution, learning, and knowledge management.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import structlog
from datetime import datetime

from .llm_interface import LLMInterface
from .graph.schema import SchemaManager
from .tuning.parameter_store import ParameterStore
from .structured_reasoning import PlanBuilder

logger = structlog.get_logger()

@dataclass
class ResearchResult:
    """Result from research execution."""
    content: str
    confidence: float
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class KnowledgeState:
    """Current state of accumulated knowledge."""
    concepts: Dict[str, Any]
    patterns: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    metrics: Dict[str, float]

class ResearchEngine:
    """
    Core engine for executing research tasks and managing knowledge.
    Coordinates between LLM, knowledge graph, and parameter tuning.
    """
    
    def __init__(self):
        self.llm = LLMInterface()
        self.schema = SchemaManager()
        self.params = ParameterStore()
        self.planner = PlanBuilder()
        self.logger = logger.bind(component="research_engine")
        
        # Track execution state
        self.current_context = None
        self.current_plan = None
    
    async def execute_step(
        self,
        step: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single research step."""
        try:
            # Get current parameters
            params = self.params.get_parameters()
            
            # Execute based on step type
            if step.startswith("collect"):
                return await self._execute_collection(step, context, params)
                
            elif step.startswith("process"):
                return await self._execute_processing(step, context, params)
                
            elif step.startswith("analyze"):
                return await self._execute_analysis(step, context, params)
                
            elif step.startswith("synthesize"):
                return await self._execute_synthesis(step, context, params)
            
            else:
                raise ValueError(f"Unknown step type: {step}")
                
        except Exception as e:
            self.logger.error("step_execution_failed", error=str(e))
            raise
    
    async def generate_insights(
        self,
        results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate insights from research results."""
        try:
            # Extract patterns
            patterns = await self._extract_patterns(results)
            
            # Generate initial insights
            insights = await self.llm.generate_insights(
                results=results,
                patterns=patterns,
                context=context
            )
            
            # Validate and enhance insights
            enhanced_insights = []
            for insight in insights:
                # Validate against existing knowledge
                if await self._validate_insight(insight):
                    # Enhance with relationships
                    enhanced = await self._enhance_insight(insight)
                    enhanced_insights.append(enhanced)
            
            # Store in knowledge graph
            await self._store_insights(enhanced_insights)
            
            return enhanced_insights
            
        except Exception as e:
            self.logger.error("insight_generation_failed", error=str(e))
            raise
    
    def get_knowledge_state(self) -> KnowledgeState:
        """Get current state of accumulated knowledge."""
        try:
            # Get core components
            concepts = self.schema.get_all_concepts()
            patterns = self.schema.get_all_patterns()
            relationships = self.schema.get_all_relationships()
            
            # Calculate metrics
            metrics = {
                "concept_coverage": len(concepts) / 100,  # Normalized
                "pattern_confidence": self._calculate_pattern_confidence(patterns),
                "relationship_density": self._calculate_relationship_density(
                    concepts,
                    relationships
                ),
                "knowledge_coherence": self._calculate_coherence(
                    concepts,
                    patterns,
                    relationships
                )
            }
            
            return KnowledgeState(
                concepts=concepts,
                patterns=patterns,
                relationships=relationships,
                metrics=metrics
            )
            
        except Exception as e:
            self.logger.error("knowledge_state_failed", error=str(e))
            raise
    
    async def _execute_collection(
        self,
        step: str,
        context: Dict[str, Any],
        params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Execute collection step."""
        # Extract source information
        source_info = await self.llm.extract_source_info(context)
        
        # Collect raw content
        results = []
        for source in source_info:
            content = await self._collect_from_source(
                source,
                params["base_confidence"]
            )
            if content:
                results.append(content)
        
        return {
            "raw_content": results,
            "source_info": source_info
        }
    
    async def _execute_processing(
        self,
        step: str,
        context: Dict[str, Any],
        params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Execute processing step."""
        # Extract key information
        extracted = await self.llm.extract_information(
            context["raw_content"],
            min_confidence=params["base_confidence"]
        )
        
        # Build relationships
        relationships = await self._build_relationships(
            extracted,
            min_confidence=params["relevance_threshold"]
        )
        
        return {
            "extracted": extracted,
            "relationships": relationships
        }
    
    async def _execute_analysis(
        self,
        step: str,
        context: Dict[str, Any],
        params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Execute analysis step."""
        # Analyze patterns
        patterns = await self._analyze_patterns(
            context["extracted"],
            min_confidence=params["base_confidence"]
        )
        
        # Generate insights
        insights = await self.llm.generate_insights(
            context["extracted"],
            patterns=patterns,
            min_confidence=params["relevance_threshold"]
        )
        
        return {
            "patterns": patterns,
            "insights": insights
        }
    
    async def _execute_synthesis(
        self,
        step: str,
        context: Dict[str, Any],
        params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Execute synthesis step."""
        # Synthesize findings
        synthesis = await self.llm.synthesize_findings(
            insights=context["insights"],
            patterns=context["patterns"],
            min_confidence=params["base_confidence"]
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            synthesis,
            min_confidence=params["relevance_threshold"]
        )
        
        return {
            "synthesis": synthesis,
            "recommendations": recommendations
        }
    
    async def _validate_insight(
        self,
        insight: Dict[str, Any]
    ) -> bool:
        """Validate insight against existing knowledge."""
        # Check confidence
        if insight.get("confidence", 0) < 0.5:
            return False
            
        # Check for contradictions
        contradictions = await self.schema.find_contradictions(insight)
        if contradictions:
            return False
            
        # Check support
        support = await self.schema.find_supporting_evidence(insight)
        return len(support) > 0
    
    async def _enhance_insight(
        self,
        insight: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance insight with relationships and metadata."""
        # Add relationships
        relationships = await self.schema.find_relationships(insight)
        insight["relationships"] = relationships
        
        # Add metadata
        metadata = await self._generate_metadata(insight)
        insight["metadata"] = metadata
        
        return insight
    
    def _calculate_pattern_confidence(
        self,
        patterns: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence in patterns."""
        if not patterns:
            return 0.0
            
        confidences = [
            p.get("confidence", 0)
            for p in patterns.values()
        ]
        return sum(confidences) / len(confidences)
    
    def _calculate_relationship_density(
        self,
        concepts: Dict[str, Any],
        relationships: List[Dict[str, Any]]
    ) -> float:
        """Calculate density of knowledge graph."""
        if not concepts:
            return 0.0
            
        max_relationships = len(concepts) * (len(concepts) - 1) / 2
        return len(relationships) / max_relationships
    
    def _calculate_coherence(
        self,
        concepts: Dict[str, Any],
        patterns: Dict[str, Any],
        relationships: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall coherence of knowledge."""
        # Start with pattern confidence
        coherence = self._calculate_pattern_confidence(patterns)
        
        # Factor in relationship density
        density = self._calculate_relationship_density(concepts, relationships)
        coherence = (coherence + density) / 2
        
        # Adjust for contradictions
        contradictions = sum(
            1 for r in relationships
            if r.get("type") == "contradicts"
        )
        if contradictions:
            coherence *= (1 - (contradictions / len(relationships)))
        
        return coherence