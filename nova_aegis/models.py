"""
Database models for NovaAegis.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Table, Text, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Dict

Base = declarative_base()

# Association tables
snippet_tags = Table(
    'snippet_tags',
    Base.metadata,
    Column('snippet_id', Integer, ForeignKey('code_snippets.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

research_tags = Table(
    'research_tags',
    Base.metadata,
    Column('research_id', Integer, ForeignKey('research_results.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

pattern_tags = Table(
    'pattern_tags',
    Base.metadata,
    Column('pattern_id', Integer, ForeignKey('code_patterns.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    language = Column(String)
    framework = Column(String)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    project_metadata = Column(JSON)  # Renamed from metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    code_snippets = relationship("CodeSnippet", back_populates="project")
    search_history = relationship("SearchHistory", back_populates="project")
    dependencies = relationship("Dependency", back_populates="project")
    file_changes = relationship("FileChange", back_populates="project")
    research_results = relationship("ResearchResult", back_populates="project")

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
    template = Column(Text, nullable=False)
    metadata = Column(JSON)
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

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "metadata": self.metadata,
            "tags": [t.name for t in self.tags],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class PatternRelation(Base):
    __tablename__ = 'pattern_relations'

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

class CodeSnippet(Base):
    __tablename__ = 'code_snippets'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    title = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="code_snippets")
    tags = relationship("Tag", secondary=snippet_tags)

class SearchHistory(Base):
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    query = Column(String, nullable=False)
    source = Column(String, nullable=False)  # e.g., 'github', 'stackoverflow', 'docs'
    result_summary = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="search_history")

class Dependency(Base):
    __tablename__ = 'dependencies'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    name = Column(String, nullable=False)
    version = Column(String)
    type = Column(String)  # e.g., 'runtime', 'dev', 'peer'
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="dependencies")

class FileChange(Base):
    __tablename__ = 'file_changes'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    file_path = Column(String, nullable=False)
    change_type = Column(String, nullable=False)  # e.g., 'create', 'modify', 'delete'
    description = Column(Text)
    diff = Column(Text)  # Store git-style diffs
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="file_changes")

class ResearchResult(Base):
    __tablename__ = 'research_results'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    url = Column(String, nullable=False)
    title = Column(String)
    content_summary = Column(Text)
    code_blocks = Column(JSON)  # Store extracted code examples
    visited_at = Column(DateTime(timezone=True), server_default=func.now())
    relevance_score = Column(Integer)  # For ranking search results

    # Relationships
    project = relationship("Project", back_populates="research_results")
    tags = relationship("Tag", secondary=research_tags)

class ProjectContext(Base):
    __tablename__ = 'project_contexts'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), unique=True)
    architecture_summary = Column(Text)
    tech_stack = Column(JSON)
    key_patterns = Column(JSON)
    development_notes = Column(Text)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())