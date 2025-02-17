"""
E2E test of task execution with knowledge building.
Tests how actors learn while doing tasks.
"""
import pytest
import asyncio
from datetime import datetime

from nova_aegis.core.actor_orchestrator import ActorOrchestrator
from nova_aegis.knowledge_store import KnowledgeStore
from nova_aegis.database import AsyncDatabaseManager

@pytest.mark.asyncio
async def test_task_knowledge_cycle():
    """Test how task execution builds knowledge."""
    orchestrator = ActorOrchestrator()
    await orchestrator.setup()
    
    try:
        # Initialize actor
        actor_id = await orchestrator.initialize_actor(
            focus_area="llm_architectures"
        )
        
        # Initial knowledge state
        initial_state = await orchestrator.knowledge.get_current_state()
        
        # Submit research task
        actions = []
        async for action in orchestrator.handle_perception(
            actor_id,
            "Research recent LLM architectures",
            {
                "timestamp": datetime.now().isoformat(),
                "source": "web",
                "topic": "llm_architectures"
            }
        ):
            actions.append(action)
            
            # Verify knowledge building from action
            if action.response_type == "browser":
                # Knowledge should grow after browser action
                current_state = await orchestrator.knowledge.get_current_state()
                assert len(current_state["patterns"]) >= len(initial_state["patterns"])
                
                # Should have browser-sourced patterns
                assert any(
                    pattern["source"] == "web"
                    for pattern in current_state["patterns"]
                )
        
        # Verify final knowledge state
        final_state = await orchestrator.knowledge.get_current_state()
        
        # Should have learned patterns
        patterns = final_state["patterns"]
        assert len(patterns) > len(initial_state["patterns"])
        assert any(
            "architecture" in p["description"].lower()
            for p in patterns
        )
        
        # Should have made connections
        connections = final_state["connections"]
        assert len(connections) > 0
        assert any(
            "llm" in c["from"].lower() or "llm" in c["to"].lower()
            for c in connections
        )
        
        # Should have focus areas
        assert "llm_architectures" in final_state["focus_areas"]
        
        # Submit follow-up task using learned knowledge
        actions = []
        async for action in orchestrator.handle_perception(
            actor_id,
            "What are the key differences between these architectures?",
            {
                "timestamp": datetime.now().isoformat(),
                "previous_task": "research",
                "topic": "llm_architectures"
            }
        ):
            actions.append(action)
            
            # Verify using previous knowledge
            if action.response_type == "thought":
                assert any(
                    "previous findings" in str(action.reasoning).lower()
                    for action in actions
                )
        
        # Verify knowledge refinement
        refined_state = await orchestrator.knowledge.get_current_state()
        assert len(refined_state["relationships"]) > len(final_state["relationships"])
        
    finally:
        await orchestrator.cleanup()