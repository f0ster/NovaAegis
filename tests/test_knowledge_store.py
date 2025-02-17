"""Tests for optimized knowledge storage and retrieval."""
import pytest
import asyncio
from datetime import datetime
import networkx as nx
from typing import Dict, List, Any

from nova_aegis.knowledge_store import KnowledgeStore
from nova_aegis.models import CodePattern, Tag, PatternRelation, PatternUsage
from nova_aegis.database import DatabaseManager

# Test data
SAMPLE_PATTERNS = [
    {
        "name": "React Hook Pattern",
        "code_template": """
const useCustomHook = (initialValue) => {
    const [state, setState] = useState(initialValue);
    useEffect(() => {
        // Effect logic
    }, []);
    return [state, setState];
};
""",
        "description": "Custom hook pattern",
        "tags": ["react", "hooks", "state-management"]
    },
    {
        "name": "HOC Pattern",
        "code_template": """
const withData = (WrappedComponent) => {
    return function WithDataComponent(props) {
        const [data, setData] = useState(null);
        useEffect(() => {
            fetchData().then(setData);
        }, []);
        return <WrappedComponent data={data} {...props} />;
    };
};
""",
        "description": "Higher-order component pattern",
        "tags": ["react", "hoc", "data-fetching"]
    }
]

@pytest.fixture
async def db():
    """Setup test database."""
    db_manager = DatabaseManager("postgresql://postgres:postgres@localhost:5432/test_db")
    await db_manager.create_tables()
    yield db_manager
    await db_manager.drop_tables()

@pytest.fixture
async def store(db):
    """Setup knowledge store."""
    async with db.session() as session:
        store = KnowledgeStore(session)
        await store.initialize()
        yield store
        await store.cleanup()

@pytest.mark.asyncio
async def test_add_pattern(store):
    """Test adding a new pattern."""
    pattern = await store.add_pattern(
        name=SAMPLE_PATTERNS[0]["name"],
        code_template=SAMPLE_PATTERNS[0]["code_template"],
        description=SAMPLE_PATTERNS[0]["description"],
        tags=SAMPLE_PATTERNS[0]["tags"]
    )
    
    assert pattern.id is not None
    assert pattern.name == SAMPLE_PATTERNS[0]["name"]
    assert len(pattern.tags) == len(SAMPLE_PATTERNS[0]["tags"])
    
    # Verify cache
    cached = store.get_pattern(pattern.id)
    assert cached is not None
    assert cached["name"] == pattern.name
    
    # Verify graph
    assert pattern.id in store.graph
    assert store.graph.nodes[pattern.id]["name"] == pattern.name

@pytest.mark.asyncio
async def test_batch_pattern_addition(store):
    """Test adding multiple patterns in batch."""
    patterns = []
    for data in SAMPLE_PATTERNS:
        pattern = await store.add_pattern(
            name=data["name"],
            code_template=data["code_template"],
            description=data["description"],
            tags=data["tags"]
        )
        patterns.append(pattern)
    
    # Verify all patterns were added
    assert len(patterns) == len(SAMPLE_PATTERNS)
    assert all(p.id in store.graph for p in patterns)
    
    # Verify relations were processed
    await store.add_relation(
        patterns[0].id,
        patterns[1].id,
        "related_to",
        weight=1.0
    )
    
    # Force process pending operations
    await store._process_pending_operations()
    
    # Verify relation was added
    assert store.graph.has_edge(patterns[0].id, patterns[1].id)
    assert (patterns[0].id, patterns[1].id) in store._relation_cache

@pytest.mark.asyncio
async def test_pattern_deduplication(store):
    """Test pattern deduplication logic."""
    # Add initial pattern
    pattern1 = await store.add_pattern(
        name=SAMPLE_PATTERNS[0]["name"],
        code_template=SAMPLE_PATTERNS[0]["code_template"],
        description=SAMPLE_PATTERNS[0]["description"],
        tags=SAMPLE_PATTERNS[0]["tags"]
    )
    
    # Try to add similar pattern
    pattern2 = await store.add_pattern(
        name=SAMPLE_PATTERNS[0]["name"],
        code_template=SAMPLE_PATTERNS[0]["code_template"],
        description="Slightly different description",
        tags=["react", "hooks"]
    )
    
    # Should return existing pattern
    assert pattern1.id == pattern2.id

