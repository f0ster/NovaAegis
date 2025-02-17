"""
Parameter store for tracking and evolving confidence settings.
Supports both systematic optimization and user feedback (RLHF).
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import structlog
import numpy as np
from pydantic import BaseModel

logger = structlog.get_logger()

@dataclass
class ParameterConfig:
    """Configuration for a tunable parameter."""
    name: str
    min_value: float
    max_value: float
    step_size: float
    description: str
    domain: Optional[str] = None

@dataclass
class UserFeedback:
    """User feedback on research results."""
    query: str
    results_quality: float  # 0-1 score
    relevance_score: float  # 0-1 score
    timestamp: datetime
    parameters: Dict[str, float]
    comments: Optional[str] = None

class ParameterState(BaseModel):
    """Current state of parameters with history."""
    current_values: Dict[str, float]
    history: List[Dict[str, Any]]
    feedback_history: List[Dict[str, Any]]
    optimization_metrics: Dict[str, float]

class ParameterStore:
    """Manages parameter evolution and optimization."""
    
    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or Path("data/parameters.json")
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Default parameters
        self.parameters = {
            "base_confidence": ParameterConfig(
                name="base_confidence",
                min_value=0.1,
                max_value=1.0,
                step_size=0.05,
                description="Base confidence threshold for accepting results"
            ),
            "relevance_threshold": ParameterConfig(
                name="relevance_threshold",
                min_value=0.3,
                max_value=0.9,
                step_size=0.05,
                description="Minimum relevance score for results"
            ),
            "knowledge_weight": ParameterConfig(
                name="knowledge_weight",
                min_value=0.1,
                max_value=2.0,
                step_size=0.1,
                description="Weight given to existing knowledge"
            ),
            "exploration_rate": ParameterConfig(
                name="exploration_rate",
                min_value=0.0,
                max_value=0.5,
                step_size=0.05,
                description="Rate of exploring new patterns"
            )
        }
        
        # Domain-specific parameters
        self.domain_parameters = {}
        
        # Load or initialize state
        self.state = self._load_state()
        
        self.logger = logger.bind(component="parameter_store")
    
    def get_parameters(self, domain: Optional[str] = None) -> Dict[str, float]:
        """Get current parameter values, optionally for specific domain."""
        base_params = self.state.current_values.copy()
        
        if domain and domain in self.domain_parameters:
            # Merge with domain-specific parameters
            domain_params = self.domain_parameters[domain]
            base_params.update(domain_params)
        
        return base_params
    
    async def record_feedback(self, feedback: UserFeedback):
        """Record and process user feedback."""
        try:
            # Store feedback
            feedback_dict = {
                "query": feedback.query,
                "results_quality": feedback.results_quality,
                "relevance_score": feedback.relevance_score,
                "timestamp": feedback.timestamp.isoformat(),
                "parameters": feedback.parameters,
                "comments": feedback.comments
            }
            self.state.feedback_history.append(feedback_dict)
            
            # Update optimization metrics
            self._update_metrics(feedback)
            
            # Adjust parameters based on feedback
            await self._adjust_parameters(feedback)
            
            # Save state
            self._save_state()
            
            self.logger.info(
                "feedback_recorded",
                query=feedback.query,
                quality=feedback.results_quality
            )
            
        except Exception as e:
            self.logger.error("feedback_recording_failed", error=str(e))
            raise
    
    async def optimize_parameters(self, metrics: Dict[str, float]):
        """Systematically optimize parameters based on metrics."""
        try:
            current_values = self.state.current_values.copy()
            
            # Calculate parameter adjustments
            adjustments = self._calculate_adjustments(metrics)
            
            # Apply adjustments within bounds
            for param, adjustment in adjustments.items():
                if param in self.parameters:
                    config = self.parameters[param]
                    current = current_values[param]
                    
                    # Apply adjustment with bounds
                    new_value = max(
                        config.min_value,
                        min(
                            config.max_value,
                            current + adjustment
                        )
                    )
                    
                    # Round to step size
                    steps = round(new_value / config.step_size)
                    current_values[param] = steps * config.step_size
            
            # Record history
            self.state.history.append({
                "timestamp": datetime.now().isoformat(),
                "values": self.state.current_values.copy(),
                "metrics": metrics.copy()
            })
            
            # Update current values
            self.state.current_values = current_values
            
            # Save state
            self._save_state()
            
            self.logger.info(
                "parameters_optimized",
                adjustments=adjustments
            )
            
        except Exception as e:
            self.logger.error("optimization_failed", error=str(e))
            raise
    
    def _load_state(self) -> ParameterState:
        """Load or initialize parameter state."""
        if self.store_path.exists():
            data = json.loads(self.store_path.read_text())
            return ParameterState(**data)
        
        # Initialize with defaults
        return ParameterState(
            current_values={
                name: config.min_value + (
                    (config.max_value - config.min_value) * 0.5
                )
                for name, config in self.parameters.items()
            },
            history=[],
            feedback_history=[],
            optimization_metrics={
                "avg_quality": 0.0,
                "avg_relevance": 0.0,
                "feedback_count": 0
            }
        )
    
    def _save_state(self):
        """Save current state to disk."""
        self.store_path.write_text(
            self.state.model_dump_json(indent=2)
        )
    
    def _update_metrics(self, feedback: UserFeedback):
        """Update optimization metrics with new feedback."""
        metrics = self.state.optimization_metrics
        count = metrics["feedback_count"]
        
        # Update running averages
        metrics["avg_quality"] = (
            (metrics["avg_quality"] * count + feedback.results_quality) /
            (count + 1)
        )
        metrics["avg_relevance"] = (
            (metrics["avg_relevance"] * count + feedback.relevance_score) /
            (count + 1)
        )
        metrics["feedback_count"] = count + 1
    
    async def _adjust_parameters(self, feedback: UserFeedback):
        """Adjust parameters based on feedback."""
        # Calculate quality-based adjustments
        quality_factor = feedback.results_quality - 0.5  # Center around 0
        
        adjustments = {}
        for param, value in feedback.parameters.items():
            if param in self.parameters:
                config = self.parameters[param]
                
                # Calculate adjustment
                adjustment = quality_factor * config.step_size
                
                # Apply bounds
                new_value = max(
                    config.min_value,
                    min(
                        config.max_value,
                        value + adjustment
                    )
                )
                
                adjustments[param] = new_value
        
        # Update values
        self.state.current_values.update(adjustments)
    
    def _calculate_adjustments(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate parameter adjustments based on metrics."""
        adjustments = {}
        
        # Use recent history for trends
        recent_history = self.state.history[-10:] if self.state.history else []
        
        for param in self.state.current_values:
            if param in self.parameters:
                config = self.parameters[param]
                
                # Calculate trend
                if recent_history:
                    values = [h["values"][param] for h in recent_history]
                    metrics_values = [
                        h["metrics"].get("avg_quality", 0)
                        for h in recent_history
                    ]
                    
                    # Calculate correlation
                    correlation = np.corrcoef(values, metrics_values)[0, 1]
                    
                    # Adjust based on correlation
                    adjustment = (
                        np.sign(correlation) *
                        config.step_size *
                        abs(correlation)
                    )
                else:
                    adjustment = 0
                
                adjustments[param] = adjustment
        
        return adjustments