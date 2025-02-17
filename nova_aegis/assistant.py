from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
import logging
from pathlib import Path

from .database import DatabaseManager
from .browser_pilot import BrowserPilot, SearchResult
from .models import (
    Project, CodeSnippet, SearchHistory, 
    ResearchResult, CodePattern, ProjectContext
)

class CodeAssistant:
    """Intelligent code assistant with real-time research and analysis capabilities"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.db = DatabaseManager()
        self._setup_logging()
        
    def _setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    async def init_project(self, name: str, language: str = None, framework: str = None) -> Project:
        """Initialize or load existing project"""
        async with self.db.transaction() as session:
            # Check for existing project
            project = await session.query(Project).filter(
                Project.path == str(self.project_path)
            ).first()
            
            if not project:
                # Create new project
                project = Project(
                    name=name,
                    path=str(self.project_path),
                    language=language,
                    framework=framework,
                    metadata={
                        'created_at': datetime.now().isoformat(),
                        'files': list(self.project_path.rglob('*')),
                    }
                )
                session.add(project)
                await session.commit()
                
            return project
            
    async def analyze_codebase(self, project_id: int) -> ProjectContext:
        """Analyze project structure and patterns"""
        async with self.db.transaction() as session:
            # Scan project files
            files = list(self.project_path.rglob('*'))
            file_types = {}
            
            for file in files:
                if file.is_file():
                    ext = file.suffix
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            # Analyze architecture and patterns
            context = ProjectContext(
                project_id=project_id,
                architecture_summary=self._generate_arch_summary(files),
                tech_stack=self._detect_tech_stack(files),
                key_patterns=self._identify_patterns(files),
                development_notes="Initial project analysis"
            )
            
            session.add(context)
            await session.commit()
            return context
            
    def _generate_arch_summary(self, files: List[Path]) -> str:
        """Generate architecture summary from project structure"""
        structure = {}
        
        for file in files:
            if file.is_file():
                parts = file.relative_to(self.project_path).parts
                current = structure
                
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = None
                
        return self._structure_to_summary(structure)
        
    def _structure_to_summary(self, structure: Dict, level: int = 0) -> str:
        """Convert directory structure to readable summary"""
        summary = []
        indent = "  " * level
        
        for key, value in structure.items():
            if value is None:
                summary.append(f"{indent}- {key}")
            else:
                summary.append(f"{indent}+ {key}/")
                summary.append(self._structure_to_summary(value, level + 1))
                
        return "\n".join(summary)
        
    def _detect_tech_stack(self, files: List[Path]) -> Dict:
        """Detect technology stack from project files"""
        tech_stack = {
            'languages': set(),
            'frameworks': set(),
            'tools': set(),
            'dependencies': set()
        }
        
        # Check package files
        package_files = {
            'package.json': self._analyze_npm_package,
            'requirements.txt': self._analyze_python_reqs,
            'Cargo.toml': self._analyze_rust_cargo,
            'go.mod': self._analyze_go_mod
        }
        
        for file in files:
            if file.name in package_files:
                package_files[file.name](file, tech_stack)
                
        return {k: list(v) for k, v in tech_stack.items()}
        
    def _identify_patterns(self, files: List[Path]) -> Dict:
        """Identify code patterns in project"""
        patterns = {
            'architectural': [],
            'design': [],
            'implementation': []
        }
        
        # Analyze files for patterns
        for file in files:
            if file.is_file():
                self._analyze_file_patterns(file, patterns)
                
        return patterns
        
    async def research_topic(self, query: str, context: Optional[Dict] = None) -> List[SearchResult]:
        """Perform comprehensive code research"""
        # First check database for existing research
        async with self.db.transaction() as session:
            existing = await session.query(ResearchResult).filter(
                ResearchResult.content_summary.ilike(f"%{query}%")
            ).all()
            
            if existing:
                self.logger.info(f"Found {len(existing)} existing research results")
                return [SearchResult(
                    url=r.url,
                    title=r.title,
                    code_snippet=r.code_blocks[0] if r.code_blocks else None,
                    metadata={'source': 'cache'},
                    source='database',
                    timestamp=r.visited_at
                ) for r in existing]
        
        # Perform new research with browser
        with BrowserPilot() as pilot:
            results = pilot.research(query)
            
            # Store results
            async with self.db.transaction() as session:
                for result in results:
                    research = ResearchResult(
                        url=result.url,
                        title=result.title,
                        content_summary=result.code_snippet,
                        code_blocks=[result.code_snippet] if result.code_snippet else [],
                        metadata=result.metadata
                    )
                    session.add(research)
                
                await session.commit()
            
            return results
            
    async def analyze_code(self, code: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze code snippet with context"""
        analysis = {
            'patterns': [],
            'complexity': self._analyze_complexity(code),
            'dependencies': self._extract_dependencies(code),
            'suggestions': []
        }
        
        # Find similar patterns
        async with self.db.transaction() as session:
            patterns = await session.query(CodePattern).all()
            
            for pattern in patterns:
                if self._pattern_matches(code, pattern):
                    analysis['patterns'].append({
                        'name': pattern.name,
                        'type': pattern.pattern_type,
                        'description': pattern.description
                    })
        
        # Generate suggestions
        analysis['suggestions'] = self._generate_suggestions(
            code, analysis['patterns'], context
        )
        
        return analysis
        
    def _analyze_complexity(self, code: str) -> Dict[str, int]:
        """Analyze code complexity metrics"""
        return {
            'cognitive': self._cognitive_complexity(code),
            'cyclomatic': self._cyclomatic_complexity(code),
            'lines': len(code.splitlines())
        }
        
    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract code dependencies"""
        # Implementation would depend on language
        pass
        
    def _pattern_matches(self, code: str, pattern: CodePattern) -> bool:
        """Check if code matches a pattern"""
        # Implementation would use pattern matching
        pass
        
    def _generate_suggestions(
        self, 
        code: str, 
        patterns: List[Dict], 
        context: Optional[Dict]
    ) -> List[str]:
        """Generate code improvement suggestions"""
        suggestions = []
        
        # Add suggestions based on patterns and context
        if context and context.get('performance_critical'):
            suggestions.extend(self._performance_suggestions(code))
            
        if patterns:
            suggestions.extend(self._pattern_based_suggestions(code, patterns))
            
        return suggestions
        
    async def save_snippet(
        self, 
        title: str,
        code: str,
        language: str,
        tags: List[str] = None
    ) -> CodeSnippet:
        """Save reusable code snippet"""
        async with self.db.transaction() as session:
            snippet = CodeSnippet(
                title=title,
                code=code,
                language=language,
                tags=tags or []
            )
            session.add(snippet)
            await session.commit()
            return snippet
            
    async def find_similar_code(self, code: str, language: Optional[str] = None) -> List[CodeSnippet]:
        """Find similar code snippets"""
        async with self.db.transaction() as session:
            query = session.query(CodeSnippet)
            
            if language:
                query = query.filter(CodeSnippet.language == language)
                
            snippets = await query.all()
            
            # Sort by similarity
            scored_snippets = [
                (snippet, self._code_similarity(code, snippet.code))
                for snippet in snippets
            ]
            
            return [
                snippet for snippet, score in sorted(
                    scored_snippets,
                    key=lambda x: x[1],
                    reverse=True
                )
                if score > 0.7  # Similarity threshold
            ]
            
    def _code_similarity(self, code1: str, code2: str) -> float:
        """Calculate code similarity score"""
        # Implementation would use code similarity algorithms
        pass