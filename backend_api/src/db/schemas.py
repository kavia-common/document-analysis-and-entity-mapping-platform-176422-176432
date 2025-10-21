from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class TaxonomyL3Schema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TaxonomyL2Schema(BaseModel):
    id: int
    name: str
    l3: Optional[List[TaxonomyL3Schema]] = None

    class Config:
        from_attributes = True


class TaxonomyL1Schema(BaseModel):
    id: int
    name: str
    l2: Optional[List[TaxonomyL2Schema]] = None

    class Config:
        from_attributes = True


class EntitySchema(BaseModel):
    id: int
    type: str
    value: str
    confidence: Optional[float] = None
    l1_id: Optional[int] = None
    l2_id: Optional[int] = None
    l3_id: Optional[int] = None

    class Config:
        from_attributes = True


class ExtractionSchema(BaseModel):
    id: int
    document_id: int
    model_name: str
    extracted_at: datetime
    raw_entities: Optional[Dict[str, Any]] = None
    success: bool
    error_message: Optional[str] = None
    entities: Optional[List[EntitySchema]] = None

    class Config:
        from_attributes = True


class DocumentSchema(BaseModel):
    id: int
    job_id: int
    name: str
    content_text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    page_count: Optional[int] = None
    extractions: Optional[List[ExtractionSchema]] = None

    class Config:
        from_attributes = True


class ReportSchema(BaseModel):
    id: int
    job_id: int
    created_at: datetime
    storage_path: str
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class JobSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    status: str
    filename: str
    storage_path: str
    error_message: Optional[str] = None
    documents: Optional[List[DocumentSchema]] = None
    reports: Optional[List[ReportSchema]] = None

    class Config:
        from_attributes = True
