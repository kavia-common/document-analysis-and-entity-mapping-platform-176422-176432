from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.db.models import Job, Document, Extraction, Entity
from src.db.schemas import JobSchema
from src.services.storage import save_upload, copy_to_tmp
from src.services.parsing import parse_file_to_text
from src.services.ai_gemini import extract_entities_with_gemini
from src.services.taxonomy import apply_mappings_to_entities
from src.services.progress import ProgressTracker
from src.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


async def _process_job(job_id: int, file_path: str, session: AsyncSession) -> None:
    """Background pipeline to parse, extract entities, and persist results."""
    try:
        ProgressTracker.set(str(job_id), "parsing", "Parsing document", 10)
        # Load job
        job = await session.get(Job, job_id)
        if not job:
            return
        # Parse file
        tmp_path = copy_to_tmp(file_path)
        text, meta = parse_file_to_text(tmp_path)
        doc = Document(job_id=job_id, name=meta.get("name", job.filename), content_text=text, meta=meta, page_count=None)
        session.add(doc)
        await session.flush()

        ProgressTracker.set(str(job_id), "ai", "Extracting entities", 50)
        ok, raw_entities, err = await extract_entities_with_gemini(text or "")
        model_name = "gemini" if err is None else "fallback"
        extr = Extraction(document_id=doc.id, model_name=model_name, raw_entities=raw_entities, success=ok, error_message=err)
        session.add(extr)
        await session.flush()

        ProgressTracker.set(str(job_id), "persist", "Saving entities", 70)
        # Persist entities grouped by type keys
        for etype in ("applications", "domains", "locations", "statuses"):
            items: List[Dict[str, Any]] = raw_entities.get(etype, []) if isinstance(raw_entities, dict) else []
            for item in items:
                value = str(item.get("value", "")).strip()
                if not value:
                    continue
                conf = item.get("confidence")
                session.add(Entity(extraction_id=extr.id, type=etype[:-1], value=value, confidence=conf))

        await session.flush()

        ProgressTracker.set(str(job_id), "mapping", "Applying known mappings", 85)
        await apply_mappings_to_entities(session, extr.id)

        job.status = "completed"
        job.updated_at = datetime.utcnow()
        await session.commit()
        ProgressTracker.set(str(job_id), "completed", "Job completed", 100)
    except Exception as e:
        logger.exception("Job %s failed: %s", job_id, e)
        try:
            job = await session.get(Job, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                await session.commit()
        finally:
            ProgressTracker.set(str(job_id), "failed", f"Job failed: {e}", 100)


# PUBLIC_INTERFACE
@router.post("/uploads", response_model=JobSchema, summary="Upload a document for processing", description="Accepts a document file and starts a background job to parse and extract entities.")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
) -> JobSchema:
    """Upload a file, create a job, and launch background processing."""
    try:
        job_uuid, storage_path = save_upload(file)
    except ValueError as ve:
        raise HTTPException(status_code=413, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {e}")

    job = Job(status="queued", filename=file.filename, storage_path=storage_path)
    session.add(job)
    await session.flush()
    await session.commit()

    # Launch background processing; pass a fresh session on demand
    async def task(job_id: int, path: str) -> None:
        async with get_async_session() as bg_session:
            await _process_job(job_id, path, bg_session)  # type: ignore[arg-type]

    background_tasks.add_task(task, job.id, storage_path)
    return JobSchema.model_validate(job)
