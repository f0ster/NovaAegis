"""
Main system monitoring interface for NovaAegis.
Assembles monitoring components into a unified dashboard.
"""
import gradio as gr
from typing import Dict, Any

from ...core.system_service import SystemService
from ...environment_forge import EnvironmentForge
from .monitoring.health_monitor import create_health_monitor
from .profiles.environment_selector import create_environment_selector
from .services.core_service_config import create_service_config

def create_system_monitor(system: SystemService, forge: EnvironmentForge) -> Dict[str, Any]:
    """Create the main system monitoring interface."""
    active_profile = forge.get_profile()
    
    with gr.Column() as monitor:
        # Environment profile selection
        profile_controls = create_environment_selector(forge)
        
        # Service configuration
        service_controls = create_service_config(active_profile)
        
        # Health monitoring
        health_display = create_health_monitor(system)
        
        # Wire up event handlers
        def build_config() -> Dict[str, Any]:
            """Build service configuration from current settings."""
            return {
                "knowledge_store": {
                    "provider": service_controls["kg_provider"].value,
                    "url": service_controls["kg_url"].value
                },
                "parameter_store": {
                    "provider": service_controls["ps_provider"].value,
                    "url": service_controls["ps_url"].value
                },
                "llm_interface": {
                    "provider": service_controls["llm_provider"].value,
                    "model": service_controls["llm_model"].value
                }
            }
            
        service_controls["start_btn"].click(
            fn=lambda: system.start_service(build_config()),
            outputs=[health_display["health_table"], health_display["system_log"]]
        )
        
        service_controls["stop_btn"].click(
            fn=system.stop_all,
            outputs=[health_display["health_table"], health_display["system_log"]]
        )
        
        # Handle profile changes
        def load_profile(profile_name: str):
            """Load configuration from selected profile."""
            profile = forge.get_profile(profile_name)
            forge.set_active_profile(profile_name)
            
            return {
                service_controls["kg_provider"]: profile.services.get("knowledge_store", {}).get("provider", "neo4j"),
                service_controls["kg_url"]: profile.services.get("knowledge_store", {}).get("url", ""),
                service_controls["ps_provider"]: profile.services.get("parameter_store", {}).get("provider", "postgres"),
                service_controls["ps_url"]: profile.services.get("parameter_store", {}).get("url", ""),
                service_controls["llm_provider"]: profile.services.get("llm_interface", {}).get("provider", "openai"),
                service_controls["llm_model"]: profile.services.get("llm_interface", {}).get("model", ""),
                health_display["system_log"]: f"Loaded configuration from profile: {profile_name}"
            }
            
        profile_controls["dropdown"].change(
            fn=load_profile,
            inputs=[profile_controls["dropdown"]],
            outputs=[
                service_controls["kg_provider"],
                service_controls["kg_url"],
                service_controls["ps_provider"],
                service_controls["ps_url"],
                service_controls["llm_provider"],
                service_controls["llm_model"],
                health_display["system_log"]
            ]
        )
        
        def save_profile(name: str, desc: str):
            """Save current configuration as new profile."""
            if not name:
                return {health_display["system_log"]: "Error: Profile name is required"}
                
            try:
                profile = forge.create_profile(
                    name=name,
                    description=desc or f"Configuration profile: {name}",
                    services={
                        "knowledge_store": {
                            "provider": service_controls["kg_provider"].value,
                            "url": service_controls["kg_url"].value
                        },
                        "parameter_store": {
                            "provider": service_controls["ps_provider"].value,
                            "url": service_controls["ps_url"].value
                        },
                        "llm_interface": {
                            "provider": service_controls["llm_provider"].value,
                            "model": service_controls["llm_model"].value
                        }
                    }
                )
                return {
                    profile_controls["dropdown"]: gr.update(choices=forge.list_profiles()),
                    health_display["system_log"]: f"Saved configuration as profile: {name}"
                }
            except ValueError as e:
                return {health_display["system_log"]: f"Error saving profile: {e}"}
                
        profile_controls["save_btn"].click(
            fn=save_profile,
            inputs=[profile_controls["name"], profile_controls["description"]],
            outputs=[profile_controls["dropdown"], health_display["system_log"]]
        )
        
        def delete_profile(name: str):
            """Delete selected profile."""
            try:
                forge.destroy_profile(name)
                return {
                    profile_controls["dropdown"]: gr.update(choices=forge.list_profiles(), value="default"),
                    health_display["system_log"]: f"Deleted profile: {name}"
                }
            except ValueError as e:
                return {health_display["system_log"]: f"Error deleting profile: {e}"}
                
        profile_controls["delete_btn"].click(
            fn=delete_profile,
            inputs=[profile_controls["dropdown"]],
            outputs=[profile_controls["dropdown"], health_display["system_log"]]
        )
        
    return {
        "container": monitor,
        "profile_controls": profile_controls,
        "service_controls": service_controls,
        "health_display": health_display
    }