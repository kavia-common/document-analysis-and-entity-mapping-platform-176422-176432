"""initial schema and minimal taxonomy seed"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Jobs
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, index=True),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_jobs_status_created_at", "jobs", ["status", "created_at"])

    # Documents
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
    )

    # Extractions
    op.create_table(
        "extractions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_name", sa.String(length=128), nullable=False, index=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("raw_entities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_extractions_doc_model", "extractions", ["document_id", "model_name"])

    # Taxonomy tables
    op.create_table(
        "taxonomy_l1",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True, index=True),
    )
    op.create_table(
        "taxonomy_l2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("l1_id", sa.Integer(), sa.ForeignKey("taxonomy_l1.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.UniqueConstraint("l1_id", "name", name="uq_taxonomy_l2_l1_name"),
    )
    op.create_table(
        "taxonomy_l3",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("l2_id", sa.Integer(), sa.ForeignKey("taxonomy_l2.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.UniqueConstraint("l2_id", "name", name="uq_taxonomy_l3_l2_name"),
    )

    # Entities
    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("extraction_id", sa.Integer(), sa.ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(length=64), nullable=False, index=True),
        sa.Column("value", sa.String(length=512), nullable=False, index=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("l1_id", sa.Integer(), sa.ForeignKey("taxonomy_l1.id"), nullable=True),
        sa.Column("l2_id", sa.Integer(), sa.ForeignKey("taxonomy_l2.id"), nullable=True),
        sa.Column("l3_id", sa.Integer(), sa.ForeignKey("taxonomy_l3.id"), nullable=True),
    )
    op.create_index("ix_entities_type_value", "entities", ["type", "value"])

    # Mappings
    op.create_table(
        "mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_value", sa.String(length=512), nullable=False, index=True),
        sa.Column("l1_id", sa.Integer(), sa.ForeignKey("taxonomy_l1.id"), nullable=True),
        sa.Column("l2_id", sa.Integer(), sa.ForeignKey("taxonomy_l2.id"), nullable=True),
        sa.Column("l3_id", sa.Integer(), sa.ForeignKey("taxonomy_l3.id"), nullable=True),
        sa.Column("kind", sa.String(length=64), nullable=False, server_default="entity"),
        sa.UniqueConstraint("raw_value", "kind", name="uq_mappings_raw_kind"),
    )

    # Reports
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Minimal taxonomy seed
    conn = op.get_bind()
    # Seed L1
    result = conn.execute(sa.text("INSERT INTO taxonomy_l1 (name) VALUES (:n1), (:n2), (:n3) RETURNING id, name"),
                          {"n1": "Applications", "n2": "Domains", "n3": "Locations"})
    l1_map = {row.name: row.id for row in result}
    # Seed L2 examples
    if "Applications" in l1_map:
        app_l1 = l1_map["Applications"]
        result = conn.execute(sa.text(
            "INSERT INTO taxonomy_l2 (l1_id, name) VALUES (:l1,'Web'),(:l1,'Mobile') RETURNING id, name"),
            {"l1": app_l1}
        )
        l2_map = {row.name: row.id for row in result}
        # Seed L3 examples
        if "Web" in l2_map:
            web_l2 = l2_map["Web"]
            conn.execute(sa.text(
                "INSERT INTO taxonomy_l3 (l2_id, name) VALUES (:l2,'Frontend'),(:l2,'Backend')"
            ), {"l2": web_l2})


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("mappings")
    op.drop_index("ix_entities_type_value", table_name="entities")
    op.drop_table("entities")
    op.drop_table("taxonomy_l3")
    op.drop_table("taxonomy_l2")
    op.drop_table("taxonomy_l1")
    op.drop_index("ix_extractions_doc_model", table_name="extractions")
    op.drop_table("extractions")
    op.drop_table("documents")
    op.drop_index("ix_jobs_status_created_at", table_name="jobs")
    op.drop_table("jobs")
