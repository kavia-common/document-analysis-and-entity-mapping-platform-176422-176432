from typing import Any

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from src.db.session import get_async_session
from src.core.config import get_settings
from src.core.logger import get_logger

# Routers
from .routes.uploads import router as uploads_router
from .routes.jobs import router as jobs_router
from .routes.taxonomy import router as taxonomy_router

load_dotenv()
settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title="Document Analysis and Entity Mapping API",
    description="Async FastAPI backend for document uploads, Gemini-based extraction, taxonomy mapping, and report generation.",
    version="0.1.0",
    openapi_tags=[
        {"name": "system", "description": "System and health endpoints"},
        {"name": "jobs", "description": "Processing jobs"},
        {"name": "documents", "description": "Documents and extractions"},
        {"name": "taxonomy", "description": "Taxonomy and mappings"},
        {"name": "reports", "description": "Report generation and retrieval"},
    ],
)

origins = settings.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
@app.get("/", tags=["system"], summary="Health Check")
def health_check() -> dict[str, str]:
    """Health check endpoint to validate the service is running."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get("/_db-ping", tags=["system"], summary="Database connectivity check")
async def db_ping(session: AsyncSession = Depends(get_async_session)) -> dict[str, Any]:
    """
    Simple DB connectivity check using an AsyncSession.

    Returns:
        JSON payload with ok: true if a trivial query succeeds.
    """
    await session.execute("SELECT 1")
    return {"ok": True}

# Include routers
app.include_router(uploads_router, prefix="", tags=["jobs"])
app.include_router(jobs_router, prefix="", tags=["jobs"])
app.include_router(taxonomy_router, prefix="", tags=["taxonomy"])
