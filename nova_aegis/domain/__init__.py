"""
Domain models for NovaAegis.
"""
from .knowledge_models import (
    CodePattern,
    PatternRelation,
    PatternUsage,
    Tag
)
from .project_models import (
    Project,
    CodeSnippet,
    Dependency,
    FileChange,
    ProjectContext
)
from .research_models import (
    SearchHistory,
    ResearchResult,
    ResultPattern
)

__all__ = [
    # Knowledge models
    'CodePattern',
    'PatternRelation',
    'PatternUsage',
    'Tag',
    
    # Project models
    'Project',
    'CodeSnippet',
    'Dependency',
    'FileChange',
    'ProjectContext',
    
    # Research models
    'SearchHistory',
    'ResearchResult',
    'ResultPattern'
]