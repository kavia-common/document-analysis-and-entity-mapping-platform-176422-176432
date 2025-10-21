from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.db.models import Job, Document, Extraction, Entity, Report
from src.db.schemas import EntitySchema
from src.services.progress import ProgressTracker
from src.services.taxonomy import upsert_mapping
from src.services.report import generate_report_for_job
from src.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class JobStatusResponse(BaseModel):
    job_id: int = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    stage: str | None = Field(None, description="Current stage")
    message: str | None = Field(None, description="Stage message")
    percent: int | None = Field(None, description="Progress percent")


class MappingRequest(BaseModel):
    raw_value: str = Field(..., description="Raw entity value to map")
    l1_id: int | None = Field(None, description="Level 1 taxonomy id")
    l2_id: int | None = Field(None, description="Level 2 taxonomy id")
    l3_id: int | None = Field(None, description="Level 3 taxonomy id")


# PUBLIC_INTERFACE
@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse, summary="Get job status")
async def get_job_status(job_id: int, session: AsyncSession = Depends(get_async_session)) -> JobStatusResponse:
    """Return job status including in-memory progress info."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    prog = ProgressTracker.get(str(job_id))
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        stage=prog.stage if prog else None,
        message=prog.message if prog else None,
        percent=prog.percent if prog else None,
    )


# PUBLIC_INTERFACE
@router.get("/jobs/{job_id}/entities", summary="Get grouped entities for a job")
async def get_job_entities(job_id: int, session: AsyncSession = Depends(get_async_session)) -> Dict[str, List[EntitySchema]]:
    """Return entities grouped by type from the latest extraction per document."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    doc_rows = (await session.execute(select(Document).where(Document.job_id == job_id))).scalars().all()
    e_by_type: Dict[str, List[EntitySchema]] = {"application": [], "domain": [], "location": [], "status": []}
    for d in doc_rows:
        ex = (await session.execute(
            select(Extraction).where(Extraction.document_id == d.id).order_by(Extraction.extracted_at.desc())
        )).scalars().first()
        if not ex:
            continue
        ents = (await session.execute(select(Entity).where(Entity.extraction_id == ex.id))).scalars().all()
        for e in ents:
            if e.type not in e_by_type:
                e_by_type[e.type] = []
            e_by_type[e.type].append(EntitySchema.model_validate(e))
    return e_by_type


# PUBLIC_INTERFACE
@router.post("/jobs/{job_id}/taxonomy/map", summary="Save mapping overrides for entities")
async def post_job_mapping(job_id: int, payload: MappingRequest, session: AsyncSession = Depends(get_async_session)) -> Dict[str, Any]:
    """Persist a mapping override for a given raw value and return updated info."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    m = await upsert_mapping(session, payload.raw_value, payload.l1_id, payload.l2_id, payload.l3_id)
    await session.commit()
    return {"ok": True, "mapping_id": m.id}


# PUBLIC_INTERFACE
@router.get("/jobs/{job_id}/report", summary="Generate and download the Excel report")
async def get_job_report(job_id: int, session: AsyncSession = Depends(get_async_session)) -> Response:
    """Generate a 5-sheet Excel report for the job and return as a file download."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # If a report exists, return the latest file
    rep = (await session.execute(
        select(Report).where(Report.job_id == job_id).order_by(Report.created_at.desc())
    )).scalars().first()
    if rep and os.path.exists(rep.storage_path):
        return FileResponse(rep.storage_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=os.path.basename(rep.storage_path))

    # Otherwise, generate
    path, _meta = await generate_report_for_job(session, job_id)
    await session.commit()
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=os.path.basename(path))
