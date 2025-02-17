"""
End-to-end test demonstrating how the system learns from research and feedback.
Shows the core business value: Improving research quality through learning.
"""
import pytest
import asyncio
from datetime import datetime
import structlog

from nova_aegis.research_engine import ResearchEngine
from nova_aegis.tuning.parameter_store import UserFeedback

logger = structlog.get_logger()

@pytest.mark.asyncio
async def test_system_learns_from_feedback():
    """
    Test that the system improves research quality based on feedback.
    
    Business Value:
    - Users get better results over time
    - System learns from user feedback
    - Knowledge accumulates and improves
    """
    engine = ResearchEngine()
    
    # Step 1: Initial research without accumulated knowledge
    initial_results = await engine.research_topic(
        "how to handle errors in async code"
    )
    
    # Record initial quality
    initial_quality = len([
        r for r in initial_results
        if "async" in r.content and "error" in r.content
    ]) / len(initial_results)
    
    # Step 2: Provide feedback on results
    await engine.record_feedback(
        UserFeedback(
            query="how to handle errors in async code",
            results_quality=initial_quality,
            relevance_score=initial_quality,
            timestamp=datetime.now(),
            parameters=engine.get_current_parameters(),
            comments="Need more specific async error handling examples"
        )
    )
    
    # Step 3: Research similar topic
    refined_results = await engine.research_topic(
        "async function error handling patterns"
    )
    
    # Verify improvement
    refined_quality = len([
        r for r in refined_results
        if "async" in r.content and "error" in r.content
    ]) / len(refined_results)
    
    assert refined_quality > initial_quality, \
        "Results should improve after feedback"

@pytest.mark.asyncio
async def test_knowledge_accumulation():
    """
    Test that knowledge builds up and improves research.
    
    Business Value:
    - System retains useful information
    - Future searches benefit from past research
    - Related topics get better results
    """
    engine = ResearchEngine()
    
    # Step 1: Research a topic
    await engine.research_topic(
        "dependency injection patterns"
    )
    
    # Step 2: Research related topic
    related_results = await engine.research_topic(
        "inversion of control examples"
    )
    
    # Verify knowledge reuse
    assert any(
        "dependency" in r.content 
        for r in related_results
    ), "Should use related knowledge"
    
    # Step 3: Verify confidence in related results
    assert any(
        r.confidence > 0.8
        for r in related_results
    ), "Should have high confidence in related results"

@pytest.mark.asyncio
async def test_feedback_improves_relevance():
    """
    Test that user feedback leads to more relevant results.
    
    Business Value:
    - System adapts to user preferences
    - Results become more specific
    - Less irrelevant information
    """
    engine = ResearchEngine()
    
    # Step 1: Initial broad search
    initial_results = await engine.research_topic(
        "state management"
    )
    
    # Step 2: Provide feedback requesting specificity
    await engine.record_feedback(
        UserFeedback(
            query="state management",
            results_quality=0.6,
            relevance_score=0.5,
            timestamp=datetime.now(),
            parameters=engine.get_current_parameters(),
            comments="Need React-specific state management"
        )
    )
    
    # Step 3: More specific search
    specific_results = await engine.research_topic(
        "React state management patterns"
    )
    
    # Verify increased relevance
    assert len(specific_results) <= len(initial_results), \
        "Should be more selective"
    assert all(
        r.relevance_score > 0.7
        for r in specific_results
    ), "All results should be highly relevant"

@pytest.mark.asyncio
async def test_cross_domain_learning():
    """
    Test that learning transfers across related domains.
    
    Business Value:
    - Knowledge from one area helps in related areas
    - System recognizes similar patterns
    - Faster learning in related domains
    """
    engine = ResearchEngine()
    
    # Step 1: Learn about Python async
    await engine.research_topic("Python async patterns")
    
    # Step 2: Research JavaScript async
    js_results = await engine.research_topic(
        "JavaScript async/await patterns"
    )
    
    # Verify pattern recognition
    assert any(
        r.pattern_match > 0.8
        for r in js_results
    ), "Should recognize similar patterns"
    
    # Step 3: Verify knowledge transfer
    concepts = await engine.get_related_concepts(
        "async programming"
    )
    assert len(concepts) > 2, "Should accumulate cross-domain concepts"
    assert any(
        c.domain == "python" for c in concepts
    ), "Should include Python concepts"
    assert any(
        c.domain == "javascript" for c in concepts
    ), "Should include JavaScript concepts"