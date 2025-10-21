from __future__ import annotations

from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TaxonomyL1, TaxonomyL2, TaxonomyL3, Mapping, Entity
from src.core.logger import get_logger

logger = get_logger(__name__)


# PUBLIC_INTERFACE
async def get_full_taxonomy(session: AsyncSession) -> List[Dict[str, Any]]:
    """Return taxonomy tree as nested dicts L1->L2->L3."""
    l1_rows = (await session.execute(select(TaxonomyL1))).scalars().all()
    l2_rows = (await session.execute(select(TaxonomyL2))).scalars().all()
    l3_rows = (await session.execute(select(TaxonomyL3))).scalars().all()

    l2_by_l1: Dict[int, List[TaxonomyL2]] = {}
    for l2 in l2_rows:
        l2_by_l1.setdefault(l2.l1_id, []).append(l2)
    l3_by_l2: Dict[int, List[TaxonomyL3]] = {}
    for l3 in l3_rows:
        l3_by_l2.setdefault(l3.l2_id, []).append(l3)

    tree: List[Dict[str, Any]] = []
    for l1 in l1_rows:
        node_l2 = []
        for l2 in l2_by_l1.get(l1.id, []):
            node_l3 = [{"id": x.id, "name": x.name} for x in l3_by_l2.get(l2.id, [])]
            node_l2.append({"id": l2.id, "name": l2.name, "l3": node_l3})
        tree.append({"id": l1.id, "name": l1.name, "l2": node_l2})
    return tree


# PUBLIC_INTERFACE
async def upsert_mapping(session: AsyncSession, raw_value: str, l1_id: Optional[int], l2_id: Optional[int], l3_id: Optional[int], kind: str = "entity") -> Mapping:
    """Create or update a mapping for a raw value."""
    stmt = select(Mapping).where(Mapping.raw_value == raw_value, Mapping.kind == kind)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.l1_id = l1_id
        existing.l2_id = l2_id
        existing.l3_id = l3_id
        await session.flush()
        return existing
    m = Mapping(raw_value=raw_value, l1_id=l1_id, l2_id=l2_id, l3_id=l3_id, kind=kind)
    session.add(m)
    await session.flush()
    return m


# PUBLIC_INTERFACE
async def apply_mappings_to_entities(session: AsyncSession, extraction_id: int) -> int:
    """Apply existing mappings to entities of a given extraction."""
    # For simplicity, we fetch entities and update based on mapping table
    ent_stmt = select(Entity).where(Entity.extraction_id == extraction_id)
    entities = (await session.execute(ent_stmt)).scalars().all()
    if not entities:
        return 0
    # Build mapping dict by raw_value
    if not entities:
        return 0
    raw_values = {e.value for e in entities}
    map_stmt = select(Mapping).where(Mapping.raw_value.in_(raw_values))
    maps = (await session.execute(map_stmt)).scalars().all()
    mapped_by_raw = {m.raw_value: m for m in maps}
    updated = 0
    for e in entities:
        m = mapped_by_raw.get(e.value)
        if m:
            e.l1_id = m.l1_id
            e.l2_id = m.l2_id
            e.l3_id = m.l3_id
            updated += 1
    if updated:
        await session.flush()
    return updated
