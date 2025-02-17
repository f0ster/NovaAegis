"""
Integration tests for browser operations in task system.
"""
import pytest
from unittest.mock import Mock, patch
import asyncio
from datetime import datetime

from nova_aegis.core.actor_orchestrator import ActorOrchestrator
from nova_aegis.environment_forge import EnvironmentForge
from nova_aegis.web.app import NovaAegisPortal

@pytest.fixture
def mock_browser():
    """Mock browser pilot."""
    with patch("nova_aegis.browser_pilot.BrowserPilot") as mock:
        mock.return_value.__enter__.return_value = mock.return_value
        mock.return_value.execute.return_value = {
            "success": True,
            "result": "test result"
        }
        yield mock

@pytest.mark.asyncio
async def test_browser_task_flow(mock_browser):
    """Test complete task flow with browser operations."""
    # Initialize portal
    portal = NovaAegisPortal()
    await portal.initialize()
    
    try:
        # Submit task that needs browser
        result = await portal.process_task(
            "Check the documentation at https://test.com"
        )
        
        # Verify browser used
        assert any(
            action["type"] == "browser"
            for action in result["actions"]
        )
        
        # Verify knowledge gained
        assert result["knowledge_gained"] > 0
        
        # Verify browser operations
        mock_browser.return_value.execute.assert_called()
        assert "navigate" in str(mock_browser.return_value.execute.call_args)
        
    finally:
        await portal.cleanup()

@pytest.mark.asyncio
async def test_browser_knowledge_integration(mock_browser):
    """Test browser results feed into knowledge system."""
    # Initialize components
    orchestrator = ActorOrchestrator()
    forge = EnvironmentForge()
    
    # Initialize actor
    actor_id = await orchestrator.initialize_actor()
    
    try:
        # Process perception that uses browser
        actions = []
        async for action in orchestrator.handle_perception(
            actor_id,
            "Research test.com",
            {"timestamp": datetime.now().isoformat()}
        ):
            actions.append(action)
            
        # Verify browser action occurred
        assert any(
            action.response_type == "browser"
            for action in actions
        )
        
        # Verify knowledge state updated
        state = await orchestrator.get_knowledge_state()
        assert len(state["patterns"]) > 0
        assert len(state["connections"]) > 0
        
        # Verify browser results integrated
        assert any(
            "test.com" in str(pattern)
            for pattern in state["patterns"]
        )
        
    finally:
        await orchestrator.cleanup()

@pytest.mark.asyncio
async def test_browser_error_handling(mock_browser):
    """Test browser error handling in task system."""
    # Setup error condition
    mock_browser.return_value.execute.side_effect = Exception("Browser error")
    
    # Initialize portal
    portal = NovaAegisPortal()
    await portal.initialize()
    
    try:
        # Submit task
        result = await portal.process_task(
            "Check https://test.com"
        )
        
        # Verify error captured
        assert any(
            action["type"] == "error"
            for action in result["actions"]
        )
        
        # Verify task marked failed
        assert any(
            "Browser error" in str(action["content"])
            for action in result["actions"]
        )
        
    finally:
        await portal.cleanup()

@pytest.mark.asyncio
async def test_browser_permissions(mock_browser):
    """Test browser tool permissions."""
    # Create restricted profile
    forge = EnvironmentForge()
    profile = forge.create_profile(
        name="restricted",
        description="Limited browser access",
        services={
            "browser": {
                "tools": [{
                    "name": "browser",
                    "permissions": ["navigate"]  # Only allow navigation
                }]
            }
        }
    )
    
    # Initialize portal with restricted profile
    portal = NovaAegisPortal()
    portal.forge.set_active_profile("restricted")
    await portal.initialize()
    
    try:
        # Try restricted operation
        result = await portal.process_task(
            "Navigate to https://test.com"
        )
        assert any(
            action["type"] == "browser" and action["success"]
            for action in result["actions"]
        )
        
        # Try forbidden operation
        result = await portal.process_task(
            "Click button on https://test.com"
        )
        assert any(
            action["type"] == "error" and "permission" in str(action["content"]).lower()
            for action in result["actions"]
        )
        
    finally:
        await portal.cleanup()
        forge.delete_profile("restricted")