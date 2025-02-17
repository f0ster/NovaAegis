"""
Browser DSL for agent interoperability.
Provides a rich domain-specific language for browser interaction.
"""
from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import Field
from ...browser_pilot import BrowserPilot

class BrowserTool(BaseTool):
    """Browser DSL for standardized web interaction."""
    
    name: str = Field(
        default="browser",
        description="Browser interface"
    )
    description: str = Field(
        default="""Browser interface with rich interaction DSL:

    # Core Navigation
    goto(url)          - Navigate to URL
    back()            - Go back one page
    forward()         - Go forward one page
    refresh()         - Refresh current page
    
    # Element Interaction
    click(selector)   - Click element
    type(selector, text) - Type into element
    submit(selector)  - Submit form
    hover(selector)   - Hover over element
    focus(selector)   - Focus element
    blur(selector)    - Remove focus
    
    # Content Extraction
    read(selector)    - Get element text
    html(selector)    - Get element HTML
    attr(selector, name) - Get attribute value
    
    # Element State
    exists(selector)  - Check existence
    visible(selector) - Check visibility
    enabled(selector) - Check if enabled
    selected(selector) - Check if selected
    
    # Page State
    url()            - Get current URL
    title()          - Get page title
    ready()          - Check if page loaded
    
    # Waiting
    wait(selector)   - Wait for element
    wait_gone(selector) - Wait for element removal
    wait_visible(selector) - Wait for visibility
    
    # Screenshots
    screenshot()     - Capture full page
    screenshot(selector) - Capture element
    
    Returns operation result.""",
        description="Interface description"
    )
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {"headless": True},
        description="Browser settings"
    )
    pilot: Optional[BrowserPilot] = Field(
        default=None,
        description="Browser pilot instance"
    )
    
    def _ensure_pilot(self):
        """Ensure browser pilot is initialized."""
        if not self.pilot:
            self.pilot = BrowserPilot(**self.settings)
            self.pilot.__enter__()
            
    def _run(self, tool_input: str) -> str:
        """Execute browser DSL command."""
        try:
            # Parse DSL command
            command = self._parse_dsl(tool_input)
            
            # Initialize if needed
            self._ensure_pilot()
            
            # Execute command
            result = self.pilot.execute(command)
            
            # Format result
            return self._format_result(result)
            
        except Exception as e:
            return f"Error: {str(e)}"
            
    def _parse_dsl(self, dsl_input: str) -> Dict[str, Any]:
        """Parse DSL command into browser pilot command."""
        # Extract command name and args
        cmd = dsl_input.strip()
        name = cmd[:cmd.index("(")]
        args = cmd[cmd.index("(")+1:cmd.rindex(")")]
        
        # Core navigation
        if name == "goto":
            return {
                "type": "navigate",
                "url": args.strip("'\"")
            }
        elif name in ["back", "forward", "refresh"]:
            return {"type": name}
            
        # Element interaction
        elif name == "click":
            return {
                "type": "click",
                "selector": args.strip("'\"")
            }
        elif name == "type":
            selector, text = args.split(",", 1)
            return {
                "type": "type",
                "selector": selector.strip("'\" "),
                "text": text.strip("'\" ")
            }
        elif name in ["submit", "hover", "focus", "blur"]:
            return {
                "type": name,
                "selector": args.strip("'\"")
            }
            
        # Content extraction
        elif name in ["read", "html"]:
            return {
                "type": "extract",
                "selector": args.strip("'\""),
                "extract": name
            }
        elif name == "attr":
            selector, attr = args.split(",", 1)
            return {
                "type": "extract",
                "selector": selector.strip("'\" "),
                "extract": "attribute",
                "attribute": attr.strip("'\" ")
            }
            
        # Element state
        elif name in ["exists", "visible", "enabled", "selected"]:
            return {
                "type": "check",
                "selector": args.strip("'\""),
                "check": name
            }
            
        # Page state
        elif name in ["url", "title", "ready"]:
            return {"type": name}
            
        # Waiting
        elif name.startswith("wait"):
            wait_type = name[5:] if len(name) > 4 else "present"
            return {
                "type": "wait",
                "selector": args.strip("'\""),
                "wait_type": wait_type
            }
            
        # Screenshots
        elif name == "screenshot":
            if args:
                return {
                    "type": "screenshot",
                    "selector": args.strip("'\"")
                }
            return {"type": "screenshot"}
            
        else:
            raise ValueError(f"Unknown DSL command: {name}")
            
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format command result for agent."""
        if not result["success"]:
            return f"Failed: {result['error']}"
            
        if "result" in result:
            return str(result["result"])
            
        return "Success"
            
    async def _arun(self, tool_input: str) -> str:
        """Execute browser DSL command async."""
        # Async just calls sync for now
        return self._run(tool_input)