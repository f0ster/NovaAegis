"""
Project management and caching for research workflows.
Handles project organization, storage, and result caching.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import structlog
import asyncio

logger = structlog.get_logger()

@dataclass
class Project:
    """Research project details."""
    name: str
    group: Optional[str]
    description: Optional[str]
    created_at: datetime
    last_updated: datetime
    metadata: Dict[str, Any]

@dataclass
class ResearchCache:
    """Cached research results."""
    query: str
    results: Dict[str, Any]
    graph_data: Dict[str, Any]
    insights: List[Dict[str, Any]]
    timestamp: datetime
    metadata: Dict[str, Any]

class ProjectManager:
    """Manages research projects and caching."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("data/projects")
        self.cache_dir = self.base_dir / "cache"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="project_manager")
        
        # Load existing projects
        self.projects: Dict[str, Project] = self._load_projects()
        self.groups: Dict[str, List[str]] = self._load_groups()
    
    def create_project(
        self,
        name: str,
        group: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Project:
        """Create new research project."""
        try:
            if name in self.projects:
                raise ValueError(f"Project {name} already exists")
            
            now = datetime.now()
            project = Project(
                name=name,
                group=group,
                description=description,
                created_at=now,
                last_updated=now,
                metadata=metadata or {}
            )
            
            # Save project
            self.projects[name] = project
            self._save_project(project)
            
            # Update group
            if group:
                if group not in self.groups:
                    self.groups[group] = []
                self.groups[group].append(name)
                self._save_groups()
            
            self.logger.info("project_created", name=name, group=group)
            return project
            
        except Exception as e:
            self.logger.error("project_creation_failed", error=str(e))
            raise
    
    def create_group(
        self,
        name: str,
        description: Optional[str] = None
    ) -> List[str]:
        """Create new project group."""
        try:
            if name in self.groups:
                raise ValueError(f"Group {name} already exists")
            
            self.groups[name] = []
            self._save_groups()
            
            self.logger.info("group_created", name=name)
            return self.groups[name]
            
        except Exception as e:
            self.logger.error("group_creation_failed", error=str(e))
            raise
    
    def get_project(self, name: str) -> Optional[Project]:
        """Get project by name."""
        return self.projects.get(name)
    
    def get_group_projects(self, group: str) -> List[Project]:
        """Get all projects in group."""
        if group not in self.groups:
            return []
        return [
            self.projects[name]
            for name in self.groups[group]
            if name in self.projects
        ]
    
    def get_cached_results(
        self,
        project: str,
        query: str
    ) -> Optional[ResearchCache]:
        """Get cached research results."""
        try:
            cache_file = self._get_cache_file(project, query)
            if not cache_file.exists():
                return None
            
            data = json.loads(cache_file.read_text())
            return ResearchCache(
                query=data["query"],
                results=data["results"],
                graph_data=data["graph_data"],
                insights=data["insights"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                metadata=data["metadata"]
            )
            
        except Exception as e:
            self.logger.error("cache_read_failed", error=str(e))
            return None
    
    def cache_results(
        self,
        project: str,
        query: str,
        results: Dict[str, Any],
        graph_data: Dict[str, Any],
        insights: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Cache research results."""
        try:
            cache = ResearchCache(
                query=query,
                results=results,
                graph_data=graph_data,
                insights=insights,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # Save cache
            cache_file = self._get_cache_file(project, query)
            cache_file.write_text(json.dumps({
                "query": cache.query,
                "results": cache.results,
                "graph_data": cache.graph_data,
                "insights": cache.insights,
                "timestamp": cache.timestamp.isoformat(),
                "metadata": cache.metadata
            }, indent=2))
            
            # Update project
            if project in self.projects:
                self.projects[project].last_updated = cache.timestamp
                self._save_project(self.projects[project])
            
            self.logger.info(
                "results_cached",
                project=project,
                query=query
            )
            
        except Exception as e:
            self.logger.error("cache_write_failed", error=str(e))
            raise
    
    def _load_projects(self) -> Dict[str, Project]:
        """Load existing projects."""
        projects = {}
        for file in self.base_dir.glob("*.json"):
            if file.stem == "groups":
                continue
            try:
                data = json.loads(file.read_text())
                projects[data["name"]] = Project(
                    name=data["name"],
                    group=data.get("group"),
                    description=data.get("description"),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    last_updated=datetime.fromisoformat(data["last_updated"]),
                    metadata=data.get("metadata", {})
                )
            except Exception as e:
                self.logger.error(
                    "project_load_failed",
                    file=file.name,
                    error=str(e)
                )
        return projects
    
    def _load_groups(self) -> Dict[str, List[str]]:
        """Load project groups."""
        groups_file = self.base_dir / "groups.json"
        if groups_file.exists():
            try:
                return json.loads(groups_file.read_text())
            except Exception as e:
                self.logger.error("groups_load_failed", error=str(e))
        return {}
    
    def _save_project(self, project: Project):
        """Save project to file."""
        project_file = self.base_dir / f"{project.name}.json"
        project_file.write_text(json.dumps({
            "name": project.name,
            "group": project.group,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "last_updated": project.last_updated.isoformat(),
            "metadata": project.metadata
        }, indent=2))
    
    def _save_groups(self):
        """Save groups to file."""
        groups_file = self.base_dir / "groups.json"
        groups_file.write_text(json.dumps(self.groups, indent=2))
    
    def _get_cache_file(self, project: str, query: str) -> Path:
        """Get cache file path for query."""
        # Use hash of query as filename to avoid invalid characters
        query_hash = str(hash(query))
        return self.cache_dir / f"{project}_{query_hash}.json"