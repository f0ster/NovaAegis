"""
Test code samples for various scenarios.
Used in integration tests to verify behavior.
"""
from typing import Dict

# Research samples with known patterns
RESEARCH_SAMPLES = {
    "async_error_handling": {
        "code": """
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"API error: {response.status}")
            return await response.json()
""",
        "patterns": ["async/await", "error handling", "http client"],
        "quality": 0.9
    },
    
    "dependency_injection": {
        "code": """
class Service:
    def __init__(self, dependency: Dependency):
        self.dependency = dependency
    
    def process(self, data: dict) -> dict:
        return self.dependency.handle(data)
""",
        "patterns": ["dependency injection", "inversion of control"],
        "quality": 0.8
    },
    
    "state_management": {
        "code": """
class StateManager:
    def __init__(self):
        self._state = {}
        self._listeners = []
    
    def update(self, key: str, value: any):
        self._state[key] = value
        self._notify_listeners(key)
    
    def subscribe(self, listener: callable):
        self._listeners.append(listener)
""",
        "patterns": ["observer pattern", "state management"],
        "quality": 0.85
    }
}

# Test queries with expected results
TEST_QUERIES = {
    "error handling": {
        "relevant_patterns": ["error handling", "exception handling"],
        "min_confidence": 0.7
    },
    "async programming": {
        "relevant_patterns": ["async/await", "coroutines"],
        "min_confidence": 0.8
    },
    "design patterns": {
        "relevant_patterns": ["dependency injection", "observer pattern"],
        "min_confidence": 0.75
    }
}

# Domain-specific samples
DOMAIN_SAMPLES = {
    "python": {
        "async": RESEARCH_SAMPLES["async_error_handling"],
        "patterns": ["python-specific", "pythonic"]
    },
    "javascript": {
        "async": """
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch failed:', error);
        throw error;
    }
}
""",
        "patterns": ["javascript-specific", "promise-based"]
    }
}

# Test feedback data
TEST_FEEDBACK = [
    {
        "query": "async error handling",
        "quality": 0.8,
        "relevance": 0.9,
        "comment": "Good async pattern examples"
    },
    {
        "query": "dependency injection",
        "quality": 0.7,
        "relevance": 0.8,
        "comment": "Clear but could use more context"
    },
    {
        "query": "state management",
        "quality": 0.9,
        "relevance": 0.85,
        "comment": "Excellent pattern implementation"
    }
]