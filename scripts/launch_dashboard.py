"""
Launch script for NovaAegis web interface.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from nova_aegis.web.app import launch_app

def main():
    """Launch the NovaAegis web interface."""
    try:
        # Get host/port from environment or use defaults
        host = os.getenv("NOVA_AEGIS_HOST", "0.0.0.0")
        port = int(os.getenv("NOVA_AEGIS_PORT", "7860"))
        
        # Launch the app
        launch_app(host=host, port=port)
        
    except Exception as e:
        print(f"Failed to launch NovaAegis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()