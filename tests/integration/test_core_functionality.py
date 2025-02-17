"""
Integration tests for core system functionality.
Tests real research, knowledge storage, and learning capabilities.
"""
import pytest
import asyncio
from pathlib import Path
import structlog
from typing import List, Dict, Any

from nova_aegis.research_engine import ResearchEngine
from nova_aegis.llm_interface import LLMInterface
from nova_aegis.tuning.confidence_crew import ConfidenceCrew
from nova_aegis.graph.schema import SchemaManager

logger = structlog.get_logger()

@pytest.fixture(scope="module")
async def setup_knowledge_base():
    """Set up fresh knowledge base for testing."""
    schema = SchemaManager(space_name="test_knowledge")
    await schema.init_schema()
    
    # Clear any existing data
    await schema.execute_query("CLEAR SPACE test_knowledge")
    
    return schema

@pytest.mark.asyncio
async def test_research_and_storage(setup_knowledge_base):
    """
    Test that research results are properly stored and retrievable.
    Uses real code research and knowledge graph storage.
    """
    engine = ResearchEngine()
    
    # Research a specific pattern
    results = await engine.research_code(
        query="async error handling patterns python",
        min_relevance=0.6
    )
    
    # Verify research results
    assert len(results) > 0, "Should find research results"
    assert any("async" in r.code_segment for r in results), \
        "Should find async-related code"
    assert any("error" in r.code_segment.lower() for r in results), \
        "Should find error handling code"
    
    # Verify storage
    stored_results = await engine.get_stored_results(
        [r.id for r in results]
    )
    assert len(stored_results) == len(results), \
        "All results should be stored"
    
    # Verify relationships
    relationships = await engine.get_result_relationships(results[0].id)
    assert len(relationships) > 0, \
        "Should create relationships between results"

@pytest.mark.asyncio
async def test_llm_integration():
    """
    Test LLM integration with real responses.
    Verifies code understanding and explanation capabilities.
    """
    llm = LLMInterface()
    
    # Test code understanding
    code = """
    async def fetch_data(url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"API error: {response.status}")
                return await response.json()
    """
    
    explanation = await llm.generate_with_context(
        prompt="Explain this code's error handling approach",
        context={"code": code, "language": "python"}
    )
    
    # Verify explanation quality
    assert len(explanation) > 100, "Should provide detailed explanation"
    assert "error" in explanation.lower(), "Should discuss error handling"
    assert "status" in explanation.lower(), "Should mention status checks"
    
    # Test pattern recognition
    patterns = await llm.extract_patterns(code)
    assert len(patterns) > 0, "Should identify code patterns"
    assert any("async" in p.name.lower() for p in patterns), \
        "Should recognize async pattern"

@pytest.mark.asyncio
async def test_confidence_tuning():
    """
    Test confidence tuning with measurable improvements.
    Shows how the system learns from results.
    """
    engine = ResearchEngine()
    crew = ConfidenceCrew(LLMInterface())
    
    # Initial research with lower confidence
    initial_results = await engine.research_code(
        query="dependency injection patterns",
        min_confidence=0.5
    )
    
    initial_metrics = {
        "relevance": engine.calculate_relevance(initial_results),
        "confidence": engine.get_average_confidence()
    }
    
    # Let system learn from results
    await crew.analyze_results(initial_results)
    await asyncio.sleep(1)  # Allow time for analysis
    
    # Research again with tuned parameters
    tuned_results = await engine.research_code(
        query="dependency injection patterns",
        min_confidence=0.7  # Higher threshold after tuning
    )
    
    tuned_metrics = {
        "relevance": engine.calculate_relevance(tuned_results),
        "confidence": engine.get_average_confidence()
    }
    
    # Verify improvements
    assert tuned_metrics["relevance"] > initial_metrics["relevance"], \
        "Result relevance should improve"
    assert tuned_metrics["confidence"] > initial_metrics["confidence"], \
        "Confidence should increase"
    
    # Verify result quality
    assert len(tuned_results) <= len(initial_results), \
        "Should be more selective with results"
    assert all(r.confidence > 0.7 for r in tuned_results), \
        "All results should meet confidence threshold"

@pytest.mark.asyncio
async def test_knowledge_accumulation():
    """
    Test how knowledge accumulates and improves over time.
    Shows learning through multiple research iterations.
    """
    engine = ResearchEngine()
    
    # Track knowledge state
    knowledge_states = []
    
    # Research related topics
    topics = [
        "basic error handling",
        "async error handling",
        "error handling with validation",
        "complete error handling system"
    ]
    
    for topic in topics:
        # Research with accumulated knowledge
        results = await engine.research_code(
            query=topic,
            use_accumulated_knowledge=True
        )
        
        # Store results
        await engine.store_research_results(results)
        
        # Record knowledge state
        state = {
            "topic": topic,
            "results_count": len(results),
            "patterns": len(await engine.get_stored_patterns()),
            "relationships": len(await engine.get_relationships()),
            "confidence": engine.get_average_confidence()
        }
        knowledge_states.append(state)
        
        # Allow knowledge integration
        await asyncio.sleep(1)
    
    # Verify knowledge growth
    assert knowledge_states[-1]["patterns"] > knowledge_states[0]["patterns"], \
        "Should accumulate patterns"
    assert knowledge_states[-1]["relationships"] > knowledge_states[0]["relationships"], \
        "Should build relationships"
    assert knowledge_states[-1]["confidence"] > knowledge_states[0]["confidence"], \
        "Should increase confidence"
    
    # Verify knowledge quality
    final_state = knowledge_states[-1]
    assert final_state["confidence"] > 0.8, \
        "Should achieve high confidence"
    assert engine.get_knowledge_coherence() > 0.7, \
        "Should maintain knowledge coherence"

@pytest.mark.asyncio
async def test_cross_domain_learning():
    """
    Test learning and adaptation across different domains.
    Shows how patterns are recognized and adapted.
    """
    engine = ResearchEngine()
    
    # Research in multiple domains
    domains = {
        "async": "asynchronous programming patterns",
        "security": "security validation patterns",
        "state": "state management patterns"
    }
    
    domain_results = {}
    for domain, query in domains.items():
        results = await engine.research_code(query)
        domain_results[domain] = results
        
        # Build domain understanding
        await engine.analyze_domain_patterns(results, domain)
        await asyncio.sleep(1)
    
    # Verify domain separation
    for domain in domains:
        patterns = await engine.get_domain_patterns(domain)
        assert len(patterns) > 0, f"Should find patterns for {domain}"
        
        # Check domain relevance
        relevance = await engine.calculate_domain_relevance(
            patterns,
            domain
        )
        assert relevance > 0.7, \
            f"Patterns should be relevant to {domain}"
    
    # Test cross-domain learning
    crossover_patterns = await engine.find_cross_domain_patterns()
    assert len(crossover_patterns) > 0, \
        "Should identify cross-domain patterns"
    
    # Verify pattern adaptation
    for pattern in crossover_patterns:
        adaptations = await pattern.get_domain_adaptations()
        assert len(adaptations) > 1, \
            "Patterns should adapt across domains"
        assert all(a.confidence > 0.6 for a in adaptations), \
            "Adaptations should maintain confidence"