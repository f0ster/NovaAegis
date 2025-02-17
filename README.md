# NovaAegis

NovaAegis is an advanced exploration companion that combines knowledge discovery with protective guidance. Like a shield (Aegis) guiding you through new knowledge (Nova), it helps explore and understand complex information through continuous learning and visual interaction.

## Core Architecture

### ExplorationCompanion
The core entity that drives NovaAegis's cognitive processes:
- **Perception**: Takes in and processes new information through browser interaction
- **Learning**: Builds and refines knowledge through graph structures
- **Understanding**: Maintains and evolves comprehension state
- **Action**: Generates insights and responses based on understanding

### Knowledge Building
- Real-time knowledge graph construction
- Pattern recognition and relationship mapping
- Confidence tracking and refinement
- Visual state tracking

### Browser Integration
- Intelligent web exploration
- Visual state capture
- Progress tracking
- Content indexing

## Usage Example

```python
from nova_aegis.core.nova_aegis import NovaAegis

# Initialize NovaAegis
aegis = NovaAegis()
await aegis.start_session()

# Start research exploration
response = await aegis.process_request(
    "Research recent HuggingFace papers about LLM architectures"
)

# Monitor research progress
companion = aegis.companion
while companion.browser_pilot.is_processing:
    status = companion.browser_pilot.get_job_status()
    print(f"Processed: {status.papers_processed}")
    
# Get insights
response = await aegis.process_request(
    "What have you found so far?"
)
print(response["insights"])

# End session
await aegis.end_session()
```

## Development

### Project Structure
```
nova_aegis/
├── core/
│   ├── companion.py     # Core ExplorationCompanion
│   └── nova_aegis.py    # NovaAegis implementation
├── graph/
│   ├── schema.py        # Knowledge graph schema
│   └── visualization.py # Graph visualization
├── browser/
│   └── pilot.py        # Browser automation
└── web/
    └── app.py          # Web interface
```

### Setup

1. Install dependencies:
```bash
pipenv install --dev
pipenv run playwright install
```

2. Start services:
```bash
docker-compose up -d
```

3. Initialize database:
```bash
just init-db
```

4. Run tests:
```bash
just test
```

### Running

Start NovaAegis:
```bash
just up
```

Visit http://localhost:7860 to interact with NovaAegis.

### Testing

Run specific test:
```bash
just test-e2e
```

Run browser automation test:
```bash
just test-browser
```

### Key Components

#### ExplorationCompanion
The core entity that processes and learns:
```python
class ExplorationCompanion:
    async def perceive(self, stimulus: Any):
        """Process new information."""
        
    async def learn(self):
        """Build understanding."""
        
    def get_understanding(self):
        """Get current understanding state."""
```

#### Browser Pilot
Handles web interaction and visual capture:
```python
class BrowserPilot:
    async def explore(self, topic: str):
        """Explore a topic."""
        
    def get_visual_states(self):
        """Get captured visual states."""
```

#### Knowledge Store
Manages knowledge graph and patterns:
```python
class KnowledgeStore:
    def add_paper(self, paper: Paper):
        """Add paper to knowledge."""
        
    def get_patterns(self):
        """Get recognized patterns."""
```

## Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## License

MIT License - see LICENSE file

## Acknowledgments

- Built with Playwright for browser automation
- Uses NetworkX for knowledge graphs
- Inspired by cognitive architectures
