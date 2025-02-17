"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager
import os
from typing import Generator, AsyncGenerator
from urllib.parse import quote_plus

# Base class for all models
Base = declarative_base()

# Environment variables for database configuration
DB_USER = os.getenv("DB_USER", "nova_aegis")
DB_PASS = os.getenv("DB_PASS", "research")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "knowledge_store")

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=bool(os.getenv("SQL_ECHO", False))
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session with automatic closing"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_project_db(project_id: int) -> Generator[Session, None, None]:
    """Get database session with project context"""
    with get_db() as db:
        # You could add project-specific initialization here
        yield db

class DatabaseManager:
    """Database connection and transaction management"""
    
    @staticmethod
    @contextmanager
    def transaction():
        """Context manager for database transactions"""
        with get_db() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    @staticmethod
    def execute_in_transaction(func):
        """Decorator for executing functions in a transaction"""
        def wrapper(*args, **kwargs):
            with DatabaseManager.transaction() as db:
                return func(db, *args, **kwargs)
        return wrapper

    @staticmethod
    def paginate(query, page: int = 1, per_page: int = 20):
        """Helper method for pagination"""
        return query.limit(per_page).offset((page - 1) * per_page)

    @staticmethod
    def create_database():
        """Create database if it doesn't exist"""
        from sqlalchemy_utils import create_database, database_exists
        
        if not database_exists(engine.url):
            create_database(engine.url)
            init_db()

class AsyncDatabaseManager:
    """Async database operations for concurrent processing"""
    
    def __init__(self):
        # Create async engine
        self.async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=bool(os.getenv("SQL_ECHO", False)),
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        
        # Create async session factory
        self.async_session = async_sessionmaker(
            self.async_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def get_async_db(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def execute_async(self, query):
        """Execute async database query"""
        async with self.get_async_db() as db:
            result = await db.execute(query)
            return result

    async def init_async_db(self):
        """Initialize database tables asynchronously"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

# Database migration functions
def run_migrations(direction: str = "upgrade") -> None:
    """Run database migrations"""
    from alembic import command
    from alembic.config import Config
    
    # Get the path to alembic.ini
    alembic_cfg = Config("alembic.ini")
    
    if direction == "upgrade":
        command.upgrade(alembic_cfg, "head")
    elif direction == "downgrade":
        command.downgrade(alembic_cfg, "-1")
    else:
        raise ValueError("Invalid migration direction")

def create_migration(message: str) -> None:
    """Create a new migration"""
    from alembic import command
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, autogenerate=True, message=message)