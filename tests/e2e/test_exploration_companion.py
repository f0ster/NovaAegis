"""
End-to-end test of NovaAegis as an ExplorationCompanion.
Tests the complete cycle of perception, processing, learning and action.
"""
import pytest
import asyncio
from datetime import datetime

from nova_aegis.nova_aegis import NovaAegis
from nova_aegis.core.companion import ExplorationCompanion, Perception
from nova_aegis.browser_pilot import BrowserPilot
from nova_aegis.knowledge_store import KnowledgeStore

@pytest.mark.asyncio
async def test_exploration_companion_research_cycle():
    """
    Tests NovaAegis's complete exploration cycle:
    - Perceiving research request
    - Processing through browser pilot
    - Learning via knowledge graph
    - Acting on understanding
    """
    # Initialize NovaAegis as ExplorationCompanion
    nova_aegis = NovaAegis()
    companion = nova_aegis.companion
    knowledge_store = companion.knowledge
    browser_pilot = companion.browser_pilot
    
    await nova_aegis.start_session()
    
    try:
        # Initial perception
        response = await nova_aegis.process_request(
            "Research recent HuggingFace papers about LLM architectures"
        )
        
        # Verify companion started perception cycle
        perception = await companion.perception_stream.get()
        assert perception.stimulus == "LLM architectures"
        assert perception.context["type"] == "research_request"
        
        # Verify browser pilot processing
        assert browser_pilot.is_processing
        assert browser_pilot.current_task.type == "research"
        assert "huggingface.co" in browser_pilot.current_task.url
        
        # Wait for knowledge accumulation
        while len(knowledge_store.get_papers()) < 3:
            await asyncio.sleep(0.1)
        
        # Verify knowledge building
        papers = knowledge_store.get_papers()
        assert len(papers) >= 3
        assert all(paper.processed for paper in papers)
        assert all(paper.vector_embedding is not None for paper in papers)
        
        # Verify graph construction
        graph = knowledge_store.get_knowledge_graph()
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0
        assert any("LLM" in node.labels for node in graph.nodes)
        
        # Request companion's understanding
        understanding = companion.get_understanding()
        assert understanding.confidence > 0.6
        assert len(understanding.key_concepts) >= 3
        assert len(understanding.patterns) > 0
        
        # Verify visual memory
        visual_states = browser_pilot.get_visual_states()
        assert len(visual_states) >= 3
        assert all(state.screenshot is not None for state in visual_states)
        
        # Request focused exploration
        response = await nova_aegis.process_request(
            "What have you learned about training approaches?"
        )
        
        # Verify companion adapts focus
        perception = await companion.perception_stream.get()
        assert perception.context["focus"] == "training"
        
        # Verify browser pilot adaptation
        assert browser_pilot.current_task.type == "focused_research"
        assert browser_pilot.current_task.context["focus"] == "training"
        
        # Verify knowledge refinement
        refined_papers = knowledge_store.get_papers(focus="training")
        assert len(refined_papers) > 0
        assert all("training" in paper.tags for paper in refined_papers)
        
        # Verify understanding evolution
        new_understanding = companion.get_understanding()
        assert new_understanding.confidence > understanding.confidence
        assert len(new_understanding.patterns) > len(understanding.patterns)
        
        # Verify companion generates insights
        assert len(response["insights"]) >= 3
        assert any(
            "training" in insight["text"].lower()
            for insight in response["insights"]
        )
        
        # Verify visual journey
        journey = browser_pilot.get_visual_journey()
        assert len(journey) >= 5
        assert journey[-1].context["type"] == "focused_analysis"
        
    finally:
        await nova_aegis.end_session()

@pytest.mark.asyncio
async def test_exploration_companion_learning():
    """
    Tests NovaAegis's learning capabilities:
    - Knowledge accumulation
    - Pattern recognition
    - Understanding refinement
    """
    nova_aegis = NovaAegis()
    companion = nova_aegis.companion
    knowledge_store = companion.knowledge
    
    await nova_aegis.start_session()
    
    try:
        # Track learning progress
        initial_state = companion.get_understanding()
        
        # First research phase
        await nova_aegis.process_request(
            "Research transformer architecture papers"
        )
        
        # Wait for learning
        while len(knowledge_store.get_patterns()) < 3:
            await asyncio.sleep(0.1)
            
        # Verify initial learning
        mid_state = companion.get_understanding()
        assert mid_state.confidence > initial_state.confidence
        assert len(mid_state.patterns) > len(initial_state.patterns)
        
        # Second research phase
        await nova_aegis.process_request(
            "Now look into attention mechanisms"
        )
        
        # Wait for additional learning
        while len(knowledge_store.get_patterns()) < 5:
            await asyncio.sleep(0.1)
            
        # Verify knowledge integration
        final_state = companion.get_understanding()
        assert final_state.confidence > mid_state.confidence
        assert len(final_state.patterns) > len(mid_state.patterns)
        
        # Verify cross-concept learning
        concepts = knowledge_store.get_concepts()
        assert "transformer" in concepts
        assert "attention" in concepts
        assert any(
            c.connects("transformer", "attention")
            for c in knowledge_store.get_connections()
        )
        
    finally:
        await nova_aegis.end_session()

@pytest.mark.asyncio
async def test_exploration_companion_adaptation():
    """
    Tests NovaAegis's ability to adapt exploration:
    - Focus shifting
    - Strategy adjustment
    - Visual context maintenance
    """
    nova_aegis = NovaAegis()
    companion = nova_aegis.companion
    browser_pilot = companion.browser_pilot
    
    await nova_aegis.start_session()
    
    try:
        # Start broad exploration
        await nova_aegis.process_request(
            "Research LLM architectures"
        )
        
        initial_strategy = browser_pilot.current_strategy
        
        # Request specific focus
        await nova_aegis.process_request(
            "Focus on efficiency improvements"
        )
        
        # Verify strategy adaptation
        assert browser_pilot.current_strategy != initial_strategy
        assert browser_pilot.current_focus == "efficiency"
        
        # Verify visual context maintained
        visual_context = browser_pilot.get_visual_context()
        assert len(visual_context.history) > 0
        assert visual_context.maintains_continuity
        
        # Request synthesis
        response = await nova_aegis.process_request(
            "What are the key findings?"
        )
        
        # Verify contextual understanding
        assert len(response["insights"]) > 0
        assert any(
            "efficiency" in insight["text"].lower()
            for insight in response["insights"]
        )
        
    finally:
        await nova_aegis.end_session()