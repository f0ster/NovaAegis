"""
Exploration interface component for NovaAegis.
Handles chat, knowledge visualization, and insights.
"""
import gradio as gr
from typing import Dict, Any

def create_exploration_tab() -> Dict[str, Any]:
    """Create the exploration interface tab."""
    with gr.Row() as exploration:
        # Left column - Chat and controls
        with gr.Column(scale=1):
            # Chat history
            chat_box = gr.Chatbot(
                label="Conversation",
                height=400
            )
            
            # Input
            with gr.Row():
                input_text = gr.Textbox(
                    label="Talk with NovaAegis",
                    placeholder="Ask me anything about software development..."
                )
                send_btn = gr.Button("Send")
                
            # Session controls
            with gr.Row():
                start_btn = gr.Button("Start Session")
                end_btn = gr.Button("End Session")
                
        # Right column - Visual journey
        with gr.Column(scale=2):
            # Knowledge visualization
            with gr.Tab("Knowledge Map"):
                graph_plot = gr.Plot(
                    label="Knowledge Visualization"
                )
                
            # Insights
            with gr.Tab("Insights"):
                insights_md = gr.Markdown()
                
            # Visual journey
            with gr.Tab("Visual Journey"):
                journey_gallery = gr.Gallery()
                
    return {
        "container": exploration,
        "chat_box": chat_box,
        "input_text": input_text,
        "send_btn": send_btn,
        "start_btn": start_btn,
        "end_btn": end_btn,
        "graph_plot": graph_plot,
        "insights_md": insights_md,
        "journey_gallery": journey_gallery
    }