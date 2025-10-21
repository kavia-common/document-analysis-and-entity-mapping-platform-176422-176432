from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.services.taxonomy import get_full_taxonomy

router = APIRouter()


# PUBLIC_INTERFACE
@router.get("/taxonomy", summary="Get taxonomy tree")
async def list_taxonomy(session: AsyncSession = Depends(get_async_session)) -> List[Dict[str, Any]]:
    """Return the full taxonomy tree with nested L1 -> L2 -> L3."""
    return await get_full_taxonomy(session)
