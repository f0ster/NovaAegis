#!/usr/bin/env python3
"""
Verify and generate previews for Mermaid diagrams.
Uses mermaid-cli to validate syntax and create SVG files.
"""
import asyncio
import json
import subprocess
from pathlib import Path
import structlog
from rich.console import Console
from rich.table import Table

logger = structlog.get_logger()
console = Console()

class DiagramVerifier:
    """Verifies and generates previews for Mermaid diagrams."""
    
    def __init__(self):
        self.docs_dir = Path("docs/diagrams")
        self.preview_dir = self.docs_dir / "previews"
        self.preview_dir.mkdir(exist_ok=True)
        
        self.results = {
            "valid": [],
            "invalid": [],
            "generated": []
        }
    
    async def verify_diagrams(self):
        """Verify all Mermaid diagrams in docs directory."""
        try:
            # Check mermaid-cli installation
            await self._check_mmdc()
            
            # Find all .mmd files
            diagram_files = list(self.docs_dir.glob("*.mmd"))
            
            if not diagram_files:
                console.print("[yellow]No diagram files found")
                return
            
            # Process each diagram
            for file in diagram_files:
                await self._process_diagram(file)
            
            # Show results
            self._show_results()
            
        except Exception as e:
            logger.error("verification_failed", error=str(e))
            raise
    
    async def _check_mmdc(self):
        """Check if mermaid-cli is installed."""
        try:
            process = await asyncio.create_subprocess_exec(
                "mmdc", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                console.print(
                    "[red]mermaid-cli not found. Install with:"
                    "\n npm install -g @mermaid-js/mermaid-cli"
                )
                raise RuntimeError("mermaid-cli not installed")
            
        except FileNotFoundError:
            console.print(
                "[red]mermaid-cli not found. Install with:"
                "\n npm install -g @mermaid-js/mermaid-cli"
            )
            raise
    
    async def _process_diagram(self, file: Path):
        """Process a single diagram file."""
        console.print(f"\n[bold blue]Processing {file.name}")
        
        # Validate syntax
        if await self._validate_syntax(file):
            self.results["valid"].append(file.name)
            
            # Generate preview
            preview_file = self.preview_dir / f"{file.stem}.svg"
            if await self._generate_preview(file, preview_file):
                self.results["generated"].append(file.name)
        else:
            self.results["invalid"].append(file.name)
    
    async def _validate_syntax(self, file: Path) -> bool:
        """Validate Mermaid syntax."""
        try:
            process = await asyncio.create_subprocess_exec(
                "mmdc", "--validate", "-i", str(file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                console.print(f"[green]✓ Valid syntax: {file.name}")
                return True
            else:
                console.print(f"[red]✗ Invalid syntax: {file.name}")
                console.print(stderr.decode())
                return False
            
        except Exception as e:
            logger.error("validation_failed", file=file.name, error=str(e))
            return False
    
    async def _generate_preview(self, source: Path, target: Path) -> bool:
        """Generate SVG preview."""
        try:
            process = await asyncio.create_subprocess_exec(
                "mmdc",
                "-i", str(source),
                "-o", str(target),
                "-c", "scripts/mermaid.config.json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                console.print(f"[green]✓ Generated preview: {target.name}")
                return True
            else:
                console.print(f"[red]✗ Preview generation failed: {target.name}")
                console.print(stderr.decode())
                return False
            
        except Exception as e:
            logger.error("preview_generation_failed", file=source.name, error=str(e))
            return False
    
    def _show_results(self):
        """Show verification results."""
        table = Table(title="Diagram Verification Results")
        
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Files", style="blue")
        
        table.add_row(
            "Valid",
            str(len(self.results["valid"])),
            ", ".join(self.results["valid"])
        )
        
        table.add_row(
            "Invalid",
            str(len(self.results["invalid"])),
            ", ".join(self.results["invalid"])
        )
        
        table.add_row(
            "Previews Generated",
            str(len(self.results["generated"])),
            ", ".join(self.results["generated"])
        )
        
        console.print("\n")
        console.print(table)

def create_config():
    """Create mermaid-cli config file."""
    config = {
        "theme": "default",
        "themeVariables": {
            "primaryColor": "#007bff",
            "primaryTextColor": "#fff",
            "primaryBorderColor": "#0056b3",
            "lineColor": "#666",
            "secondaryColor": "#6c757d",
            "tertiaryColor": "#f8f9fa"
        }
    }
    
    config_path = Path("scripts/mermaid.config.json")
    config_path.parent.mkdir(exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2))

async def main():
    """Main entry point."""
    # Create config file
    create_config()
    
    # Verify diagrams
    verifier = DiagramVerifier()
    await verifier.verify_diagrams()

if __name__ == "__main__":
    asyncio.run(main())