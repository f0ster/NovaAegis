"""
End-to-end test demonstrating confidence parameter tuning during research.
Shows how CrewAI agents monitor and adjust confidence based on results.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import structlog
from langchain.chat_models import ChatOpenAI

from nova_aegis.research_engine import ResearchEngine
from nova_aegis.tuning.confidence_crew import (
    ConfidenceCrew,
    ConfidenceMetrics
)

logger = structlog.get_logger()

class TestConfidenceTuning:
    """Test confidence parameter tuning during research tasks."""
    
    @pytest.fixture
    async def research_setup(self):
        """Set up research components."""
        llm = ChatOpenAI(temperature=0)
        engine = ResearchEngine()
        crew = ConfidenceCrew(llm)
        return engine, crew
    
    async def test_confidence_tuning_loop(self, research_setup):
        """
        Test complete confidence tuning loop during research.
        Shows how parameters are adjusted based on research results.
        """
        engine, crew = research_setup
        
        # Initial confidence parameters
        params = {
            "similarity_threshold": 0.7,
            "relevance_threshold": 0.6,
            "relationship_confidence": 0.8
        }
        
        # Research topics to evaluate tuning
        topics = [
            "async error handling",
            "dependency injection",
            "state management",
            "data validation"
        ]
        
        metrics_history = []
        
        # Run research with parameter tuning
        for topic in topics:
            # Do research with current parameters
            results = await engine.research_code(
                query=topic,
                confidence_params=params
            )
            
            # Collect metrics from this run
            run_metrics = [
                ConfidenceMetrics(
                    parameter_name="similarity_threshold",
                    current_value=params["similarity_threshold"],
                    success_rate=len([r for r in results if r.is_relevant]) / len(results),
                    false_positives=len([r for r in results if not r.is_relevant]),
                    false_negatives=0,  # Would need ground truth
                    timestamp=datetime.now(),
                    context={"topic": topic}
                ),
                ConfidenceMetrics(
                    parameter_name="relevance_threshold",
                    current_value=params["relevance_threshold"],
                    success_rate=len([r for r in results if r.matches_query]) / len(results),
                    false_positives=len([r for r in results if not r.matches_query]),
                    false_negatives=0,
                    timestamp=datetime.now(),
                    context={"topic": topic}
                )
            ]
            
            metrics_history.extend(run_metrics)
            
            # Tune parameters based on accumulated metrics
            new_params = await crew.tune_parameters(
                metrics=metrics_history[-10:],  # Use recent history
                current_params=params
            )
            
            if new_params:
                # Verify parameter changes are reasonable
                for name, value in new_params.items():
                    assert abs(value - params[name]) < 0.2, \
                        f"Parameter {name} changed too drastically"
                
                # Update parameters for next run
                params = new_params
            
            # Log progress
            logger.info(
                "research_iteration_complete",
                topic=topic,
                params=params,
                results=len(results)
            )
        
        # Verify tuning improved results
        early_success = sum(m.success_rate for m in metrics_history[:4]) / 4
        late_success = sum(m.success_rate for m in metrics_history[-4:]) / 4
        assert late_success > early_success, \
            "Tuning should improve success rate"
    
    async def test_parameter_stability(self, research_setup):
        """
        Test that parameter tuning maintains stability.
        Ensures changes are gradual and well-validated.
        """
        engine, crew = research_setup
        
        # Run multiple tuning iterations on same topic
        topic = "error handling patterns"
        params = {
            "similarity_threshold": 0.7,
            "relevance_threshold": 0.6
        }
        
        param_history = []
        
        for _ in range(5):
            # Research with current parameters
            results = await engine.research_code(
                query=topic,
                confidence_params=params
            )
            
            # Collect metrics
            metrics = [
                ConfidenceMetrics(
                    parameter_name=name,
                    current_value=value,
                    success_rate=len([r for r in results if r.is_relevant]) / len(results),
                    false_positives=len([r for r in results if not r.is_relevant]),
                    false_negatives=0,
                    timestamp=datetime.now(),
                    context={"topic": topic}
                )
                for name, value in params.items()
            ]
            
            # Tune parameters
            new_params = await crew.tune_parameters(
                metrics=metrics,
                current_params=params
            )
            
            if new_params:
                params = new_params
            
            param_history.append(params.copy())
        
        # Verify parameter stability
        for name in params:
            values = [p[name] for p in param_history]
            max_change = max(abs(a - b) for a, b in zip(values[:-1], values[1:]))
            assert max_change < 0.1, \
                f"Parameter {name} showed unstable changes"
    
    async def test_feedback_incorporation(self, research_setup):
        """
        Test how feedback affects parameter tuning.
        Shows adaptation to explicit feedback signals.
        """
        engine, crew = research_setup
        
        # Initial research
        params = {
            "similarity_threshold": 0.7,
            "relevance_threshold": 0.6
        }
        
        results = await engine.research_code(
            query="dependency injection patterns",
            confidence_params=params
        )
        
        # Simulate feedback
        feedback_metrics = [
            ConfidenceMetrics(
                parameter_name="similarity_threshold",
                current_value=params["similarity_threshold"],
                success_rate=0.6,  # Lower than expected
                false_positives=5,  # Too many irrelevant results
                false_negatives=1,
                timestamp=datetime.now(),
                context={
                    "feedback": "Too many similar but irrelevant results"
                }
            )
        ]
        
        # Tune based on feedback
        new_params = await crew.tune_parameters(
            metrics=feedback_metrics,
            current_params=params
        )
        
        assert new_params["similarity_threshold"] > params["similarity_threshold"], \
            "Should increase threshold after feedback about irrelevant results"