@pytest.mark.asyncio
async def test_pattern_search(store):
    """Test pattern search functionality."""
    # Add test patterns
    for data in SAMPLE_PATTERNS:
        await store.add_pattern(
            name=data["name"],
            code_template=data["code_template"],
            description=data["description"],
            tags=data["tags"]
        )
    
    # Search for hooks
    results = await store.find_patterns("hook")
    assert len(results) > 0
    assert any("Hook" in r["name"] for r in results)
    
    # Search for HOC
    results = await store.find_patterns("hoc")
    assert len(results) > 0
    assert any("HOC" in r["name"] for r in results)

@pytest.mark.asyncio
async def test_related_patterns(store):
    """Test retrieving related patterns."""
    # Add test patterns
    patterns = []
    for data in SAMPLE_PATTERNS:
        pattern = await store.add_pattern(
            name=data["name"],
            code_template=data["code_template"],
            description=data["description"],
            tags=data["tags"]
        )
        patterns.append(pattern)
    
    # Add relations
    await store.add_relation(
        patterns[0].id,
        patterns[1].id,
        "related_to",
        weight=1.0
    )
    
    # Force process relations
    await store._process_pending_operations()
    
    # Get related patterns
    related = store.get_related_patterns(patterns[0].id)
    assert len(related) > 0
    assert any(r["id"] == patterns[1].id for r in related)

@pytest.mark.asyncio
async def test_pattern_usage(store):
    """Test pattern usage tracking."""
    # Add test pattern
    pattern = await store.add_pattern(
        name=SAMPLE_PATTERNS[0]["name"],
        code_template=SAMPLE_PATTERNS[0]["code_template"],
        description=SAMPLE_PATTERNS[0]["description"],
        tags=SAMPLE_PATTERNS[0]["tags"]
    )
    
    # Record usage
    await store.record_pattern_usage(
        pattern.id,
        {"context": "test usage"}
    )
    
    # Verify weight updates
    edges = list(store.graph.edges(pattern.id, data=True))
    if edges:
        assert edges[0][2]["weight"] > 1.0

@pytest.mark.asyncio
async def test_cache_performance(store):
    """Test cache performance."""
    # Add test patterns
    patterns = []
    for i in range(100):  # Add many patterns
        pattern = await store.add_pattern(
            name=f"Pattern {i}",
            code_template=f"template {i}",
            description=f"description {i}",
            tags=["test"]
        )
        patterns.append(pattern)
    
    # Measure cache performance
    start = datetime.now()
    for _ in range(1000):  # Many lookups
        _ = store.get_pattern(patterns[0].id)
    cache_duration = (datetime.now() - start).total_seconds()
    
    # Should be very fast due to caching
    assert cache_duration < 0.1

@pytest.mark.asyncio
async def test_batch_processing(store):
    """Test batch processing performance."""
    # Add many relations
    start = datetime.now()
    pattern_ids = []
    
    # Create patterns
    for i in range(10):
        pattern = await store.add_pattern(
            name=f"Pattern {i}",
            code_template=f"template {i}",
            description=f"description {i}",
            tags=["test"]
        )
        pattern_ids.append(pattern.id)
    
    # Add many relations
    for i in range(len(pattern_ids) - 1):
        await store.add_relation(
            pattern_ids[i],
            pattern_ids[i + 1],
            "related_to",
            weight=1.0
        )
    
    # Force process
    await store._process_pending_operations()
    
    duration = (datetime.now() - start).total_seconds()
    
    # Should be relatively fast due to batching
    assert duration < 1.0
    assert len(store._relation_cache) == len(pattern_ids) - 1

@pytest.mark.asyncio
async def test_graph_consistency(store):
    """Test graph and database consistency."""
    # Add patterns and relations
    patterns = []
    for data in SAMPLE_PATTERNS:
        pattern = await store.add_pattern(
            name=data["name"],
            code_template=data["code_template"],
            description=data["description"],
            tags=data["tags"]
        )
        patterns.append(pattern)
    
    await store.add_relation(
        patterns[0].id,
        patterns[1].id,
        "related_to",
        weight=1.0
    )
    
    await store._process_pending_operations()
    
    # Verify graph structure
    assert nx.is_directed_acyclic_graph(store.graph)
    assert len(store.graph.nodes) == len(patterns)
    assert len(store.graph.edges) == 1
    
    # Verify cache consistency
    assert len(store._pattern_cache) == len(patterns)
    assert len(store._relation_cache) == 1