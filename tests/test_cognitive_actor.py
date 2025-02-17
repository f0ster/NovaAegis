"""
Test cognitive actor with research chain integration.
"""
import pytest
from unittest.mock import Mock, patch
import asyncio
from datetime import datetime

from nova_aegis.core.cognitive_actor import CognitiveActor, Action
from nova_aegis.core.tools.browser_tool import BrowserTool

@pytest.fixture
def mock_browser_tool():
    """Mock browser tool with research capabilities."""
    tool = Mock(spec=BrowserTool)
    tool.name = "browser"
    
    # Mock paper metadata result
    tool._run.return_value = {
        "type": "paper",
        "data": {
            "title": "Test LLM Paper",
            "authors": ["Author 1", "Author 2"],
            "abstract": "Test abstract about LLMs",
            "published_date": "2024-02-12",
            "url": "https://test.com/paper",
            "citations": 42
        }
    }
    return tool

@pytest.fixture
async def actor():
    """Test actor with mocked components."""
    actor = CognitiveActor()
    
    # Mock core components
    actor.knowledge = Mock()
    actor.knowledge.query_relevant.return_value = {
        "focus": "llm_architectures",
        "concepts": ["transformer", "attention"]
    }
    actor.knowledge.get_current_state.return_value = {
        "papers": [],
        "concepts": ["llm", "architecture"]
    }
    
    actor.communication = Mock()
    actor.communication.llm = Mock()
    
    return actor

@pytest.mark.asyncio
async def test_research_initialization(actor, mock_browser_tool):
    """Test research chain initialization."""
    # Initialize with research focus
    await actor.initialize_services({
        "browser": {
            "settings": {"headless": True}
        }
    })
    
    # Verify tool setup
    assert len(actor.tools) == 1
    assert actor.tools[0].name == "browser"
    assert actor.agent is not None
    assert actor.executor is not None

@pytest.mark.asyncio
async def test_paper_research_flow(actor, mock_browser_tool):
    """Test paper research processing."""
    # Setup actor with mock tool
    actor.tools = [mock_browser_tool]
    actor.agent = Mock()
    actor.executor = Mock()
    actor.executor.arun.return_value = (
        "Thought: I should check HuggingFace papers\n"
        "Action: browser({'type': 'verify_papers_list'})\n"
        "Observation: Found papers list\n"
        "Thought: Let me check the first paper\n"
        "Action: browser({'type': 'extract_paper_metadata'})\n"
        "Observation: Paper is about LLM architecture"
    )
    
    # Submit research task
    await actor.perceive(
        "Research LLM architecture papers",
        {"focus": "llm_architectures"}
    )
    
    # Process one cycle
    await actor.process()
    
    # Verify executor called with research context
    actor.executor.arun.assert_called_once()
    call_args = actor.executor.arun.call_args[0][0]
    assert "LLM" in call_args
    assert "architecture" in call_args
    
    # Verify research insights generated
    processed = await actor.processing_stream.get()
    assert len(processed["insights"]) > 0
    assert any(
        "paper" in i["content"].lower()
        for i in processed["insights"]
    )

@pytest.mark.asyncio
async def test_knowledge_integration(actor, mock_browser_tool):
    """Test paper knowledge integration."""
    # Setup actor
    actor.tools = [mock_browser_tool]
    actor.agent = Mock()
    actor.executor = Mock()
    actor.executor.arun.return_value = (
        "Thought: Found paper about LLM architecture\n"
        "Action: browser({'type': 'extract_paper_metadata'})\n"
        "Observation: Paper metadata extracted"
    )
    
    # Submit research task
    await actor.perceive(
        "Research LLM papers",
        {"focus": "llm_architectures"}
    )
    
    # Process one cycle
    await actor.process()
    
    # Verify knowledge integration
    actor.knowledge.integrate_insights.assert_called_once()
    insights = actor.knowledge.integrate_insights.call_args[0][0]
    
    # Should have thought and paper insight
    assert len(insights) == 3
    assert insights[0]["type"] == "thought"
    assert "LLM" in insights[0]["content"]
    assert insights[1]["type"] == "action"
    assert "extract_paper_metadata" in insights[1]["content"]

@pytest.mark.asyncio
async def test_research_confidence(actor, mock_browser_tool):
    """Test research confidence calculation."""
    # Setup actor
    actor.tools = [mock_browser_tool]
    actor.agent = Mock()
    actor.executor = Mock()
    
    # Simulate high confidence case
    actor.executor.arun.return_value = (
        "Thought: Found relevant LLM paper\n"
        "Action: browser({'type': 'extract_paper_metadata'})\n"
        "Observation: Paper matches focus area\n"
        "Thought: Paper has good citations\n"
        "Thought: Content aligns with research"
    )
    
    # Process research
    await actor.perceive("Research LLM papers")
    await actor.process()
    await actor.act()
    
    # Get action
    action = await actor.action_stream.get()
    
    # Should have high confidence from multiple supporting thoughts
    assert action.confidence > 0.8
    assert len(action.reasoning) >= 3

@pytest.mark.asyncio
async def test_research_error_handling(actor, mock_browser_tool):
    """Test research error handling."""
    # Setup actor with failing tool
    mock_browser_tool._run.side_effect = Exception("Research error")
    actor.tools = [mock_browser_tool]
    actor.agent = Mock()
    actor.executor = Mock()
    actor.executor.arun.return_value = (
        "Action: browser({'type': 'verify_papers_list'})"
    )
    
    # Submit research task
    await actor.perceive("Research LLM papers")
    
    # Process one cycle
    await actor.process()
    
    # Verify error action generated
    action = await actor.action_stream.get()
    assert action.response_type == "error"
    assert "Research error" in action.content
    assert action.confidence == 0.0