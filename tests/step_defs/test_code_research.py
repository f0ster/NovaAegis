"""Step definitions for code research behavior tests"""
import pytest
from pytest_bdd import scenario, given, when, then, parsers
import asyncio
from pathlib import Path
import os

from nova_aegis.assistant import CodeAssistant
from nova_aegis.database import DatabaseManager
from nova_aegis.models import Project, CodePattern

# Scenarios
@scenario('../features/code_research.feature', 'Research React Component Patterns')
def test_research_patterns():
    """Test researching React patterns"""
    pass

@scenario('../features/code_research.feature', 'Analyze Code Implementation')
def test_analyze_code():
    """Test code analysis"""
    pass

@scenario('../features/code_research.feature', 'Find Similar Code Examples')
def test_find_similar():
    """Test finding similar code"""
    pass

@scenario('../features/code_research.feature', 'Track Project Context')
def test_track_context():
    """Test project context tracking"""
    pass

@scenario('../features/code_research.feature', 'Research with Multiple Sources')
def test_multiple_sources():
    """Test multi-source research"""
    pass

@scenario('../features/code_research.feature', 'Save and Reuse Patterns')
def test_save_patterns():
    """Test pattern saving and reuse"""
    pass

# Fixtures
@pytest.fixture
def test_db():
    """Setup test database using Docker"""
    # Get database URL from environment or use test container
    database_url = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db")
    
    # Initialize test database
    db = DatabaseManager(database_url)
    db.create_database()
    
    yield db
    
    # Cleanup
    db.drop_database()

@pytest.fixture
def assistant(tmp_path, test_db):
    """Initialize code assistant with test configuration"""
    return CodeAssistant(str(tmp_path))

# Given steps
@given("the code assistant is initialized")
def init_assistant(assistant):
    """Ensure assistant is initialized"""
    assert assistant is not None

@given("the database is connected")
def check_db(test_db):
    """Ensure database is connected"""
    assert test_db.is_connected()

@given("I have a React component code")
def react_code(context):
    """Store React code in context"""
    context.code = context.text

@given("I have initialized a new project")
async def init_project(assistant):
    """Initialize test project"""
    context.project = await assistant.init_project(
        name="Test Project",
        language="javascript",
        framework="react"
    )
    assert context.project is not None

@given("I have a code snippet")
def code_snippet(context):
    """Store code snippet in context"""
    context.code_snippet = """
    function TestComponent() {
        return <div>Test</div>;
    }
    """

@given("I have found a useful code pattern")
def useful_pattern(context):
    """Store useful pattern in context"""
    context.pattern = {
        "name": "Test Pattern",
        "code": """
        const withData = WrappedComponent => {
            return function WithDataComponent(props) {
                const [data, setData] = useState(null);
                useEffect(() => {
                    fetchData().then(setData);
                }, []);
                return <WrappedComponent data={data} {...props} />;
            };
        };
        """,
        "description": "HOC for data fetching",
        "tags": ["react", "hoc", "data-fetching"]
    }

# When steps
@when("I search for 'react component patterns'")
async def search_patterns(assistant, context):
    """Perform pattern search"""
    context.results = await assistant.research_topic("react component patterns")
    assert context.results is not None

@when("I analyze the code")
async def analyze_code(assistant, context):
    """Analyze provided code"""
    context.analysis = await assistant.analyze_code(context.code)
    assert context.analysis is not None

@when("I search for similar implementations")
async def search_similar(assistant, context):
    """Search for similar code"""
    context.similar = await assistant.find_similar_code(context.code_snippet)
    assert context.similar is not None

@when("I make changes to project files")
async def make_changes(assistant, context):
    """Simulate file changes"""
    await assistant.log_file_change(
        context.project.id,
        "src/components/Test.js",
        "create",
        "Added test component"
    )

@when("I search across multiple sources")
async def multi_source_search(assistant, context):
    """Perform multi-source search"""
    context.results = await assistant.research_topic(
        "react hooks",
        sources=["github", "stackoverflow"]
    )
    assert context.results is not None

