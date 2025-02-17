"""
Core service configuration interface.
Handles configuration of knowledge store, parameter store, and LLM services.
"""
import gradio as gr
from typing import Dict, Any

from ....core.service_provider import SERVICE_REGISTRY
from ....environment_forge import EnvironmentProfile

def create_service_config(active_profile: EnvironmentProfile) -> Dict[str, Any]:
    """Create the core service configuration interface."""
    with gr.Column() as config:
        with gr.Row():
            # Knowledge Store Config
            with gr.Column():
                gr.Markdown("### Knowledge Store")
                kg_provider = gr.Dropdown(
                    choices=list(SERVICE_REGISTRY["knowledge_store"].keys()),
                    value=active_profile.services.get("knowledge_store", {}).get("provider", "neo4j"),
                    label="Provider"
                )
                kg_url = gr.Textbox(
                    value=active_profile.services.get("knowledge_store", {}).get("url", ""),
                    label="URL"
                )
                
            # Parameter Store Config  
            with gr.Column():
                gr.Markdown("### Parameter Store")
                ps_provider = gr.Dropdown(
                    choices=list(SERVICE_REGISTRY["parameter_store"].keys()),
                    value=active_profile.services.get("parameter_store", {}).get("provider", "postgres"),
                    label="Provider"
                )
                ps_url = gr.Textbox(
                    value=active_profile.services.get("parameter_store", {}).get("url", ""),
                    label="URL"
                )
                
            # LLM Interface Config
            with gr.Column():
                gr.Markdown("### LLM Interface")
                llm_provider = gr.Dropdown(
                    choices=list(SERVICE_REGISTRY["llm_interface"].keys()),
                    value=active_profile.services.get("llm_interface", {}).get("provider", "openai"),
                    label="Provider"
                )
                llm_model = gr.Textbox(
                    value=active_profile.services.get("llm_interface", {}).get("model", ""),
                    label="Model"
                )
                
        with gr.Row():
            start_btn = gr.Button("▶️ Start Services")
            stop_btn = gr.Button("⏹️ Stop Services")
            
    return {
        "container": config,
        "kg_provider": kg_provider,
        "kg_url": kg_url,
        "ps_provider": ps_provider,
        "ps_url": ps_url,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "start_btn": start_btn,
        "stop_btn": stop_btn
    }