"""
Behavioral test demonstrating the complete research workflow.
Shows domain-driven functionality of research, indexing, and knowledge building.
"""
import pytest
import asyncio
from datetime import datetime

from nova_aegis.nova_aegis import NovaAegis
from nova_aegis.browser_pilot import BrowserPilot
from nova_aegis.knowledge_store import KnowledgeStore

@pytest.mark.asyncio
async def test_huggingface_research_workflow():
    """
    Demonstrates complete research workflow:
    1. Initial research command
    2. Browser exploration and indexing
    3. Knowledge graph building
    4. Status checking and updates
    """
    # Initialize core components
    nova_aegis = NovaAegis()
    knowledge_store = KnowledgeStore()
    browser_pilot = BrowserPilot(knowledge_store)
    
    await nova_aegis.start_session()
    
    try:
        # Start research exploration
        response = await nova_aegis.process_request(
            "Research recent HuggingFace papers about LLM architectures"
        )
        
        # Verify research started
        assert "exploring" in response["message"].lower()
        assert browser_pilot.is_exploring
        assert browser_pilot.current_url.startswith("https://huggingface.co")
        
        # Wait for initial paper processing
        while len(browser_pilot.processed_papers) < 3:
            await asyncio.sleep(0.1)
            
        # Verify papers are being processed
        papers = browser_pilot.processed_papers
        assert len(papers) >= 3
        assert all(paper.url.startswith("https://huggingface.co") for paper in papers)
        assert all(paper.content is not None for paper in papers)
        
        # Check knowledge graph building
        graph = knowledge_store.get_knowledge_graph()
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0
        assert any("LLM" in node.labels for node in graph.nodes)
        
        # Verify paper indexing
        indexed_papers = knowledge_store.get_indexed_papers()
        assert len(indexed_papers) >= 3
        assert all(paper.indexed_at is not None for paper in indexed_papers)
        assert all(paper.vector_embedding is not None for paper in indexed_papers)
        
        # Check job status
        status = browser_pilot.get_job_status()
        assert status.papers_processed >= 3
        assert status.is_indexing
        assert len(status.recent_updates) > 0
        
        # Request research update
        update_response = await nova_aegis.process_request(
            "What have you found so far?"
        )
        
        # Verify browser loads from index
        assert browser_pilot.loading_from_index
        assert len(browser_pilot.loaded_papers) >= 3
        
        # Verify knowledge synthesis
        assert len(update_response["insights"]) >= 3
        assert all(
            insight["confidence"] > 0.6 
            for insight in update_response["insights"]
        )
        
        # Verify visual elements
        assert "knowledge_graph" in update_response["visual"]
        graph_viz = update_response["visual"]["knowledge_graph"]
        assert len(graph_viz["nodes"]) >= len(graph.nodes)
        assert len(graph_viz["edges"]) >= len(graph.edges)
        
        # Verify understanding state
        understanding = knowledge_store.get_current_understanding()
        assert understanding.confidence > 0.7
        assert len(understanding.key_concepts) >= 3
        assert len(understanding.patterns) > 0
        assert all(
            pattern.support_count >= 2 
            for pattern in understanding.patterns
        )
        
        # Request specific insight
        insight_response = await nova_aegis.process_request(
            "Tell me about training approaches"
        )
        
        # Verify focused analysis
        assert browser_pilot.current_focus == "training"
        assert len(insight_response["insights"]) > 0
        assert any(
            "training" in insight["text"].lower()
            for insight in insight_response["insights"]
        )
        
        # Verify knowledge graph updates
        updated_graph = knowledge_store.get_knowledge_graph()
        assert len(updated_graph.nodes) >= len(graph.nodes)
        assert len(updated_graph.edges) >= len(graph.edges)
        assert any(
            "training" in node.labels 
            for node in updated_graph.nodes
        )
        
        # Verify research completion
        final_status = browser_pilot.get_job_status()
        assert final_status.completed
        assert final_status.papers_processed >= 5
        assert final_status.indexed_count == final_status.papers_processed
        assert len(final_status.research_summary) > 0
        
    finally:
        await nova_aegis.end_session()
        await browser_pilot.cleanup()

@pytest.mark.asyncio
async def test_research_visual_tracking():
    """
    Demonstrates visual tracking of research progress:
    1. Screenshot capture
    2. Visual state tracking
    3. Progress visualization
    """
    nova_aegis = NovaAegis()
    browser_pilot = BrowserPilot()
    
    await nova_aegis.start_session()
    
    try:
        # Start research with visual tracking
        response = await nova_aegis.process_request(
            "Research recent HuggingFace papers about LLM architectures",
            {"track_visual": True}
        )
        
        # Verify visual capture started
        assert browser_pilot.is_capturing
        assert len(browser_pilot.visual_history) > 0
        
        # Wait for visual updates
        while len(browser_pilot.visual_history) < 3:
            await asyncio.sleep(0.1)
        
        # Verify visual states
        visual_states = browser_pilot.visual_history
        assert len(visual_states) >= 3
        assert all(state.screenshot is not None for state in visual_states)
        assert all(state.timestamp is not None for state in visual_states)
        
        # Verify progress visualization
        progress = browser_pilot.get_progress_visualization()
        assert progress.total_papers > 0
        assert progress.processed_count > 0
        assert progress.visual_timeline is not None
        
        # Check visual context
        context = browser_pilot.get_visual_context()
        assert len(context.screenshots) >= 3
        assert context.has_progress_markers
        assert context.timeline_complete
        
    finally:
        await nova_aegis.end_session()
        await browser_pilot.cleanup()