@when("I save the pattern")
async def save_pattern(assistant, context):
    """Save code pattern"""
    context.saved_pattern = await assistant.save_snippet(
        title=context.pattern["name"],
        code=context.pattern["code"],
        language="javascript",
        tags=context.pattern["tags"]
    )
    assert context.saved_pattern is not None

# Then steps
@then("I should receive search results")
def check_results(context):
    """Verify search results"""
    assert len(context.results) > 0

@then("the results should contain code examples")
def check_code_examples(context):
    """Verify code examples in results"""
    assert any(r.code_snippet for r in context.results)

@then("the results should be saved to the database")
async def check_saved_results(test_db, context):
    """Verify results are saved"""
    async with test_db.transaction() as session:
        saved = await session.query(SearchResult).all()
        assert len(saved) > 0

@then("I should receive complexity metrics")
def check_metrics(context):
    """Verify complexity metrics"""
    assert "complexity" in context.analysis
    assert "cognitive" in context.analysis["complexity"]
    assert "cyclomatic" in context.analysis["complexity"]

@then("I should receive pattern suggestions")
def check_suggestions(context):
    """Verify pattern suggestions"""
    assert "patterns" in context.analysis
    assert len(context.analysis["patterns"]) > 0

@then("the analysis should be cached for future reference")
async def check_cached_analysis(test_db, context):
    """Verify analysis is cached"""
    async with test_db.transaction() as session:
        cached = await session.query(CodePattern).filter_by(
            code=context.code
        ).first()
        assert cached is not None

@then("I should receive relevant code examples")
def check_relevant_examples(context):
    """Verify relevant examples"""
    assert len(context.similar) > 0
    assert all(s.relevance_score > 0.5 for s in context.similar)

@then("the examples should be sorted by relevance")
def check_sorting(context):
    """Verify result sorting"""
    scores = [s.relevance_score for s in context.similar]
    assert scores == sorted(scores, reverse=True)

@then("the changes should be tracked in the database")
async def check_tracked_changes(test_db, context):
    """Verify tracked changes"""
    async with test_db.transaction() as session:
        changes = await session.query(FileChange).filter_by(
            project_id=context.project.id
        ).all()
        assert len(changes) > 0

@then("the project context should be updated")
async def check_context_update(assistant, context):
    """Verify context update"""
    project_context = await assistant.get_project_context(context.project.id)
    assert "Test.js" in project_context["recent_changes"][0]["file_path"]

@then("I should be able to retrieve the project history")
async def check_project_history(assistant, context):
    """Verify project history"""
    history = await assistant.get_project_history(context.project.id)
    assert len(history) > 0

@then("I should receive results from GitHub")
def check_github_results(context):
    """Verify GitHub results"""
    assert any(r.source == "github" for r in context.results)

@then("I should receive results from Stack Overflow")
def check_stackoverflow_results(context):
    """Verify Stack Overflow results"""
    assert any(r.source == "stackoverflow" for r in context.results)

@then("the results should be deduplicated")
def check_deduplication(context):
    """Verify result deduplication"""
    urls = [r.url for r in context.results]
    assert len(urls) == len(set(urls))

@then("the results should be ranked by relevance")
def check_ranking(context):
    """Verify result ranking"""
    assert all(hasattr(r, "relevance_score") for r in context.results)
    scores = [r.relevance_score for r in context.results]
    assert scores == sorted(scores, reverse=True)

@then("it should be stored in the database")
async def check_stored_pattern(test_db, context):
    """Verify pattern storage"""
    async with test_db.transaction() as session:
        pattern = await session.query(CodePattern).filter_by(
            name=context.pattern["name"]
        ).first()
        assert pattern is not None

@then("I should be able to retrieve it later")
async def check_pattern_retrieval(assistant, context):
    """Verify pattern retrieval"""
    pattern = await assistant.get_pattern(context.saved_pattern.id)
    assert pattern.name == context.pattern["name"]

@then("similar patterns should be suggested when relevant")
async def check_pattern_suggestions(assistant, context):
    """Verify pattern suggestions"""
    suggestions = await assistant.suggest_patterns(context.code_snippet)
    assert any(s.id == context.saved_pattern.id for s in suggestions)