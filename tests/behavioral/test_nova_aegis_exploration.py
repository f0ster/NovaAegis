"""
Behavioral test demonstrating NovaAegis's exploration capabilities.
Shows how browser interaction is part of the perception system.
"""
import pytest
import asyncio
import structlog
from datetime import datetime

from nova_aegis.nova_aegis import NovaAegis
from nova_aegis.core.companion import Perception
from nova_aegis.browser_pilot import BrowserPilot

logger = structlog.get_logger()

@pytest.mark.asyncio
async def test_nova_aegis_research_exploration():
    """
    Test how NovaAegis explores and learns through browser interaction.
    Shows the complete flow from request to understanding.
    """
    # Initialize NovaAegis
    nova_aegis = NovaAegis()
    await nova_aegis.start_session()
    
    try:
        # Initial research request
        response = await nova_aegis.process_request(
            "Let's explore recent developments in LLM architectures"
        )
        
        # Verify initial understanding
        assert response["message"].startswith("I'd be happy to explore")
        assert len(response["insights"]) == 0  # No insights yet
        
        # Verify companion started perception
        companion = nova_aegis.companion
        assert len(companion.understanding.knowledge_state) == 0
        
        # First exploration cycle
        perception = await companion.perception_stream.get()
        assert perception.stimulus == "LLM architectures"
        
        # Verify browser pilot integration
        pilot = companion.browser_pilot
        assert pilot.current_task == "explore_topic"
        assert "LLM" in pilot.current_context["keywords"]
        
        # Let pilot gather information
        await asyncio.sleep(1)  # Allow time for gathering
        
        # Verify knowledge accumulation
        assert len(companion.understanding.knowledge_state) > 0
        assert companion.understanding.certainty_levels["LLM"] > 0.5
        
        # Second research request with context
        response = await nova_aegis.process_request(
            "What patterns do you notice in training approaches?"
        )
        
        # Verify knowledge integration
        assert "training" in companion.understanding.knowledge_state
        assert len(response["insights"]) > 0
        
        # Verify visual context
        assert "visual" in response
        assert response["visual"]["type"] == "knowledge_graph"
        
        # Verify pilot adaptation
        assert pilot.current_task == "analyze_patterns"
        assert "training" in pilot.current_context["focus_areas"]
        
        # Final synthesis request
        response = await nova_aegis.process_request(
            "Can you summarize the key innovations?"
        )
        
        # Verify comprehensive understanding
        assert len(response["insights"]) >= 3
        assert all(
            insight["certainty"] > 0.7 
            for insight in response["insights"]
        )
        
        # Verify visual journey
        assert len(nova_aegis.visual_memory) >= 3
        assert all(
            "timestamp" in memory 
            for memory in nova_aegis.visual_memory
        )
        
    finally:
        await nova_aegis.end_session()

@pytest.mark.asyncio
async def test_nova_aegis_perception_cycle():
    """
    Test NovaAegis's perception cycle in detail.
    Shows how browser pilot feeds into understanding.
    """
    nova_aegis = NovaAegis()
    await nova_aegis.start_session()
    
    try:
        # Start exploration
        companion = nova_aegis.companion
        pilot = companion.browser_pilot
        
        # Track perception cycle
        perceptions = []
        async def collect_perceptions():
            while True:
                perception = await companion.perception_stream.get()
                perceptions.append(perception)
                if len(perceptions) >= 3:
                    break
        
        # Start perception collection
        collector = asyncio.create_task(collect_perceptions())
        
        # Trigger exploration
        await nova_aegis.process_request(
            "Let's explore transformer architectures"
        )
        
        # Wait for perceptions
        await collector
        
        # Verify perception cycle
        assert len(perceptions) == 3
        
        # First perception should be initial request
        assert perceptions[0].stimulus == "transformer architectures"
        assert perceptions[0].context["type"] == "user_request"
        
        # Second perception should be pilot findings
        assert "findings" in perceptions[1].context
        assert perceptions[1].context["source"] == "browser_pilot"
        
        # Third perception should be synthesized understanding
        assert perceptions[2].context["type"] == "synthesis"
        assert "visual_data" in perceptions[2].context
        
        # Verify pilot integration
        assert pilot.exploration_history[-1]["success"]
        assert pilot.current_context["depth"] >= 2
        
        # Verify knowledge building
        knowledge = companion.understanding.knowledge_state
        assert "transformer" in knowledge
        assert "attention" in knowledge
        assert knowledge["transformer"]["confidence"] > 0.6
        
    finally:
        await nova_aegis.end_session()

@pytest.mark.asyncio
async def test_nova_aegis_visual_exploration():
    """
    Test NovaAegis's visual exploration capabilities.
    Shows how visual context enhances understanding.
    """
    nova_aegis = NovaAegis()
    await nova_aegis.start_session()
    
    try:
        # Start with architecture diagram
        response = await nova_aegis.process_request(
            "Can you analyze this architecture diagram?",
            context={
                "visual": True,
                "image_path": "tests/data/llm_architecture.png"
            }
        )
        
        # Verify visual perception
        companion = nova_aegis.companion
        pilot = companion.browser_pilot
        
        assert pilot.current_task == "analyze_visual"
        assert "image_analysis" in pilot.current_context
        
        # Verify visual understanding
        knowledge = companion.understanding.knowledge_state
        assert "visual_components" in knowledge
        assert knowledge["visual_components"]["confidence"] > 0.7
        
        # Verify insights include visual elements
        assert any(
            "diagram" in insight["source"]
            for insight in response["insights"]
        )
        
        # Verify visual memory
        assert len(nova_aegis.visual_memory) > 0
        assert "architecture_analysis" in nova_aegis.visual_memory[-1]["type"]
        
    finally:
        await nova_aegis.end_session()