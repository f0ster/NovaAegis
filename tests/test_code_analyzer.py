"""Tests for code analysis capabilities."""
import pytest
from nova_aegis.code_analyzer import CodeAnalyzer, CodeInsight

# Test code samples
PYTHON_CODE = '''
def calculate_fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

class DataProcessor:
    def __init__(self, data: list):
        self.data = data
        
    def process(self) -> list:
        """Process data with nested loops."""
        result = []
        for item in self.data:
            if isinstance(item, list):
                for subitem in item:
                    if subitem > 0:
                        result.append(subitem * 2)
        return result
'''

JS_CODE = '''
const memoize = (fn) => {
    const cache = new Map();
    return (...args) => {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
            return cache.get(key);
        }
        const result = fn(...args);
        cache.set(key, result);
        return result;
    };
};

class DataService {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.cache = new Map();
    }
    
    async fetchData(id) {
        if (this.cache.has(id)) {
            return this.cache.get(id);
        }
        try {
            const response = await fetch(`${this.apiUrl}/${id}`);
            if (!response.ok) {
                throw new Error('Network error');
            }
            const data = await response.json();
            this.cache.set(id, data);
            return data;
        } catch (error) {
            console.error('Failed to fetch:', error);
            throw error;
        }
    }
}
'''

@pytest.fixture
def analyzer():
    """Create code analyzer instance."""
    return CodeAnalyzer()

def test_python_analysis(analyzer):
    """Test Python code analysis."""
    analysis = analyzer.analyze_code(PYTHON_CODE, "python")
    
    # Verify basic metrics
    assert analysis.language == "python"
    assert analysis.metrics["size"]["lines"] > 0
    assert analysis.metrics["complexity"]["cyclomatic"] > 1
    
    # Check structure detection
    assert len(analysis.structure["functions"]) == 1
    assert len(analysis.structure["classes"]) == 1
    assert analysis.structure["functions"][0]["name"] == "calculate_fibonacci"
    assert analysis.structure["classes"][0]["name"] == "DataProcessor"
    
    # Verify complexity insights
    complexity_insights = [
        i for i in analysis.insights 
        if i.category == "complexity"
    ]
    assert len(complexity_insights) > 0
    
    # Check nesting analysis
    assert analysis.metrics["maintainability"]["nesting_depth"] >= 3

def test_javascript_analysis(analyzer):
    """Test JavaScript code analysis."""
    analysis = analyzer.analyze_code(JS_CODE, "javascript")
    
    # Verify basic metrics
    assert analysis.language == "javascript"
    assert analysis.metrics["size"]["lines"] > 0
    
    # Check structure detection
    assert len(analysis.structure["functions"]) >= 1
    assert len(analysis.structure["classes"]) == 1
    assert any(f["name"] == "memoize" for f in analysis.structure["functions"])
    assert analysis.structure["classes"][0]["name"] == "DataService"
    
    # Verify async/await detection
    assert any(
        "async" in i.description 
        for i in analysis.insights
    )
    
    # Check error handling insights
    assert any(
        i.category == "error_handling" 
        for i in analysis.insights
    )

@pytest.mark.parametrize("code,language,expected_deps", [
    (
        "import numpy as np\nfrom pandas import DataFrame",
        "python",
        ["numpy", "pandas"]
    ),
    (
        "const React = require('react');\nimport axios from 'axios';",
        "javascript",
        ["react", "axios"]
    )
])
def test_dependency_extraction(analyzer, code, language, expected_deps):
    """Test dependency extraction across languages."""
    analysis = analyzer.analyze_code(code, language)
    assert all(dep in analysis.dependencies for dep in expected_deps)

@pytest.mark.parametrize("code,language,min_complexity", [
    # Simple code
    ("def add(a, b): return a + b", "python", 1),
    # Complex code with loops and conditions
    (PYTHON_CODE, "python", 5),
    # JavaScript with error handling
    (JS_CODE, "javascript", 4)
])
def test_complexity_scoring(analyzer, code, language, min_complexity):
    """Test complexity scoring across different code samples."""
    analysis = analyzer.analyze_code(code, language)
    assert analysis.complexity_score > 0
    assert analysis.metrics["complexity"]["cyclomatic"] >= min_complexity

def test_insight_generation(analyzer):
    """Test generation of code insights."""
    # Code with potential issues
    code = '''
def process_data(items):
    results = []
    for item in items:
        if item.type == 'A':
            if item.value > 0:
                if item.status == 'active':
                    for subitem in item.data:
                        if subitem > 100:
                            results.append(subitem)
    return results
'''
    analysis = analyzer.analyze_code(code, "python")
    
    # Check for specific insights
    insights_by_category = {
        i.category: i for i in analysis.insights
    }
    
    # Should detect deep nesting
    assert "maintainability" in insights_by_category
    nesting_insight = insights_by_category["maintainability"]
    assert "nesting" in nesting_insight.description.lower()
    assert nesting_insight.severity in ["warning", "critical"]
    
    # Should detect complexity issues
    assert "complexity" in insights_by_category
    complexity_insight = insights_by_category["complexity"]
    assert complexity_insight.severity in ["warning", "critical"]

def test_halstead_metrics(analyzer):
    """Test Halstead complexity metrics calculation."""
    code = '''
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
'''
    analysis = analyzer.analyze_code(code, "python")
    halstead = analysis.metrics["complexity"]["halstead"]
    
    # Verify Halstead metrics
    assert "program_length" in halstead
    assert "vocabulary" in halstead
    assert "volume" in halstead
    assert "difficulty" in halstead
    assert "effort" in halstead
    
    # Check reasonable values
    assert halstead["program_length"] > 0
    assert halstead["vocabulary"] > 0
    assert halstead["volume"] > 0
    assert halstead["difficulty"] > 0

def test_cognitive_complexity(analyzer):
    """Test cognitive complexity calculation."""
    # Code with nested control structures
    code = '''
def validate_user_input(data):
    if data.get('username'):
        if len(data['username']) >= 3:
            if data.get('email'):
                if '@' in data['email']:
                    if data.get('password'):
                        if len(data['password']) >= 8:
                            return True
    return False
'''
    analysis = analyzer.analyze_code(code, "python")
    
    # Cognitive complexity should be high due to nesting
    assert analysis.metrics["complexity"]["cognitive"] > 5
    
    # Should generate maintainability insight
    assert any(
        i.category == "maintainability" and i.severity == "critical"
        for i in analysis.insights
    )

def test_analysis_error_handling(analyzer):
    """Test analyzer error handling with invalid code."""
    # Invalid Python syntax
    with pytest.raises(Exception):
        analyzer.analyze_code("def invalid syntax:", "python")
    
    # Invalid JavaScript syntax
    with pytest.raises(Exception):
        analyzer.analyze_code("const x =", "javascript")