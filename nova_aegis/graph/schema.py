"""
Schema management for Nebula Graph.
Handles schema creation, updates, and migrations.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import structlog
from datetime import datetime

from .query_builder import QueryBuilder, QueryPart

logger = structlog.get_logger()

@dataclass
class TagSchema:
    """Definition for a vertex tag schema."""
    name: str
    properties: Dict[str, str]
    indices: List[str] = None

@dataclass
class EdgeSchema:
    """Definition for an edge type schema."""
    name: str
    properties: Dict[str, str]
    indices: List[str] = None

@dataclass
class Migration:
    """Schema migration definition."""
    version: int
    description: str
    up_queries: List[str]
    down_queries: List[str]

class SchemaManager:
    """Manages graph schema and migrations."""
    
    def __init__(self, session, space_name: str):
        self.session = session
        self.space_name = space_name
        self.logger = logger.bind(component="schema_manager")
    
    async def init_schema(self):
        """Initialize base schema."""
        try:
            # Create space
            await self._create_space()
            
            # Create tags
            await self._create_tags([
                TagSchema(
                    name="Code",
                    properties={
                        "language": "string",
                        "code": "string",
                        "description": "string",
                        "source_url": "string",
                        "complexity": "double",
                        "created_at": "timestamp",
                        "tags": "set<string>",
                        "embedding": "list<double>"
                    },
                    indices=[
                        "language",
                        "source_url"
                    ]
                ),
                TagSchema(
                    name="Category",
                    properties={
                        "name": "string",
                        "description": "string"
                    },
                    indices=["name"]
                )
            ])
            
            # Create edges
            await self._create_edges([
                EdgeSchema(
                    name="RELATES_TO",
                    properties={
                        "relation_type": "string",
                        "weight": "double",
                        "properties": "map<string,string>"
                    },
                    indices=["relation_type"]
                ),
                EdgeSchema(
                    name="BELONGS_TO",
                    properties={
                        "confidence": "double"
                    }
                )
            ])
            
            self.logger.info("schema_initialized")
            
        except Exception as e:
            self.logger.error("schema_init_failed", error=str(e))
            raise
    
    async def _create_space(self):
        """Create graph space if not exists."""
        query = f"""
        CREATE SPACE IF NOT EXISTS {self.space_name}
        (partition_num=10, 
         replica_factor=1, 
         vid_type=FIXED_STRING(50))
        """
        await self._execute(query)
        await self._execute(f"USE {self.space_name}")
    
    async def _create_tags(self, tags: List[TagSchema]):
        """Create vertex tags."""
        for tag in tags:
            # Create tag
            props = ", ".join(
                f"{name} {type_}" 
                for name, type_ in tag.properties.items()
            )
            query = f"""
            CREATE TAG IF NOT EXISTS {tag.name}({props})
            """
            await self._execute(query)
            
            # Create indices
            if tag.indices:
                for field in tag.indices:
                    await self._execute(f"""
                    CREATE TAG INDEX IF NOT EXISTS 
                    {tag.name.lower()}_{field}_idx 
                    ON {tag.name}({field})
                    """)
    
    async def _create_edges(self, edges: List[EdgeSchema]):
        """Create edge types."""
        for edge in edges:
            # Create edge
            props = ", ".join(
                f"{name} {type_}" 
                for name, type_ in edge.properties.items()
            )
            query = f"""
            CREATE EDGE IF NOT EXISTS {edge.name}({props})
            """
            await self._execute(query)
            
            # Create indices
            if edge.indices:
                for field in edge.indices:
                    await self._execute(f"""
                    CREATE EDGE INDEX IF NOT EXISTS 
                    {edge.name.lower()}_{field}_idx 
                    ON {edge.name}({field})
                    """)
    
    async def run_migrations(self, target_version: Optional[int] = None):
        """Run schema migrations."""
        try:
            # Get current version
            current = await self._get_current_version()
            
            # Get migrations to run
            migrations = self._get_migrations()
            if target_version is None:
                target_version = max(m.version for m in migrations)
            
            # Run migrations
            if current < target_version:
                # Forward migrations
                to_apply = [
                    m for m in migrations 
                    if current < m.version <= target_version
                ]
                for migration in to_apply:
                    await self._apply_migration(migration)
                    
            elif current > target_version:
                # Rollback migrations
                to_rollback = [
                    m for m in migrations
                    if target_version < m.version <= current
                ]
                for migration in reversed(to_rollback):
                    await self._rollback_migration(migration)
            
            self.logger.info(
                "migrations_complete",
                from_version=current,
                to_version=target_version
            )
            
        except Exception as e:
            self.logger.error("migration_failed", error=str(e))
            raise
    
    async def _get_current_version(self) -> int:
        """Get current schema version."""
        try:
            result = await self._execute(
                "FETCH PROP ON schema_version 'current' YIELD version"
            )
            return int(result[0]['version'])
        except:
            return 0
    
    def _get_migrations(self) -> List[Migration]:
        """Get all available migrations."""
        return [
            Migration(
                version=1,
                description="Add embedding indices",
                up_queries=[
                    "CREATE TAG INDEX code_embedding_idx ON Code(embedding)",
                ],
                down_queries=[
                    "DROP TAG INDEX code_embedding_idx",
                ]
            ),
            Migration(
                version=2,
                description="Add timestamp indices",
                up_queries=[
                    "CREATE TAG INDEX code_created_idx ON Code(created_at)",
                ],
                down_queries=[
                    "DROP TAG INDEX code_created_idx",
                ]
            )
        ]
    
    async def _apply_migration(self, migration: Migration):
        """Apply a migration."""
        self.logger.info(
            "applying_migration",
            version=migration.version,
            description=migration.description
        )
        
        for query in migration.up_queries:
            await self._execute(query)
            
        await self._update_version(migration.version)
    
    async def _rollback_migration(self, migration: Migration):
        """Rollback a migration."""
        self.logger.info(
            "rolling_back_migration",
            version=migration.version,
            description=migration.description
        )
        
        for query in migration.down_queries:
            await self._execute(query)
            
        await self._update_version(migration.version - 1)
    
    async def _update_version(self, version: int):
        """Update schema version."""
        await self._execute(f"""
        UPDATE VERTEX ON schema_version 'current'
        SET version = {version}
        """)
    
    async def _execute(self, query: str):
        """Execute a query."""
        result = await self.session.execute(query)
        if not result.is_succeeded():
            raise Exception(f"Query failed: {result.error_msg()}")
        return result.rows()