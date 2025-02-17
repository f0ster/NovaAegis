"""
Environment profile selection and configuration interface.
Handles loading, saving, and switching between environment profiles.
"""
import gradio as gr
from typing import Dict, Any

from ....environment_forge import EnvironmentForge, EnvironmentProfile

def create_environment_selector(forge: EnvironmentForge) -> Dict[str, Any]:
    """Create the environment profile selection interface."""
    with gr.Column() as selector:
        gr.Markdown("## Environment Profiles")
        profile_dropdown = gr.Dropdown(
            choices=forge.list_profiles(),
            value=forge.active_profile,
            label="Select Profile",
            interactive=True
        )
        
        with gr.Row():
            profile_name = gr.Textbox(
                label="New Profile Name",
                placeholder="Enter name for new profile"
            )
            profile_desc = gr.Textbox(
                label="Description",
                placeholder="Enter profile description"
            )
            
        with gr.Row():
            save_btn = gr.Button("💾 Save Current as Profile")
            delete_btn = gr.Button("🗑️ Delete Profile")
            
    return {
        "container": selector,
        "dropdown": profile_dropdown,
        "name": profile_name,
        "description": profile_desc,
        "save_btn": save_btn,
        "delete_btn": delete_btn
    }