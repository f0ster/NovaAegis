"""
Project domain models for code management and tracking.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from ..database import Base

# Association tables
snippet_tags = Table(
    'snippet_tags',
    Base.metadata,
    Column('snippet_id', Integer, ForeignKey('code_snippets.id')),
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
    project_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    code_snippets = relationship("CodeSnippet", back_populates="project")
    dependencies = relationship("Dependency", back_populates="project")
    file_changes = relationship("FileChange", back_populates="project")
    context = relationship("ProjectContext", back_populates="project", uselist=False)
    search_history = relationship("SearchHistory", back_populates="project")

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

class ProjectContext(Base):
    __tablename__ = 'project_contexts'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), unique=True)
    architecture_summary = Column(Text)
    tech_stack = Column(JSON)
    key_patterns = Column(JSON)
    development_notes = Column(Text)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="context")