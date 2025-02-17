"""
PerceptionGateway: Standardizes how external inputs become actor perceptions.
Ensures consistent perception handling regardless of source (CLI, web, etc).
"""
from typing import Dict, Any, Optional, AsyncIterator, Literal
import asyncio
from datetime import datetime
import json
from pathlib import Path

from .research_scientist import ResearchScientist
from .cognitive_actor import Action

TaskStatus = Literal["running", "completed", "failed", "paused"]

class PerceptionGateway:
    """Gateway that standardizes input -> perception flow."""
    
    def __init__(self):
        self.scientist = ResearchScientist()
        self._initialized = False
        
        # Task history
        self.task_dir = Path.home() / ".nova_aegis" / "tasks"
        self.task_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize scientist if needed."""
        if not self._initialized:
            await self.scientist.awaken()
            self._initialized = True
            
    def _update_task(self, task_file: Path, status: TaskStatus, actions: list, error: Optional[str] = None):
        """Update task state."""
        task = json.loads(task_file.read_text())
        task.update({
            "status": status,
            "actions": actions,
            "error": error,
            "updated_at": datetime.now().isoformat()
        })
        task_file.write_text(json.dumps(task, indent=2))
            
    async def submit_input(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Action]:
        """Submit any input as a perception."""
        await self.initialize()
        
        # Create task record
        task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_file = self.task_dir / f"{task_id}.json"
        task_file.write_text(json.dumps({
            "input": input_data,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "actions": []
        }, indent=2))
        
        try:
            # Create standardized perception
            await self.scientist.perceive(input_data, context or {
                "timestamp": datetime.now().isoformat(),
                "type": "input",
                "task_id": task_id
            })
            
            # Stream actions
            actions = []
            while True:
                try:
                    action = await self.scientist.action_stream.get()
                    
                    # Save action
                    actions.append({
                        "type": action.response_type,
                        "content": action.content,
                        "confidence": action.confidence,
                        "timestamp": datetime.now().isoformat()
                    })
                    self._update_task(task_file, "running", actions)
                    
                    yield action
                    
                except asyncio.QueueEmpty:
                    break
                    
            # Mark task complete
            self._update_task(task_file, "completed", actions)
            
        except Exception as e:
            # Mark task failed
            self._update_task(task_file, "failed", actions, str(e))
            raise
                
    async def submit_feedback(self, feedback_data: Dict[str, Any]) -> AsyncIterator[Action]:
        """Submit feedback as a perception."""
        await self.initialize()
        
        # Create standardized feedback perception
        await self.scientist.perceive(feedback_data, {
            "timestamp": datetime.now().isoformat(),
            "type": "feedback"
        })
        
        # Stream actions
        while True:
            try:
                action = await self.scientist.action_stream.get()
                yield action
            except asyncio.QueueEmpty:
                break
    
    async def pause_task(self, task_id: str):
        """Pause a running task."""
        task_file = self.task_dir / f"{task_id}.json"
        if task_file.exists():
            task = json.loads(task_file.read_text())
            if task["status"] == "running":
                self._update_task(task_file, "paused", task["actions"])
                
    async def resume_task(self, task_id: str):
        """Resume a paused task."""
        task_file = self.task_dir / f"{task_id}.json"
        if task_file.exists():
            task = json.loads(task_file.read_text())
            if task["status"] == "paused":
                self._update_task(task_file, "running", task["actions"])
                
    async def get_understanding(self) -> Dict[str, Any]:
        """Get current understanding state."""
        await self.initialize()
        return {
            "knowledge": self.scientist.understanding.knowledge_state,
            "certainty": self.scientist.understanding.certainty_levels,
            "curiosities": self.scientist.understanding.curiosities
        }
    
    async def get_task_history(self) -> List[Dict[str, Any]]:
        """Get history of all tasks."""
        tasks = []
        for task_file in sorted(self.task_dir.glob("*.json"), reverse=True):
            tasks.append(json.loads(task_file.read_text()))
        return tasks
        
    async def cleanup(self):
        """Cleanup resources."""
        if self._initialized:
            await self.scientist.rest()
            self._initialized = False