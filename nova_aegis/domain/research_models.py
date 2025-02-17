"""
Research domain models for tracking searches and findings.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Table, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from ..database import Base

# Association tables
research_tags = Table(
    'research_tags',
    Base.metadata,
    Column('research_id', Integer, ForeignKey('research_results.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

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
    results = relationship("ResearchResult", back_populates="search")

class ResearchResult(Base):
    __tablename__ = 'research_results'

    id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey('search_history.id'))
    url = Column(String, nullable=False)
    title = Column(String)
    content_summary = Column(Text)
    code_blocks = Column(JSON)  # Store extracted code examples
    visited_at = Column(DateTime(timezone=True), server_default=func.now())
    relevance_score = Column(Integer)  # For ranking search results
    insights = Column(JSON)  # Store extracted insights
    confidence = Column(Float)  # Confidence in findings

    # Relationships
    search = relationship("SearchHistory", back_populates="results")
    tags = relationship("Tag", secondary=research_tags)
    patterns = relationship("CodePattern", secondary="result_patterns")

class ResultPattern(Base):
    """Track patterns found in research results."""
    __tablename__ = 'result_patterns'

    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey('research_results.id'))
    pattern_id = Column(Integer, ForeignKey('code_patterns.id'))
    confidence = Column(Float)  # Confidence in pattern match
    context = Column(JSON)  # Context where pattern was found
    created_at = Column(DateTime(timezone=True), server_default=func.now())