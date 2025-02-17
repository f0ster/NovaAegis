"""
Web interface for NovaAegis actor portal.
"""
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from datetime import datetime

from ..core.actor_orchestrator import ActorOrchestrator
from ..environment_forge import EnvironmentForge
from ..knowledge_store import KnowledgeStore
from ..database import AsyncDatabaseManager
from ..domain import (
    Project,
    CodePattern,
    ResearchResult,
    SearchHistory
)

app = FastAPI(title="NovaAegis Portal")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
async def get_db():
    db = AsyncDatabaseManager()
    async with db.get_async_db() as session:
        yield session

# Initialize core systems
orchestrator = ActorOrchestrator()
knowledge_store = None

# API Models
class CreateWorkerRequest(BaseModel):
    name: str
    focus_area: Optional[str] = None
    tools: Optional[List[str]] = None

class TaskRequest(BaseModel):
    input: str
    context: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str = "pending"

@app.on_event("startup")
async def startup():
    """Initialize core systems."""
    global knowledge_store
    db = AsyncDatabaseManager()
    knowledge_store = KnowledgeStore(db.get_async_db)
    await knowledge_store.initialize()
    await orchestrator.setup()

@app.get("/api/v1/status")
async def get_status():
    """Get portal status."""
    return {
        "status": "running",
        "active_workers": len(orchestrator.actors),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/workers")
async def create_worker(request: CreateWorkerRequest) -> Dict[str, str]:
    """Create new worker."""
    try:
        # Get profile from forge
        forge = EnvironmentForge()
        profile = forge.get_profile()

        # Initialize actor with profile
        worker_id = await orchestrator.initialize_actor(
            profile_name=profile.name,
            focus_area=request.focus_area
        )
        return {"worker_id": worker_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/workers")
async def list_workers() -> Dict[str, List[Dict[str, Any]]]:
    """List all workers."""
    workers = []
    for worker_id in orchestrator.actors:
        state = await orchestrator.get_actor_state(worker_id)
        workers.append({
            "id": worker_id,
            "status": state["status"],
            "focus_area": state["focus_area"],
            "operation_count": state["operation_count"]
        })
    return {"workers": workers}

@app.get("/api/v1/workers/{worker_id}")
async def get_worker(worker_id: str) -> Dict[str, Any]:
    """Get worker status."""
    try:
        return await orchestrator.get_actor_state(worker_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/workers/{worker_id}/tasks")
async def submit_task(
    worker_id: str,
    request: TaskRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """Submit task to worker."""
    try:
        task_id = f"task_{datetime.now().timestamp()}"
        
        # Start task processing in background
        background_tasks.add_task(
            process_task,
            worker_id,
            task_id,
            request.input,
            request.context
        )
        
        # Initialize task status
        _task_results[task_id] = {
            "status": "pending",
            "results": []
        }
        
        return TaskResponse(task_id=task_id)
        
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_task(
    worker_id: str,
    task_id: str,
    input: str,
    context: Optional[Dict[str, Any]] = None
):
    """Process task in background."""
    try:
        actions = []
        async for action in orchestrator.handle_perception(
            worker_id,
            input,
            context
        ):
            actions.append({
                "type": action.response_type,
                "content": action.content,
                "confidence": action.confidence,
                "timestamp": action.timestamp.isoformat()
            })
            
        # Update task status
        _task_results[task_id] = {
            "status": "completed",
            "results": actions
        }
            
    except Exception as e:
        # Store error
        _task_errors[task_id] = str(e)
        _task_results[task_id] = {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: str) -> Dict[str, Any]:
    """Get task status and results."""
    try:
        # Get task results from storage
        if task_id not in _task_results:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return _task_results[task_id]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/workers/{worker_id}/knowledge")
async def get_worker_knowledge(worker_id: str) -> Dict[str, Any]:
    """Get worker's knowledge state."""
    try:
        state = await orchestrator.get_actor_state(worker_id)
        return {
            "patterns": state["knowledge"].get("patterns", []),
            "concepts": state["knowledge"].get("concepts", []),
            "relationships": state["knowledge"].get("relationships", []),
            "focus_areas": state["focus_areas"]
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/workers/{worker_id}/stop")
async def stop_worker(worker_id: str):
    """Stop worker."""
    try:
        await orchestrator.terminate_actor(worker_id)
        return {"status": "stopped"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/workers/{worker_id}/start")
async def start_worker(worker_id: str):
    """Start worker."""
    try:
        state = await orchestrator.get_actor_state(worker_id)
        if state["status"] != "stopped":
            raise HTTPException(status_code=400, detail="Worker already running")
            
        await orchestrator.initialize_actor(
            focus_area=state["focus_area"]
        )
        return {"status": "started"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown():
    """Clean up resources."""
    await orchestrator.cleanup()

# Task storage
_task_results: Dict[str, Dict[str, Any]] = {}
_task_errors: Dict[str, str] = {}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)