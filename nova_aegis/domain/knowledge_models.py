"""
Knowledge domain models for pattern storage and relationships.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Table, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.util._concurrency_py3k import greenlet_spawn
from datetime import datetime
from typing import Dict

from ..database import Base

# Association tables
pattern_tags = Table(
    'pattern_tags',
    Base.metadata,
    Column('pattern_id', Integer, ForeignKey('code_patterns.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CodePattern(Base):
    __tablename__ = 'code_patterns'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    language = Column(String)
    framework = Column(String)
    template = Column(Text, nullable=False)
    pattern_metadata = Column('metadata', JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tags = relationship("Tag", secondary=pattern_tags)
    usages = relationship("PatternUsage", back_populates="pattern")
    source_relations = relationship(
        "PatternRelation",
        foreign_keys="PatternRelation.source_id",
        back_populates="source"
    )
    target_relations = relationship(
        "PatternRelation",
        foreign_keys="PatternRelation.target_id",
        back_populates="target"
    )

    async def to_dict(self) -> Dict:
        """Convert to dictionary."""
        tags = await greenlet_spawn(lambda: [t.name for t in self.tags])
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "framework": self.framework,
            "template": self.template,
            "metadata": self.pattern_metadata,
            "tags": tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class PatternRelation(Base):
    __tablename__ = 'code_pattern_relations'

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('code_patterns.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('code_patterns.id'), nullable=False)
    relation_type = Column(String, nullable=False)  # e.g., 'implements', 'extends', 'uses'
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source = relationship(
        "CodePattern",
        foreign_keys=[source_id],
        back_populates="source_relations"
    )
    target = relationship(
        "CodePattern",
        foreign_keys=[target_id],
        back_populates="target_relations"
    )

class PatternUsage(Base):
    __tablename__ = 'pattern_usages'

    id = Column(Integer, primary_key=True)
    pattern_id = Column(Integer, ForeignKey('code_patterns.id'), nullable=False)
    context = Column(JSON)  # Store usage context
    used_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    pattern = relationship("CodePattern", back_populates="usages")