#!/usr/bin/env python3
"""
Demonstrates complete research workflow through browser interaction.
Shows NovaAegis analyzing HuggingFace papers and building knowledge.
"""
import asyncio
from playwright.async_api import async_playwright
import structlog
from pathlib import Path
import json
import time
from datetime import datetime

logger = structlog.get_logger()

class ResearchDemo:
    """Demonstrates research workflow through browser."""
    
    def __init__(self):
        self.url = "http://localhost:7860"
        self.logger = logger.bind(component="research_demo")
        
        # Track demo state
        self.results_dir = Path("demo_results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def run_demo(self):
        """Run complete research workflow demo."""
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Step 1: Setup
                await self._setup_environment(page)
                
                # Step 2: Create project
                await self._create_project(page)
                
                # Step 3: Configure LLM
                await self._configure_llm(page)
                
                # Step 4: Initial research
                results = await self._run_initial_research(page)
                
                # Step 5: Follow-up research
                refined_results = await self._run_followup_research(page)
                
                # Step 6: Export results
                await self._export_results(page, results, refined_results)
                
                # Clean up
                await context.close()
                await browser.close()
                
        except Exception as e:
            self.logger.error("demo_failed", error=str(e))
            raise
    
    async def _setup_environment(self, page):
        """Setup research environment."""
        self.logger.info("setting_up_environment")
        
        # Load interface
        await page.goto(self.url)
        await page.wait_for_selector("h1:has-text('NovaAegis Research Assistant')")
        
        # Create results directory for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_results_dir = self.results_dir / timestamp
        self.current_results_dir.mkdir()
    
    async def _create_project(self, page):
        """Create research project."""
        self.logger.info("creating_project")
        
        # Go to Projects tab
        await page.click("text=Projects")
        await page.click("button:has-text('New Group')")
        
        # Create LLM Research group
        await page.fill("input[aria-label='Group Name']", "LLM Research")
        await page.fill("textarea[aria-label='Description']", "Research on LLM architectures and techniques")
        await page.click("button:has-text('Create')")
        
        # Create project
        await page.click("button:has-text('New Project')")
        await page.fill("input[aria-label='Project Name']", "HF Papers Analysis")
        await page.fill("textarea[aria-label='Description']", "Analysis of recent HuggingFace papers")
        await page.click("text=LLM Research")  # Select group
        await page.click("button:has-text('Create')")
        
        # Verify creation
        await page.wait_for_selector("text=HF Papers Analysis")
    
    async def _configure_llm(self, page):
        """Configure LLM settings."""
        self.logger.info("configuring_llm")
        
        # Go to LLM Settings
        await page.click("text=LLM Settings")
        
        # Configure local model
        await page.click("text=Local")
        await page.select_option("select[aria-label='Local Model']", "llama2-7b")
        await page.fill("input[aria-label='Model Path']", "models/llama2-7b")
        
        # Set parameters
        await page.fill("input[aria-label='Temperature']", "0.7")
        await page.fill("input[aria-label='Max Tokens']", "2000")
        
        # Save settings
        await page.click("button:has-text('Save LLM Settings')")
        await page.wait_for_selector("text=Settings saved successfully")
    
    async def _run_initial_research(self, page):
        """Run initial research query."""
        self.logger.info("running_initial_research")
        
        # Go to Research tab
        await page.click("text=Research")
        
        # Enter research query
        await page.fill("textarea[aria-label='Research Request']", """
        Research recent HuggingFace papers about LLM architectures.
        Focus on:
        - Novel architecture approaches
        - Performance improvements
        - Training innovations
        Create a structured knowledge graph and provide insights.
        """)
        
        # Configure research
        await page.fill("input[aria-label='Focus Level']", "0.8")
        await page.fill("input[aria-label='Research Depth']", "4")
        
        # Start research
        await page.click("button:has-text('Begin Research')")
        
        # Wait for completion
        await page.wait_for_selector("#knowledge-graph svg", timeout=60000)
        await page.wait_for_selector(".results-container")
        
        # Capture results
        results = {
            "graph_data": await self._capture_graph_data(page),
            "insights": await page.text_content(".results-container"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save screenshot
        await page.screenshot(
            path=str(self.current_results_dir / "initial_research.png")
        )
        
        return results
    
    async def _run_followup_research(self, page):
        """Run follow-up research based on initial findings."""
        self.logger.info("running_followup_research")
        
        # Enter follow-up query
        await page.fill("textarea[aria-label='Research Request']", """
        Based on the previous research, what are the most promising
        approaches for improving LLM training efficiency?
        Focus on practical implementations and benchmarks.
        """)
        
        # Start research
        await page.click("button:has-text('Begin Research')")
        
        # Wait for completion
        await page.wait_for_selector("#knowledge-graph svg", timeout=60000)
        await page.wait_for_selector(".results-container")
        
        # Capture results
        results = {
            "graph_data": await self._capture_graph_data(page),
            "insights": await page.text_content(".results-container"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save screenshot
        await page.screenshot(
            path=str(self.current_results_dir / "followup_research.png")
        )
        
        return results
    
    async def _export_results(self, page, initial_results, followup_results):
        """Export and save research results."""
        self.logger.info("exporting_results")
        
        # Save results
        results_file = self.current_results_dir / "research_results.json"
        results_file.write_text(json.dumps({
            "initial_research": initial_results,
            "followup_research": followup_results,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "project": "HF Papers Analysis"
            }
        }, indent=2))
        
        # Export from UI
        await page.click("button:has-text('Export')")
        
        # Wait for download
        download = await page.wait_for_event("download")
        await download.save_as(
            str(self.current_results_dir / "exported_results.json")
        )
    
    async def _capture_graph_data(self, page):
        """Capture knowledge graph data."""
        return await page.evaluate("""
            () => {
                const graphElement = document.querySelector("#knowledge-graph");
                return {
                    nodes: graphElement.__data__.nodes,
                    edges: graphElement.__data__.edges
                };
            }
        """)

async def main():
    """Run research workflow demo."""
    demo = ResearchDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())