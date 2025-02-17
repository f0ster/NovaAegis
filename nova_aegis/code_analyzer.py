"""
Code Analyzer for deep code understanding and analysis.
Provides insights into code structure, complexity, and behavior.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import ast
import re
from functools import lru_cache
import structlog

logger = structlog.get_logger()

@dataclass
class CodeInsight:
    """Detailed insight about code structure or behavior."""
    category: str  # e.g., "complexity", "architecture", "performance"
    description: str
    severity: str  # "info", "suggestion", "warning", "critical"
    line_numbers: Optional[List[int]] = None
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeAnalysis:
    """Complete analysis of a code segment."""
    language: str
    metrics: Dict[str, Any]
    insights: List[CodeInsight]
    dependencies: List[str]
    structure: Dict[str, Any]
    complexity_score: float

class CodeAnalyzer:
    """Analyzes code structure, quality, and behavior."""
    
    def __init__(self):
        self.logger = logger.bind(component="code_analyzer")
    
    def analyze_code(self, code: str, language: str) -> CodeAnalysis:
        """
        Perform comprehensive code analysis.
        
        This is the main entry point for code analysis, providing:
        1. Code structure understanding
        2. Quality metrics
        3. Behavioral insights
        4. Dependency analysis
        """
        self.logger.info("analyzing_code", language=language)
        
        try:
            metrics = self._calculate_metrics(code, language)
            insights = self._generate_insights(code, language, metrics)
            deps = self._extract_dependencies(code, language)
            structure = self._analyze_structure(code, language)
            complexity = self._calculate_complexity_score(metrics)
            
            return CodeAnalysis(
                language=language,
                metrics=metrics,
                insights=insights,
                dependencies=deps,
                structure=structure,
                complexity_score=complexity
            )
        except Exception as e:
            self.logger.error("analysis_failed", error=str(e))
            raise
    
    @lru_cache(maxsize=100)
    def _calculate_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        metrics = {
            "size": {
                "lines": len(code.splitlines()),
                "characters": len(code),
                "non_empty_lines": len([l for l in code.splitlines() if l.strip()]),
            },
            "complexity": {
                "cyclomatic": self._cyclomatic_complexity(code, language),
                "cognitive": self._cognitive_complexity(code, language),
                "halstead": self._halstead_metrics(code, language)
            },
            "maintainability": {
                "comment_ratio": self._comment_ratio(code, language),
                "function_length": self._average_function_length(code, language),
                "nesting_depth": self._max_nesting_depth(code, language)
            }
        }
        
        if language == "python":
            metrics.update(self._python_specific_metrics(code))
        elif language in ["javascript", "typescript"]:
            metrics.update(self._js_specific_metrics(code))
            
        return metrics
    
    def _generate_insights(
        self,
        code: str,
        language: str,
        metrics: Dict[str, Any]
    ) -> List[CodeInsight]:
        """Generate actionable code insights."""
        insights = []
        
        # Complexity insights
        if metrics["complexity"]["cyclomatic"] > 10:
            insights.append(CodeInsight(
                category="complexity",
                description="High cyclomatic complexity suggests code may be difficult to test",
                severity="warning"
            ))
            
        if metrics["maintainability"]["nesting_depth"] > 4:
            insights.append(CodeInsight(
                category="maintainability",
                description="Deep nesting makes code hard to understand",
                severity="warning"
            ))
            
        # Language-specific insights
        if language == "python":
            insights.extend(self._python_insights(code, metrics))
        elif language in ["javascript", "typescript"]:
            insights.extend(self._js_insights(code, metrics))
            
        return insights
    
    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """Extract code dependencies."""
        deps = set()
        
        if language == "python":
            # Match imports
            import_patterns = [
                r"^import\s+(\w+)",
                r"^from\s+(\w+)\s+import",
            ]
            for pattern in import_patterns:
                deps.update(re.findall(pattern, code, re.MULTILINE))
                
        elif language in ["javascript", "typescript"]:
            # Match requires and imports
            js_patterns = [
                r"require\(['\"]([^'\"]+)['\"]\)",
                r"from\s+['\"]([^'\"]+)['\"]",
            ]
            for pattern in js_patterns:
                deps.update(re.findall(pattern, code))
                
        return sorted(deps)
    
    def _analyze_structure(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code structure and organization."""
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "exports": []
        }
        
        if language == "python":
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        structure["functions"].append({
                            "name": node.name,
                            "args": len(node.args.args),
                            "line": node.lineno
                        })
                    elif isinstance(node, ast.ClassDef):
                        structure["classes"].append({
                            "name": node.name,
                            "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                            "line": node.lineno
                        })
            except SyntaxError:
                self.logger.warning("python_parse_failed")
                
        elif language in ["javascript", "typescript"]:
            # Extract function declarations and arrow functions
            fn_patterns = [
                r"function\s+(\w+)\s*\([^)]*\)",
                r"const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
            ]
            for pattern in fn_patterns:
                matches = re.finditer(pattern, code)
                structure["functions"].extend({
                    "name": m.group(1),
                    "line": code[:m.start()].count('\n') + 1
                } for m in matches)
                
            # Extract classes
            class_pattern = r"class\s+(\w+)"
            matches = re.finditer(class_pattern, code)
            structure["classes"].extend({
                "name": m.group(1),
                "line": code[:m.start()].count('\n') + 1
            } for m in matches)
            
        return structure
    
    def _cyclomatic_complexity(self, code: str, language: str) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_patterns = {
            "python": [
                r"\bif\b", r"\belif\b", r"\bfor\b", r"\bwhile\b",
                r"\band\b", r"\bor\b", r"\bexcept\b", r"\bwith\b"
            ],
            "javascript": [
                r"\bif\b", r"\belse\s+if\b", r"\bfor\b", r"\bwhile\b",
                r"\bcase\b", r"\bcatch\b", r"\b\&\&\b", r"\b\|\|\b"
            ]
        }
        
        patterns = decision_patterns.get(language, [])
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
            
        return complexity
    
    def _cognitive_complexity(self, code: str, language: str) -> int:
        """Calculate cognitive complexity."""
        complexity = 0
        nesting = 0
        
        lines = code.splitlines()
        for line in lines:
            line = line.strip()
            
            # Increase nesting level
            if any(line.endswith(c) for c in (':', '{', '{')):
                nesting += 1
                
            # Add complexity for control structures
            if any(kw in line for kw in ['if', 'for', 'while', 'switch']):
                complexity += (1 + nesting)  # Higher weight for nested structures
                
            # Decrease nesting level
            if line.startswith(('}', 'end', 'endif')):
                nesting = max(0, nesting - 1)
                
        return complexity
    
    def _halstead_metrics(self, code: str, language: str) -> Dict[str, float]:
        """Calculate Halstead complexity metrics."""
        # Count operators and operands
        operators = set()
        operands = set()
        
        if language == "python":
            # Simple operator extraction for demonstration
            ops = re.findall(r'[\+\-\*/=<>!&\|]', code)
            operators.update(ops)
            
            # Extract variable names and literals
            operands.update(re.findall(r'\b[a-zA-Z_]\w*\b', code))
            
        elif language in ["javascript", "typescript"]:
            # JavaScript operators
            ops = re.findall(r'[\+\-\*/=<>!&\|]|\b(typeof|instanceof)\b', code)
            operators.update(ops)
            
            # Extract variable names and literals
            operands.update(re.findall(r'\b[a-zA-Z_$]\w*\b', code))
        
        n1 = len(operators)  # Unique operators
        n2 = len(operands)   # Unique operands
        N1 = len(re.findall(r'[\+\-\*/=<>!&\|]', code))  # Total operators
        N2 = len(re.findall(r'\b[a-zA-Z_$]\w*\b', code)) # Total operands
        
        # Calculate metrics
        program_length = N1 + N2
        vocabulary = n1 + n2
        volume = program_length * (vocabulary.bit_length() if vocabulary > 0 else 1)
        difficulty = (n1 * N2) / (2 * n2) if n2 > 0 else 0
        
        return {
            "program_length": program_length,
            "vocabulary": vocabulary,
            "volume": volume,
            "difficulty": difficulty,
            "effort": volume * difficulty
        }
    
    def _calculate_complexity_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall complexity score (0-1)."""
        weights = {
            "cyclomatic": 0.3,
            "cognitive": 0.3,
            "halstead": 0.2,
            "maintainability": 0.2
        }
        
        # Normalize metrics to 0-1 scale
        cyclomatic_norm = min(1.0, metrics["complexity"]["cyclomatic"] / 20)
        cognitive_norm = min(1.0, metrics["complexity"]["cognitive"] / 30)
        halstead_norm = min(1.0, metrics["complexity"]["halstead"]["difficulty"] / 100)
        maint_norm = min(1.0, metrics["maintainability"]["nesting_depth"] / 10)
        
        # Calculate weighted score
        score = sum([
            weights["cyclomatic"] * cyclomatic_norm,
            weights["cognitive"] * cognitive_norm,
            weights["halstead"] * halstead_norm,
            weights["maintainability"] * maint_norm
        ])
        
        return score