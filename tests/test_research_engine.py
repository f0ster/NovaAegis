"""Tests for code research capabilities."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from nova_aegis.research_engine import (
    ResearchEngine,
    ResearchQuery,
    ResearchResult
)

# Test data
MOCK_GITHUB_RESULTS = [
    {
        "url": "https://github.com/user/repo/blob/main/example.py",
        "code": """
def process_data(items: list) -> list:
    return [item * 2 for item in items if item > 0]
""",
        "stars": 100
    },
    {
        "url": "https://github.com/user/repo/blob/main/utils.py",
        "code": """
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
""",
        "stars": 50
    }
]

MOCK_STACKOVERFLOW_RESULTS = [
    {
        "url": "https://stackoverflow.com/questions/1234",
        "code": """
def memoize(func):
    cache = {}
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper
""",
        "votes": 42,
        "accepted": True
    }
]

MOCK_DOCS_RESULTS = [
    {
        "url": "https://docs.python.org/3/library/asyncio.html",
        "code": """
async def main():
    task = asyncio.create_task(other_function())
    await task
""",
        "section": "Tasks"
    }
]

@pytest.fixture
async def mock_browser():
    """Mock browser pilot."""
    browser = AsyncMock()
    browser.search_github.return_value = MOCK_GITHUB_RESULTS
    browser.search_stackoverflow.return_value = MOCK_STACKOVERFLOW_RESULTS
    browser.search_documentation.return_value = MOCK_DOCS_RESULTS
    return browser

@pytest.fixture
async def mock_knowledge_base():
    """Mock knowledge base."""
    kb = AsyncMock()
    kb.find_similar_research.return_value = []
    kb.store_research_result = AsyncMock()
    return kb

@pytest.fixture
async def research_engine(mock_browser, mock_knowledge_base):
    """Create research engine with mocked dependencies."""
    return ResearchEngine(mock_browser, mock_knowledge_base)

@pytest.mark.asyncio
async def test_basic_research(research_engine):
    """Test basic code research functionality."""
    query = ResearchQuery(
        query_text="async data processing",
        language="python"
    )
    
    results = await research_engine.research_code(query)
    
    assert len(results) > 0
    assert all(isinstance(r, ResearchResult) for r in results)
    assert all(r.relevance_score > 0 for r in results)

@pytest.mark.asyncio
async def test_cached_results(research_engine, mock_knowledge_base):
    """Test using cached research results."""
    # Setup mock cached results
    cached_results = [
        ResearchResult(
            source_url="https://example.com/cached",
            code_segment="def cached_function(): pass",
            language="python",
            relevance_score=0.9,
            context={"source": "cache"}
        )
    ]
    mock_knowledge_base.find_similar_research.return_value = cached_results
    
    query = ResearchQuery(
        query_text="cached example",
        language="python",
        max_results=1
    )
    
    results = await research_engine.research_code(query)
    
    assert len(results) == 1
    assert results[0].source_url == "https://example.com/cached"
    # Should not perform live research if cache hits are sufficient
    research_engine.browser.search_github.assert_not_called()

@pytest.mark.asyncio
async def test_multi_source_research(research_engine):
    """Test research across multiple sources."""
    query = ResearchQuery(
        query_text="data processing",
        language="python",
        max_results=5
    )
    
    results = await research_engine.research_code(query)
    
    # Check results from different sources
    sources = {r.context["source"] for r in results}
    assert "github" in sources
    assert "stackoverflow" in sources
    
    # Results should be sorted by relevance
    scores = [r.relevance_score for r in results]
    assert scores == sorted(scores, reverse=True)

@pytest.mark.asyncio
async def test_relevance_scoring(research_engine):
    """Test relevance scoring of research results."""
    query = ResearchQuery(
        query_text="async data processing",
        language="python"
    )
    
    results = await research_engine.research_code(query)
    
    # Results containing query terms should have higher relevance
    for result in results:
        if "async" in result.code_segment.lower():
            assert result.relevance_score > 0.5

@pytest.mark.asyncio
async def test_source_quality_ranking(research_engine):
    """Test source quality affects result ranking."""
    query = ResearchQuery(query_text="example")
    
    results = await research_engine.research_code(query)
    
    # Documentation should rank higher than other sources
    doc_results = [r for r in results if r.context["source"] == "documentation"]
    other_results = [r for r in results if r.context["source"] != "documentation"]
    
    if doc_results and other_results:
        assert doc_results[0].relevance_score >= other_results[0].relevance_score

@pytest.mark.asyncio
async def test_knowledge_base_updates(research_engine, mock_knowledge_base):
    """Test knowledge base is updated with new findings."""
    query = ResearchQuery(
        query_text="new research",
        max_results=2
    )
    
    await research_engine.research_code(query)
    
    # Should store new research results
    assert mock_knowledge_base.store_research_result.called
    call_count = mock_knowledge_base.store_research_result.call_count
    assert call_count > 0

@pytest.mark.asyncio
async def test_error_handling(research_engine, mock_browser):
    """Test handling of research errors."""
    # Simulate GitHub API error
    mock_browser.search_github.side_effect = Exception("API Error")
    
    query = ResearchQuery(query_text="error test")
    
    # Should still return results from other sources
    results = await research_engine.research_code(query)
    assert len(results) > 0
    assert all(r.context["source"] != "github" for r in results)

@pytest.mark.asyncio
async def test_language_specific_research(research_engine):
    """Test language-specific research capabilities."""
    # Python research
    py_query = ResearchQuery(
        query_text="async function",
        language="python"
    )
    py_results = await research_engine.research_code(py_query)
    assert any(r.language == "python" for r in py_results)
    
    # JavaScript research
    js_query = ResearchQuery(
        query_text="async function",
        language="javascript"
    )
    js_results = await research_engine.research_code(js_query)
    assert any(r.language == "javascript" for r in js_results)

@pytest.mark.asyncio
async def test_result_deduplication(research_engine):
    """Test deduplication of research results."""
    # Mock duplicate results
    duplicate_url = "https://example.com/duplicate"
    mock_results = [
        {
            "url": duplicate_url,
            "code": "def example(): pass",
            "stars": 10
        },
        {
            "url": duplicate_url,  # Same URL
            "code": "def example(): pass",
            "stars": 5
        }
    ]
    research_engine.browser.search_github.return_value = mock_results
    
    query = ResearchQuery(query_text="duplicate test")
    results = await research_engine.research_code(query)
    
    # Should only include one copy of duplicate results
    urls = [r.source_url for r in results]
    assert urls.count(duplicate_url) == 1

@pytest.mark.asyncio
async def test_context_aware_research(research_engine):
    """Test context-aware research capabilities."""
    query = ResearchQuery(
        query_text="database connection",
        context={
            "framework": "django",
            "database": "postgresql"
        }
    )
    
    results = await research_engine.research_code(query)
    
    # Results should be influenced by context
    assert any(
        "django" in r.code_segment.lower() or 
        "postgresql" in r.code_segment.lower() 
        for r in results
    )