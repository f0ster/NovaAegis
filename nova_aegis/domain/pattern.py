"""Domain models for code patterns with rich behavior."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import networkx as nx

@dataclass
class Tag:
    """Tag for categorizing patterns."""
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tag):
            return NotImplemented
        return self.name == other.name

@dataclass
class Pattern:
    """Code pattern with associated metadata and behavior."""
    name: str
    template: str
    description: str
    tags: Set[Tag] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Ensure tags are a set."""
        self.tags = set(self.tags)
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the pattern."""
        self.tags.add(tag)
        self._mark_updated()
    
    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from the pattern."""
        self.tags.discard(tag)
        self._mark_updated()
    
    def update_template(self, new_template: str) -> None:
        """Update the pattern template."""
        self.template = new_template
        self._mark_updated()
    
    def update_description(self, new_description: str) -> None:
        """Update the pattern description."""
        self.description = new_description
        self._mark_updated()
    
    def _mark_updated(self) -> None:
        """Mark pattern as updated."""
        self.updated_at = datetime.now()
    
    def matches(self, other: Pattern, similarity_threshold: float = 0.8) -> bool:
        """Check if pattern matches another pattern."""
        from difflib import SequenceMatcher
        
        # Check name similarity
        name_ratio = SequenceMatcher(None, self.name, other.name).ratio()
        if name_ratio > similarity_threshold:
            return True
        
        # Check template similarity
        template_ratio = SequenceMatcher(
            None, self.template, other.template
        ).ratio()
        return template_ratio > similarity_threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "description": self.description,
            "tags": [tag.name for tag in self.tags],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class PatternRelation:
    """Relationship between patterns."""
    source: Pattern
    target: Pattern
    relation_type: str
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None
    
    def strengthen(self, amount: float = 0.1) -> None:
        """Strengthen the relationship."""
        self.weight += amount
    
    def weaken(self, amount: float = 0.1) -> None:
        """Weaken the relationship."""
        self.weight = max(0.0, self.weight - amount)

@dataclass
class PatternUsage:
    """Record of pattern usage."""
    pattern: Pattern
    context: Dict[str, Any]
    used_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert usage record to dictionary."""
        return {
            "id": self.id,
            "pattern_id": self.pattern.id,
            "context": self.context,
            "used_at": self.used_at.isoformat()
        }

class PatternGraph:
    """Graph representation of pattern relationships."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_pattern(self, pattern: Pattern) -> None:
        """Add pattern to graph."""
        self.graph.add_node(
            pattern.id,
            name=pattern.name,
            data=pattern.to_dict()
        )
    
    def add_relation(
        self,
        relation: PatternRelation
    ) -> None:
        """Add relationship to graph."""
        self.graph.add_edge(
            relation.source.id,
            relation.target.id,
            type=relation.relation_type,
            weight=relation.weight
        )
    
    def get_related_patterns(
        self,
        pattern: Pattern,
        relation_type: Optional[str] = None,
        depth: int = 1
    ) -> List[Pattern]:
        """Get patterns related to given pattern."""
        if pattern.id not in self.graph:
            return []
        
        related_ids = set()
        current = {pattern.id}
        
        for _ in range(depth):
            next_level = set()
            for node in current:
                for _, neighbor in self.graph.edges(node):
                    if relation_type is None or self.graph.edges[node, neighbor]['type'] == relation_type:
                        next_level.add(neighbor)
            current = next_level
            related_ids.update(current)
        
        return [
            Pattern(**self.graph.nodes[pid]['data'])
            for pid in related_ids
        ]
    
    def get_pattern_similarity(
        self,
        pattern1: Pattern,
        pattern2: Pattern
    ) -> float:
        """Get similarity score between patterns."""
        if not (pattern1.id in self.graph and pattern2.id in self.graph):
            return 0.0
            
        # Use network metrics for similarity
        return nx.simrank_similarity(
            self.graph,
            pattern1.id,
            pattern2.id
        )