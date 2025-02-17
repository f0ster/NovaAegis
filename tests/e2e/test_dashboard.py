"""
End-to-end test of NovaAegis actor portal.
Tests task execution with automatic knowledge building.
"""
import os
import pytest
import subprocess
import time
from pathlib import Path
import requests
import json

def start_dashboard():
    """Start NovaAegis portal."""
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Start portal
    log_file = logs_dir / "dashboard.log"
    with open(log_file, "w") as f:
        process = subprocess.Popen(
            ["python", "-m", "nova_aegis.web.app"],
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=str(Path(__file__).parent.parent.parent),
            env={
                **os.environ,
                "PYTHONPATH": str(Path(__file__).parent.parent.parent)
            }
        )
    
    # Wait for portal to start
    start_time = time.time()
    while time.time() - start_time < 30:  # 30 second timeout
        try:
            response = requests.get("http://localhost:7860/api/v1/status")
            if response.status_code == 200:
                print("Portal started successfully")
                return process
        except:
            if not process.poll() is None:
                with open(log_file) as f:
                    print("Portal crashed:", f.read())
                raise RuntimeError("Portal process died")
            time.sleep(0.1)
    
    # Check final log content
    if log_file.exists():
        with open(log_file) as f:
            print("Final portal output:", f.read())
    
    raise TimeoutError("Portal failed to start")

def stop_dashboard(process):
    """Stop portal and cleanup."""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

@pytest.fixture
def dashboard():
    """Start portal before test and cleanup after."""
    process = start_dashboard()
    yield
    stop_dashboard(process)

def test_task_execution_cycle(dashboard):
    """Test complete task execution cycle with knowledge building."""
    # Create actor
    response = requests.post(
        "http://localhost:7860/api/v1/workers",
        json={
            "name": "test_worker",
            "focus_area": "llm_architectures"
        }
    )
    assert response.status_code == 200
    worker_id = response.json()["worker_id"]
    
    # Initial knowledge state
    response = requests.get(
        f"http://localhost:7860/api/v1/workers/{worker_id}/knowledge"
    )
    initial_knowledge = response.json()
    
    # Submit first task
    response = requests.post(
        f"http://localhost:7860/api/v1/workers/{worker_id}/tasks",
        json={
            "input": "What are the latest LLM architectures?",
            "context": {"source": "web"}
        }
    )
    assert response.status_code == 200
    task_1 = response.json()["task_id"]
    
    # Wait for completion
    while True:
        response = requests.get(
            f"http://localhost:7860/api/v1/tasks/{task_1}"
        )
        task = response.json()
        if task["status"] == "completed":
            break
        elif task["status"] == "failed":
            raise Exception(f"Task failed: {task['error']}")
        time.sleep(1)
    
    # Verify knowledge grew
    response = requests.get(
        f"http://localhost:7860/api/v1/workers/{worker_id}/knowledge"
    )
    mid_knowledge = response.json()
    assert len(mid_knowledge["concepts"]) > len(initial_knowledge["concepts"])
    
    # Submit follow-up task using new knowledge
    response = requests.post(
        f"http://localhost:7860/api/v1/workers/{worker_id}/tasks",
        json={
            "input": "What are the key differences between these architectures?",
            "context": {"previous_task": task_1}
        }
    )
    assert response.status_code == 200
    task_2 = response.json()["task_id"]
    
    # Wait for completion
    while True:
        response = requests.get(
            f"http://localhost:7860/api/v1/tasks/{task_2}"
        )
        task = response.json()
        if task["status"] == "completed":
            # Verify used previous knowledge
            assert any(
                "previous findings" in str(a["reasoning"]).lower()
                for a in task["actions"]
            )
            break
        elif task["status"] == "failed":
            raise Exception(f"Task failed: {task['error']}")
        time.sleep(1)
    
    # Verify knowledge refined
    response = requests.get(
        f"http://localhost:7860/api/v1/workers/{worker_id}/knowledge"
    )
    final_knowledge = response.json()
    assert len(final_knowledge["relationships"]) > len(mid_knowledge["relationships"])

def test_multi_actor_knowledge(dashboard):
    """Test knowledge sharing between actors."""
    # Create actors
    response = requests.post(
        "http://localhost:7860/api/v1/workers",
        json={"name": "worker_1", "focus_area": "llm_architectures"}
    )
    worker_1 = response.json()["worker_id"]
    
    response = requests.post(
        "http://localhost:7860/api/v1/workers",
        json={"name": "worker_2", "focus_area": "llm_training"}
    )
    worker_2 = response.json()["worker_id"]
    
    # First worker learns about architectures
    response = requests.post(
        f"http://localhost:7860/api/v1/workers/{worker_1}/tasks",
        json={
            "input": "Research LLM architecture patterns",
            "context": {"source": "web"}
        }
    )
    task_1 = response.json()["task_id"]
    
    # Wait for completion
    while True:
        response = requests.get(f"http://localhost:7860/api/v1/tasks/{task_1}")
        if response.json()["status"] == "completed":
            break
        time.sleep(1)
    
    # Second worker uses shared knowledge
    response = requests.post(
        f"http://localhost:7860/api/v1/workers/{worker_2}/tasks",
        json={
            "input": "How do these architectures affect training?",
            "context": {"related_focus": "llm_architectures"}
        }
    )
    task_2 = response.json()["task_id"]
    
    # Wait for completion
    while True:
        response = requests.get(f"http://localhost:7860/api/v1/tasks/{task_2}")
        task = response.json()
        if task["status"] == "completed":
            # Verify used shared knowledge
            assert any(
                "architecture" in str(a["reasoning"]).lower()
                for a in task["actions"]
            )
            break
        time.sleep(1)
    
    # Verify knowledge graph connections
    response = requests.get("/api/v1/knowledge")
    knowledge = response.json()
    
    # Should have cross-domain relationships
    assert any(
        r["from_focus"] == "llm_architectures" and r["to_focus"] == "llm_training"
        for r in knowledge["relationships"]
    )