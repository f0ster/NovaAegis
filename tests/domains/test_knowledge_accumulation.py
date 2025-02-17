"""
Domain-driven tests for knowledge accumulation behavior.
Shows how the system learns and refines understanding through research chains.
"""
import pytest
import asyncio
from typing import List, Dict, Any
import structlog
from datetime import datetime

from nova_aegis.research_engine import ResearchEngine
from nova_aegis.tuning.confidence_crew import ConfidenceCrew
from nova_aegis.llm_interface import LLMInterface

logger = structlog.get_logger()

async def test_knowledge_chain_refinement():
    """
    Test how knowledge is refined through chained research.
    Shows actual learning behavior through multiple research steps.
    """
    engine = ResearchEngine()
    llm = LLMInterface()
    
    # Initial research on error handling
    results = await engine.research_code(
        query="error handling best practices",
        min_relevance=0.5  # Start with lower threshold
    )
    
    # Extract core concepts
    concepts = await llm.extract_concepts(
        [r.code_segment for r in results]
    )
    
    # First refinement: Research each concept
    concept_results = {}
    for concept in concepts:
        concept_results[concept] = await engine.research_code(
            query=f"{concept} implementation patterns",
            min_relevance=0.7  # Higher threshold for specific concepts
        )
        
        # Allow knowledge accumulation
        await asyncio.sleep(1)
    
    # Verify knowledge improvement
    assert len(engine.get_stored_patterns()) > len(results)
    assert engine.get_average_confidence() > 0.6
    
    # Second refinement: Cross-reference implementations
    for concept, implementations in concept_results.items():
        relationships = await engine.find_implementation_relationships(
            implementations
        )
        
        # Store and analyze relationships
        for rel in relationships:
            await engine.store_relationship(
                rel.source_id,
                rel.target_id,
                rel.relation_type,
                rel.confidence
            )
    
    # Verify relationship learning
    assert len(engine.get_relationships()) > 0
    assert engine.get_relationship_confidence() > 0.5
    
    # Third refinement: Use accumulated knowledge
    enhanced_results = await engine.research_code(
        query="error handling",  # Same as initial query
        use_accumulated_knowledge=True
    )
    
    # Verify knowledge application
    assert len(enhanced_results) >= len(results)
    assert engine.get_result_relevance(enhanced_results) > \
           engine.get_result_relevance(results)

async def test_domain_specific_learning():
    """
    Test how the system builds domain-specific knowledge.
    Shows specialization and cross-domain learning.
    """
    engine = ResearchEngine()
    
    # Research in multiple domains
    domains = {
        "async": "asynchronous programming patterns",
        "security": "security validation patterns",
        "state": "state management patterns"
    }
    
    domain_knowledge = {}
    for domain, query in domains.items():
        # Initial domain research
        results = await engine.research_code(query)
        domain_knowledge[domain] = results
        
        # Build domain understanding
        await engine.analyze_domain_patterns(results, domain)
        
        # Allow knowledge processing
        await asyncio.sleep(1)
    
    # Verify domain separation
    for domain in domains:
        patterns = engine.get_domain_patterns(domain)
        assert len(patterns) > 0
        
        # Check domain relevance
        relevance = engine.calculate_domain_relevance(
            patterns,
            domain
        )
        assert relevance > 0.7
    
    # Test cross-domain learning
    crossover_patterns = engine.find_cross_domain_patterns()
    assert len(crossover_patterns) > 0
    
    # Verify pattern specialization
    for pattern in crossover_patterns:
        adaptations = pattern.get_domain_adaptations()
        assert len(adaptations) > 1
        assert all(a.confidence > 0.6 for a in adaptations)

async def test_confidence_based_refinement():
    """
    Test how confidence scores guide knowledge refinement.
    Shows the system's ability to improve understanding.
    """
    engine = ResearchEngine()
    crew = ConfidenceCrew(llm=LLMInterface())
    
    # Track confidence evolution
    confidence_history = []
    
    # Initial learning phase
    for _ in range(3):
        results = await engine.research_code(
            query="dependency injection patterns",
            min_confidence=0.5
        )
        
        # Record confidence
        confidence_history.append(
            engine.get_average_confidence()
        )
        
        # Analyze and refine
        await crew.analyze_results(results)
        await asyncio.sleep(1)
    
    # Verify confidence improvement
    assert confidence_history[-1] > confidence_history[0]
    
    # Test knowledge application
    high_confidence_results = await engine.research_code(
        query="dependency injection",
        min_confidence=0.8  # Higher threshold
    )
    
    # Verify quality
    assert engine.get_result_relevance(high_confidence_results) > 0.8
    assert engine.get_false_positive_rate(high_confidence_results) < 0.1

async def test_incremental_knowledge_building():
    """
    Test how knowledge is built up incrementally.
    Shows the system's learning progression.
    """
    engine = ResearchEngine()
    
    # Define learning sequence
    topics = [
        "basic error handling",
        "error handling with async",
        "error handling with validation",
        "complete error handling system"
    ]
    
    knowledge_state = []
    for topic in topics:
        # Research with current knowledge
        results = await engine.research_code(
            query=topic,
            use_accumulated_knowledge=True
        )
        
        # Store and analyze
        await engine.store_research_results(results)
        patterns = await engine.analyze_implementation_patterns(
            results
        )
        
        # Record knowledge state
        knowledge_state.append({
            "topic": topic,
            "patterns_found": len(patterns),
            "confidence": engine.get_average_confidence(),
            "relationships": len(engine.get_relationships())
        })
        
        # Allow knowledge integration
        await asyncio.sleep(1)
    
    # Verify knowledge progression
    assert knowledge_state[-1]["patterns_found"] > \
           knowledge_state[0]["patterns_found"]
    
    assert knowledge_state[-1]["confidence"] > \
           knowledge_state[0]["confidence"]
    
    assert knowledge_state[-1]["relationships"] > \
           knowledge_state[0]["relationships"]
    
    # Verify knowledge quality
    final_state = knowledge_state[-1]
    assert final_state["confidence"] > 0.8
    assert engine.get_knowledge_coherence() > 0.7