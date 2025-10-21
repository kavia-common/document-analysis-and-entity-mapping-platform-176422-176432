import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Central Base for declarative models
Base = declarative_base()

def _get_database_url() -> str:
    """
    Resolve database URL from environment. Must be an asyncpg URL.
    Example: postgresql+asyncpg://user:password@host:5432/dbname
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    # If user supplied a sync URL, try to adapt to asyncpg
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

# Create a global AsyncEngine and session factory
DATABASE_URL = _get_database_url()
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=(os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"),
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# PUBLIC_INTERFACE
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a request-scoped AsyncSession for FastAPI dependencies."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Session context manager handles close
            ...
