"""
Knowledge store for managing patterns and insights.
"""
from typing import List, Dict, Set, Optional, Any
import asyncio
from datetime import datetime
import networkx as nx
from sqlalchemy import select, and_, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
import json
from functools import lru_cache
import structlog

from .domain.knowledge_models import (
    CodePattern,
    PatternRelation,
    PatternUsage,
    Tag
)
from .database import DatabaseManager

logger = structlog.get_logger()

class KnowledgeStore:
    """Knowledge store with caching and batch operations."""
    
    def __init__(self, session_factory):
        """Initialize with session factory."""
        self.session_factory = session_factory
        self.graph = nx.DiGraph()
        self._pattern_cache = {}
        self._relation_cache = set()
        self._pending_operations = []
        self.batch_size = 100
        
    async def initialize(self):
        """Load existing patterns and relations into memory."""
        async with self.session_factory() as session:
            # Load patterns
            patterns = await session.execute(select(CodePattern))
            for pattern in patterns.scalars():
                self._pattern_cache[pattern.id] = pattern
                pattern_dict = await pattern.to_dict()
                self.graph.add_node(
                    pattern.id,
                    type="pattern",
                    name=pattern.name,
                    data=pattern_dict
                )
            
            # Load relations
            relations = await session.execute(select(PatternRelation))
            for relation in relations.scalars():
                self._relation_cache.add((relation.source_id, relation.target_id))
                self.graph.add_edge(
                    relation.source_id,
                    relation.target_id,
                    type=relation.relation_type,
                    weight=relation.weight
                )
                
            logger.info(
                "Knowledge store initialized",
                patterns=len(self._pattern_cache),
                relations=len(self._relation_cache)
            )

    async def get_patterns(self, focus_area: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get patterns filtered by focus area."""
        patterns = []
        for pattern in self._pattern_cache.values():
            pattern_dict = await pattern.to_dict()
            if focus_area is None or pattern_dict.get("metadata", {}).get("focus_area") == focus_area:
                patterns.append(pattern_dict)
        return patterns

    async def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns."""
        return await self.get_patterns()

    async def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get all pattern connections."""
        connections = []
        for source_id, target_id in self._relation_cache:
            edge = self.graph.edges[source_id, target_id]
            connections.append({
                "from": source_id,
                "to": target_id,
                "type": edge["type"],
                "weight": edge["weight"]
            })
        return connections

    async def get_all_focus_areas(self) -> List[str]:
        """Get all unique focus areas."""
        focus_areas = set()
        for pattern in self._pattern_cache.values():
            pattern_dict = await pattern.to_dict()
            if focus_area := pattern_dict.get("metadata", {}).get("focus_area"):
                focus_areas.add(focus_area)
        return list(focus_areas)

    async def get_focus_areas(self, actor_id: str) -> List[str]:
        """Get focus areas for a specific actor."""
        # For now, return all focus areas since we don't track per-actor areas
        return await self.get_all_focus_areas()

    async def get_confidence_metrics(self) -> Dict[str, float]:
        """Get confidence metrics for patterns and relationships."""
        pattern_confidence = sum(
            p.get("metadata", {}).get("confidence", 0.0)
            for p in await self.get_all_patterns()
        ) / max(len(self._pattern_cache), 1)

        relation_confidence = sum(
            edge["weight"]
            for _, _, edge in self.graph.edges(data=True)
        ) / max(len(self._relation_cache), 1)

        return {
            "pattern_confidence": pattern_confidence,
            "relation_confidence": relation_confidence,
            "overall_confidence": (pattern_confidence + relation_confidence) / 2
        }

    async def integrate_finding(self, finding: Dict[str, Any]):
        """Integrate a new finding into the knowledge store."""
        async with self.session_factory() as session:
            if finding["type"] == "pattern":
                await self.add_pattern(
                    name=finding["content"]["name"],
                    code_template=finding["content"]["template"],
                    description=finding["content"].get("description", ""),
                    tags=finding["content"].get("tags", []),
                    pattern_data={
                        **finding["content"].get("metadata", {}),
                        "confidence": finding["confidence"],
                        "focus_area": finding.get("focus_area"),
                        "timestamp": finding["timestamp"].isoformat()
                    },
                    session=session
                )
            elif finding["type"] == "connection":
                await self.add_relation(
                    source_id=finding["content"]["from"],
                    target_id=finding["content"]["to"],
                    relation_type=finding["content"]["type"],
                    weight=finding["confidence"],
                    session=session
                )

    async def index_finding(self, finding: Dict[str, Any]):
        """Index a finding for future reference."""
        async with self.session_factory() as session:
            # Store as pattern with special metadata
            await self.add_pattern(
                name=f"Finding: {finding['type']}",
                code_template="",  # No code template for general findings
                description=str(finding["content"]),
                tags=[finding["type"]],
                pattern_data={
                    "type": "finding",
                    "finding_type": finding["type"],
                    "confidence": finding["confidence"],
                    "context": finding["context"],
                    "timestamp": finding["timestamp"].isoformat()
                },
                session=session
            )

    async def integrate_understanding(self, knowledge_state: Dict[str, Any], context: Dict[str, Any]):
        """Integrate actor's understanding into knowledge store."""
        async with self.session_factory() as session:
            # Add patterns from knowledge state
            for pattern in knowledge_state.get("patterns", []):
                await self.add_pattern(
                    name=pattern["name"],
                    code_template=pattern["template"],
                    description=pattern.get("description", ""),
                    tags=pattern.get("tags", []),
                    pattern_data={
                        **pattern.get("metadata", {}),
                        "context": context,
                        "timestamp": datetime.now().isoformat()
                    },
                    session=session
                )

            # Add relationships
            for rel in knowledge_state.get("relationships", []):
                await self.add_relation(
                    source_id=rel["from"],
                    target_id=rel["to"],
                    relation_type=rel["type"],
                    weight=rel.get("weight", 1.0),
                    session=session
                )

    async def get_pattern(self, pattern_id: int) -> Optional[Dict[str, Any]]:
        """Get pattern by ID with caching."""
        pattern = self._pattern_cache.get(pattern_id)
        return await pattern.to_dict() if pattern else None
    
    async def add_pattern(
        self,
        name: str,
        code_template: str,
        description: str,
        tags: List[str],
        pattern_data: Optional[Dict] = None,
        session: Optional[AsyncSession] = None
    ) -> CodePattern:
        """Add new pattern with efficient tag handling."""
        async with self.session_factory() if session is None else session:
            # Check cache first
            existing = await self._find_similar_pattern(name, code_template, session)
            if existing:
                return existing
            
            # Prepare pattern
            pattern = CodePattern(
                name=name,
                description=description,
                language=pattern_data.get("language"),
                framework=pattern_data.get("framework"),
                template=code_template,
                pattern_metadata=pattern_data,
                created_at=datetime.now()
            )
            
            # Batch tag creation/lookup
            tag_ids = await self._get_or_create_tags(tags, session)
            pattern.tags = tag_ids
            
            # Add to session
            session.add(pattern)
            await session.flush()
            
            # Update cache
            self._pattern_cache[pattern.id] = pattern
            pattern_dict = await pattern.to_dict()
            self.graph.add_node(
                pattern.id,
                type="pattern",
                name=name,
                data=pattern_dict
            )
            
            return pattern
    
    async def _find_similar_pattern(
        self,
        name: str,
        code_template: str,
        session: AsyncSession
    ) -> Optional[CodePattern]:
        """Find similar existing pattern to avoid duplicates."""
        # Use PostgreSQL similarity functions
        query = select(CodePattern).where(
            or_(
                CodePattern.name.op('%%')(name),
                CodePattern.template.op('%%')(code_template)
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_or_create_tags(
        self,
        tag_names: List[str],
        session: AsyncSession
    ) -> List[Tag]:
        """Efficiently get or create tags in batch."""
        # Prepare upsert statement
        stmt = insert(Tag).values([
            {'name': name} for name in tag_names
        ]).on_conflict_do_nothing()
        
        await session.execute(stmt)
        
        # Get all tags in one query
        query = select(Tag).where(Tag.name.in_(tag_names))
        result = await session.execute(query)
        return result.scalars().all()
    
    async def add_relation(
        self,
        source_id: int,
        target_id: int,
        relation_type: str,
        weight: float = 1.0,
        session: Optional[AsyncSession] = None
    ):
        """Add relation with caching and batch processing."""
        key = (source_id, target_id)
        if key in self._relation_cache:
            return
        
        self._pending_operations.append({
            'type': 'relation',
            'data': {
                'source_id': source_id,
                'target_id': target_id,
                'relation_type': relation_type,
                'weight': weight
            }
        })
        
        # Process batch if needed
        if len(self._pending_operations) >= self.batch_size:
            await self._process_pending_operations(session)
    
    async def _process_pending_operations(self, session: Optional[AsyncSession] = None):
        """Process pending operations in batch."""
        if not self._pending_operations:
            return
            
        async with self.session_factory() if session is None else session:
            relations = [
                op['data'] for op in self._pending_operations 
                if op['type'] == 'relation'
            ]
            
            if relations:
                # Batch insert relations
                stmt = insert(PatternRelation).values(relations)
                await session.execute(stmt)
                
                # Update cache and graph
                for rel in relations:
                    key = (rel['source_id'], rel['target_id'])
                    self._relation_cache.add(key)
                    self.graph.add_edge(
                        rel['source_id'],
                        rel['target_id'],
                        type=rel['relation_type'],
                        weight=rel['weight']
                    )
            
            self._pending_operations.clear()
    
    async def find_patterns(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find patterns using PostgreSQL full-text search."""
        async with self.session_factory() as session:
            # Use GiST index for pattern search
            stmt = select(CodePattern).where(
                or_(
                    CodePattern.name.match(query),
                    CodePattern.description.match(query),
                    CodePattern.template.match(query)
                )
            ).limit(limit)
            
            result = await session.execute(stmt)
            patterns = result.scalars().all()
            return [await p.to_dict() for p in patterns]
    
    async def get_related_patterns(
        self,
        pattern_id: int,
        relation_type: Optional[str] = None,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """Get related patterns using graph traversal."""
        if pattern_id not in self.graph:
            return []
            
        related = set()
        current = {pattern_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current:
                for _, neighbor in self.graph.edges(node):
                    if relation_type is None or self.graph.edges[node, neighbor]['type'] == relation_type:
                        next_level.add(neighbor)
            current = next_level
            related.update(current)
        
        patterns = []
        for pid in related:
            if pid in self._pattern_cache:
                pattern_dict = await self.get_pattern(pid)
                if pattern_dict:
                    patterns.append(pattern_dict)
        return patterns
    
    async def record_pattern_usage(
        self,
        pattern_id: int,
        context: Dict[str, Any]
    ):
        """Record pattern usage with context."""
        async with self.session_factory() as session:
            usage = PatternUsage(
                pattern_id=pattern_id,
                context=context,
                used_at=datetime.now()
            )
            session.add(usage)
            
            # Update pattern weights based on usage
            await self._update_pattern_weights(pattern_id, session)
    
    async def _update_pattern_weights(
        self,
        pattern_id: int,
        session: AsyncSession
    ):
        """Update relation weights based on pattern usage."""
        # Get pattern usage count
        usage_count = await session.scalar(
            select(PatternUsage)
            .where(PatternUsage.pattern_id == pattern_id)
            .count()
        )
        
        # Update weights in graph
        for _, neighbor in self.graph.edges(pattern_id):
            edge = self.graph.edges[pattern_id, neighbor]
            edge['weight'] *= (1 + (usage_count / 100))  # Adjust weight formula as needed
    
    async def cleanup(self):
        """Process any pending operations and cleanup."""
        async with self.session_factory() as session:
            await self._process_pending_operations(session)
            await session.commit()

    async def save_state(self):
        """Save current state to database."""
        async with self.session_factory() as session:
            await self._process_pending_operations(session)
            await session.commit()

    async def get_current_state(self) -> Dict[str, Any]:
        """Get current knowledge state."""
        patterns = []
        for pattern in self._pattern_cache.values():
            pattern_dict = await pattern.to_dict()
            patterns.append(pattern_dict)

        relations = []
        for source_id, target_id in self._relation_cache:
            edge = self.graph.edges[source_id, target_id]
            relations.append({
                "from": source_id,
                "to": target_id,
                "type": edge["type"],
                "weight": edge["weight"]
            })

        return {
            "patterns": patterns,
            "relationships": relations,
            "focus_areas": list(set(p.get("metadata", {}).get("focus_area") for p in patterns if p.get("metadata")))
        }