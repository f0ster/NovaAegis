"""
Real-time health monitoring for core system services.
Displays service status, response times, and system logs.
"""
import gradio as gr
from typing import Dict, List, Any

from ....core.service_provider import ServiceState
from ....core.system_service import SystemService

def get_service_health(system: SystemService) -> List[List[str]]:
    """Get current health status of core services."""
    health_status = []
    for service_type, health in system.get_service_status().items():
        health_status.append([
            "🟢" if health.state == ServiceState.READY else 
            "🟡" if health.state == ServiceState.DEGRADED else "🔴",
            service_type,
            f"{health.response_time_ms:.1f}ms" if health.response_time_ms else "N/A",
            health.state.name,
            health.last_error or ""
        ])
    return health_status

def create_health_monitor(system: SystemService) -> Dict[str, Any]:
    """Create the service health monitoring display."""
    with gr.Column() as monitor:
        gr.Markdown("## Core Services")
        
        # Health status table with auto-refresh
        health_table = gr.Dataframe(
            headers=["Status", "Service", "Response Time", "State", "Last Error"],
            value=get_service_health(system),
            interactive=False,
            every=1  # Auto-refresh every second
        )
        
        # System logs
        gr.Markdown("## System Logs")
        system_log = gr.Textbox(
            label="Logs",
            value="",
            lines=10,
            max_lines=10
        )
        
    return {
        "container": monitor,
        "health_table": health_table,
        "system_log": system_log
    }