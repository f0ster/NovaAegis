import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
import os

from nova_aegis.assistant import CodeAssistant
from nova_aegis.models import Project, CodeSnippet, SearchResult
from nova_aegis.database import DatabaseManager

# Test fixtures
@pytest.fixture
def test_project_path(tmp_path):
    """Create a temporary project directory"""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    return str(project_dir)

@pytest.fixture
async def test_db():
    """Setup test database"""
    # Use in-memory SQLite for testing
    test_url = "sqlite+aiosqlite:///:memory:"
    
    # Override database URL
    with patch.dict(os.environ, {"DATABASE_URL": test_url}):
        db = DatabaseManager()
        await db.create_tables()
        yield db
        await db.drop_tables()

@pytest.fixture
def mock_browser():
    """Mock browser automation"""
    with patch("nova_aegis.browser_pilot.BrowserPilot") as mock:
        yield mock

@pytest.mark.asyncio
async def test_init_project(test_project_path, test_db):
    """Test project initialization"""
    assistant = CodeAssistant(test_project_path)
    
    project = await assistant.init_project(
        name="Test Project",
        language="javascript",
        framework="react"
    )
    
    assert project.name == "Test Project"
    assert project.path == test_project_path
    assert project.language == "javascript"
    assert project.framework == "react"

@pytest.mark.asyncio
async def test_analyze_codebase(test_project_path, test_db):
    """Test codebase analysis"""
    # Create test files
    project_dir = Path(test_project_path)
    (project_dir / "src").mkdir()
    (project_dir / "src" / "App.js").write_text("""
        import React from 'react';
        
        function App() {
            return <div>Hello World</div>;
        }
        
        export default App;
    """)
    
    assistant = CodeAssistant(test_project_path)
    project = await assistant.init_project("Test Project")
    
    context = await assistant.analyze_codebase(project.id)
    
    assert "App.js" in context.architecture_summary
    assert "react" in context.tech_stack["frameworks"]

@pytest.mark.asyncio
async def test_research_topic(test_project_path, test_db, mock_browser):
    """Test code research functionality"""
    # Mock browser search results
    mock_results = [
        SearchResult(
            url="https://example.com/result1",
            title="Test Result 1",
            code_snippet="const Component = () => <div>Test</div>",
            metadata={"source": "test"},
            source="github"
        )
    ]
    mock_browser.return_value.__aenter__.return_value.research.return_value = mock_results
    
    assistant = CodeAssistant(test_project_path)
    project = await assistant.init_project("Test Project")
    
    results = await assistant.research_topic(
        "react component pattern",
        {"project_id": project.id}
    )
    
    assert len(results) == 1
    assert results[0].title == "Test Result 1"
    assert "react component pattern" in results[0].code_snippet

@pytest.mark.asyncio
async def test_analyze_code(test_project_path, test_db):
    """Test code analysis functionality"""
    test_code = """
    import React, { useState } from 'react';
    
    function TestComponent() {
        const [count, setCount] = useState(0);
        
        return (
            <div>
                <p>Count: {count}</p>
                <button onClick={() => setCount(count + 1)}>
                    Increment
                </button>
            </div>
        );
    }
    """
    
    assistant = CodeAssistant(test_project_path)
    project = await assistant.init_project("Test Project")
    
    analysis = await assistant.analyze_code(
        test_code,
        {"project_id": project.id}
    )
    
    assert "patterns" in analysis
    assert "complexity" in analysis
    assert "suggestions" in analysis
    assert analysis["complexity"]["lines"] > 0

@pytest.mark.asyncio
async def test_save_snippet(test_project_path, test_db):
    """Test code snippet storage"""
    assistant = CodeAssistant(test_project_path)
    project = await assistant.init_project("Test Project")
    
    snippet = await assistant.save_snippet(
        title="Test Component",
        code="const Test = () => <div>Test</div>;",
        language="javascript",
        tags=["react", "component"]
    )
    
    assert snippet.title == "Test Component"
    assert "Test = () =>" in snippet.code
    assert "react" in [tag.name for tag in snippet.tags]

@pytest.mark.asyncio
async def test_find_similar_code(test_project_path, test_db):
    """Test similar code search"""
    assistant = CodeAssistant(test_project_path)
    project = await assistant.init_project("Test Project")
    
    # Save test snippets
    await assistant.save_snippet(
        title="Button Component",
        code="const Button = ({ onClick, children }) => <button onClick={onClick}>{children}</button>;",
        language="javascript",
        tags=["react", "component"]
    )
    
    similar = await assistant.find_similar_code(
        "const CustomButton = props => <button {...props} />",
        language="javascript"
    )
    
    assert len(similar) > 0
    assert "Button" in similar[0].title

@pytest.mark.asyncio
async def test_project_context_tracking(test_project_path, test_db):
    """Test project context maintenance"""
    assistant = CodeAssistant(test_project_path)
    project = await assistant.init_project("Test Project")
    
    # Create test file changes
    test_files = [
        ("src/components/Header.js", "react component"),
        ("src/utils/api.js", "utility functions"),
        ("src/styles/main.css", "styles")
    ]
    
    for file_path, desc in test_files:
        await assistant.log_file_change(
            project.id,
            file_path,
            "create",
            desc
        )
    
    context = await assistant.get_project_context(project.id)
    
    assert len(context["recent_changes"]) == 3
    assert "Header.js" in context["recent_changes"][0]["file_path"]
    assert "components" in context["architecture_summary"]

def test_code_complexity_analysis(test_project_path):
    """Test code complexity metrics"""
    assistant = CodeAssistant(test_project_path)
    
    test_code = """
    function ComplexComponent() {
        const [state1, setState1] = useState();
        const [state2, setState2] = useState();
        
        useEffect(() => {
            if (state1) {
                if (state2) {
                    // Nested conditions
                    doSomething();
                }
            }
        }, [state1, state2]);
        
        return <div>{state1 && state2 && <Child />}</div>;
    }
    """
    
    metrics = assistant._analyze_complexity(test_code)
    
    assert metrics["cognitive"] > 1  # Due to nested conditions
    assert metrics["cyclomatic"] > 1  # Due to branching
    assert metrics["lines"] > 10

def test_pattern_matching(test_project_path):
    """Test code pattern detection"""
    assistant = CodeAssistant(test_project_path)
    
    test_code = """
    const withData = WrappedComponent => {
        return function WithDataComponent(props) {
            const [data, setData] = useState(null);
            
            useEffect(() => {
                fetchData().then(setData);
            }, []);
            
            return <WrappedComponent data={data} {...props} />;
        };
    };
    """
    
    patterns = assistant._identify_patterns([test_code])
    
    assert any(p["name"] == "HOC" for p in patterns["architectural"])
    assert any(p["name"] == "Data Fetching" for p in patterns["implementation"])