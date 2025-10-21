from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    Text,
    UniqueConstraint,
    Index,
    JSON,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base

# Jobs track processing per upload
class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), index=True, default="queued")
    filename: Mapped[str] = mapped_column(String(512))
    storage_path: Mapped[str] = mapped_column(String(1024))
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    documents: Mapped[list[Document]] = relationship("Document", back_populates="job", cascade="all, delete-orphan")
    reports: Mapped[list[Report]] = relationship("Report", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_status_created_at", "status", "created_at"),
    )


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(512))
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    job: Mapped[Job] = relationship("Job", back_populates="documents")
    extractions: Mapped[list[Extraction]] = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")


class Extraction(Base):
    __tablename__ = "extractions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    raw_entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship("Document", back_populates="extractions")
    entities: Mapped[list[Entity]] = relationship("Entity", back_populates="extraction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_extractions_doc_model", "document_id", "model_name"),
    )


class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    extraction_id: Mapped[int] = mapped_column(ForeignKey("extractions.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(64), index=True)  # application | domain | location | status | other
    value: Mapped[str] = mapped_column(String(512), index=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)

    l1_id: Mapped[Optional[int]] = mapped_column(ForeignKey("taxonomy_l1.id"), nullable=True)
    l2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("taxonomy_l2.id"), nullable=True)
    l3_id: Mapped[Optional[int]] = mapped_column(ForeignKey("taxonomy_l3.id"), nullable=True)

    extraction: Mapped[Extraction] = relationship("Extraction", back_populates="entities")
    l1: Mapped[Optional[TaxonomyL1]] = relationship("TaxonomyL1")
    l2: Mapped[Optional[TaxonomyL2]] = relationship("TaxonomyL2")
    l3: Mapped[Optional[TaxonomyL3]] = relationship("TaxonomyL3")

    __table_args__ = (
        Index("ix_entities_type_value", "type", "value"),
    )


class TaxonomyL1(Base):
    __tablename__ = "taxonomy_l1"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)


class TaxonomyL2(Base):
    __tablename__ = "taxonomy_l2"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    l1_id: Mapped[int] = mapped_column(ForeignKey("taxonomy_l1.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))

    l1: Mapped[TaxonomyL1] = relationship("TaxonomyL1")

    __table_args__ = (UniqueConstraint("l1_id", "name", name="uq_taxonomy_l2_l1_name"),)


class TaxonomyL3(Base):
    __tablename__ = "taxonomy_l3"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    l2_id: Mapped[int] = mapped_column(ForeignKey("taxonomy_l2.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))

    l2: Mapped[TaxonomyL2] = relationship("TaxonomyL2")

    __table_args__ = (UniqueConstraint("l2_id", "name", name="uq_taxonomy_l3_l2_name"),)


class Mapping(Base):
    __tablename__ = "mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Original raw value to normalize
    raw_value: Mapped[str] = mapped_column(String(512), index=True)
    # To which taxonomy node it maps (at least l1 or l2 or l3)
    l1_id: Mapped[Optional[int]] = mapped_column(ForeignKey("taxonomy_l1.id"), nullable=True)
    l2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("taxonomy_l2.id"), nullable=True)
    l3_id: Mapped[Optional[int]] = mapped_column(ForeignKey("taxonomy_l3.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(64), default="entity")  # for future subtypes

    l1: Mapped[Optional[TaxonomyL1]] = relationship("TaxonomyL1")
    l2: Mapped[Optional[TaxonomyL2]] = relationship("TaxonomyL2")
    l3: Mapped[Optional[TaxonomyL3]] = relationship("TaxonomyL3")

    __table_args__ = (
        UniqueConstraint("raw_value", "kind", name="uq_mappings_raw_kind"),
    )


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    storage_path: Mapped[str] = mapped_column(String(1024))
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    job: Mapped[Job] = relationship("Job", back_populates="reports")
