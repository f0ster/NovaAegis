"""
Integration test for parameter tuning system.
Tests both systematic optimization and user feedback (RLHF).
"""
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import structlog
from typing import Dict, Any

from nova_aegis.tuning.parameter_store import (
    ParameterStore,
    UserFeedback,
    ParameterConfig
)

logger = structlog.get_logger()

@pytest.fixture
async def param_store():
    """Create test parameter store."""
    # Use temporary path for test
    store = ParameterStore(Path("tests/data/test_params.json"))
    yield store
    # Cleanup
    if store.store_path.exists():
        store.store_path.unlink()

async def test_parameter_evolution():
    """
    Test how parameters evolve through feedback and optimization.
    Shows both systematic and user-driven improvements.
    """
    store = ParameterStore(Path("tests/data/evolution_test.json"))
    
    # Initial parameters
    initial_params = store.get_parameters()
    assert 0.0 <= initial_params["base_confidence"] <= 1.0
    assert 0.0 <= initial_params["relevance_threshold"] <= 1.0
    
    # Simulate research sessions with feedback
    research_sessions = [
        {
            "query": "async error handling",
            "quality": 0.6,
            "relevance": 0.7,
            "comment": "Good but could be more specific"
        },
        {
            "query": "dependency injection patterns",
            "quality": 0.8,
            "relevance": 0.9,
            "comment": "Excellent relevant results"
        },
        {
            "query": "microservices architecture",
            "quality": 0.4,
            "relevance": 0.5,
            "comment": "Too broad, needs refinement"
        }
    ]
    
    feedback_history = []
    
    # Process each session
    for session in research_sessions:
        # Record feedback
        feedback = UserFeedback(
            query=session["query"],
            results_quality=session["quality"],
            relevance_score=session["relevance"],
            timestamp=datetime.now(),
            parameters=store.get_parameters(),
            comments=session["comment"]
        )
        await store.record_feedback(feedback)
        feedback_history.append(feedback)
        
        # Allow parameter adjustment
        await asyncio.sleep(1)
        
        # Optimize based on metrics
        metrics = {
            "avg_quality": sum(f.results_quality for f in feedback_history) / len(feedback_history),
            "avg_relevance": sum(f.relevance_score for f in feedback_history) / len(feedback_history)
        }
        await store.optimize_parameters(metrics)
    
    # Verify parameter evolution
    final_params = store.get_parameters()
    
    # Parameters should adjust based on feedback
    assert final_params != initial_params, "Parameters should evolve"
    
    # Check optimization metrics improved
    assert store.state.optimization_metrics["avg_quality"] > 0.5, \
        "Quality should improve"
    assert store.state.optimization_metrics["avg_relevance"] > 0.6, \
        "Relevance should improve"
    
    # Verify history tracking
    assert len(store.state.history) >= len(research_sessions), \
        "Should track parameter history"
    assert len(store.state.feedback_history) == len(research_sessions), \
        "Should track all feedback"

async def test_domain_specific_tuning():
    """
    Test parameter tuning for specific domains.
    Shows how parameters adapt to different contexts.
    """
    store = ParameterStore(Path("tests/data/domain_test.json"))
    
    domains = ["python", "javascript", "devops"]
    
    for domain in domains:
        # Get domain parameters
        domain_params = store.get_parameters(domain=domain)
        
        # Simulate domain-specific feedback
        feedback = UserFeedback(
            query=f"{domain} best practices",
            results_quality=0.7,
            relevance_score=0.8,
            timestamp=datetime.now(),
            parameters=domain_params,
            comments=f"Good {domain} specific results"
        )
        await store.record_feedback(feedback)
        
        # Allow parameter adjustment
        await asyncio.sleep(1)
    
    # Verify domain-specific adaptation
    params_by_domain = {
        domain: store.get_parameters(domain=domain)
        for domain in domains
    }
    
    # Parameters should differ between domains
    assert len(set(
        str(params) for params in params_by_domain.values()
    )) > 1, "Should have domain-specific parameters"

async def test_feedback_driven_adjustment():
    """
    Test how user feedback drives parameter adjustment.
    Shows RLHF-style learning from user input.
    """
    store = ParameterStore(Path("tests/data/feedback_test.json"))
    
    # Initial state
    initial_params = store.get_parameters()
    
    # Simulate user feedback sequence
    feedbacks = [
        # User wants more specific results
        UserFeedback(
            query="testing strategies",
            results_quality=0.5,
            relevance_score=0.6,
            timestamp=datetime.now(),
            parameters=store.get_parameters(),
            comments="Too general, need more specific results"
        ),
        # System adjusted, results improved
        UserFeedback(
            query="unit testing patterns",
            results_quality=0.8,
            relevance_score=0.9,
            timestamp=datetime.now(),
            parameters=store.get_parameters(),
            comments="Much better, very relevant"
        ),
        # Maintaining high quality
        UserFeedback(
            query="integration testing best practices",
            results_quality=0.9,
            relevance_score=0.9,
            timestamp=datetime.now(),
            parameters=store.get_parameters(),
            comments="Excellent specific results"
        )
    ]
    
    # Process feedback sequence
    for feedback in feedbacks:
        await store.record_feedback(feedback)
        await asyncio.sleep(1)
    
    # Verify parameter adaptation
    final_params = store.get_parameters()
    
    # Relevance threshold should increase
    assert final_params["relevance_threshold"] > initial_params["relevance_threshold"], \
        "Should increase relevance threshold for specificity"
    
    # Base confidence should improve
    assert final_params["base_confidence"] > initial_params["base_confidence"], \
        "Should increase confidence with good feedback"
    
    # Verify feedback processing
    assert store.state.optimization_metrics["avg_quality"] > 0.7, \
        "Should show quality improvement"
    assert len(store.state.feedback_history) == len(feedbacks), \
        "Should track all feedback"

async def test_systematic_optimization():
    """
    Test systematic parameter optimization based on metrics.
    Shows data-driven parameter tuning.
    """
    store = ParameterStore(Path("tests/data/optimization_test.json"))
    
    # Track optimization progress
    optimization_steps = []
    
    # Run multiple optimization cycles
    for i in range(5):
        # Generate synthetic metrics
        metrics = {
            "avg_quality": 0.5 + (i * 0.1),  # Improving quality
            "avg_relevance": 0.6 + (i * 0.08),  # Improving relevance
            "success_rate": 0.7 + (i * 0.06)  # Improving success
        }
        
        # Optimize parameters
        await store.optimize_parameters(metrics)
        
        # Record state
        optimization_steps.append({
            "step": i,
            "metrics": metrics,
            "parameters": store.get_parameters()
        })
        
        await asyncio.sleep(1)
    
    # Verify optimization progress
    assert len(optimization_steps) == 5, "Should complete all steps"
    
    # Parameters should improve with metrics
    first_step = optimization_steps[0]["parameters"]
    last_step = optimization_steps[-1]["parameters"]
    
    # Confidence should increase with success
    assert last_step["base_confidence"] > first_step["base_confidence"], \
        "Should increase confidence with success"
    
    # Verify optimization history
    assert len(store.state.history) >= 5, "Should track optimization history"
    
    # Check metric improvements
    assert store.state.optimization_metrics["avg_quality"] > 0.7, \
        "Should improve quality"
    assert store.state.optimization_metrics["avg_relevance"] > 0.8, \
        "Should improve relevance"