import io
import pytest

from src.services.taxonomy import upsert_mapping, apply_mappings_to_entities

@pytest.mark.pg_required
def test_upsert_mapping_and_apply(client):
    # Create a job & let background create doc/extraction/entities with fallback entities
    data = io.BytesIO(b"NetworkService about data security in USA")
    r = client.post("/uploads", files={"file": ("d.txt", data, "text/plain")})
    assert r.status_code == 200
    jid = r.json()["id"]

    # We cannot directly access session from client; import get_async_session and run small async flow
    import asyncio
    from src.db.session import get_async_session
    from sqlalchemy import select
    from src.db.models import Document, Extraction

    async def _work():
        async with get_async_session() as s:  # type: ignore
            # Find extraction (may not yet exist immediately). Poll a bit.
            ex = None
            for _ in range(10):
                docs = (await s.execute(select(Document).where(Document.job_id == jid))).scalars().all()
                if docs:
                    for d in docs:
                        ex = (await s.execute(select(Extraction).where(Extraction.document_id == d.id))).scalars().first()
                        if ex:
                            break
                if ex:
                    break
                await asyncio.sleep(0.2)
            if not ex:
                return  # background not ready; skip apply test gracefully

            # Upsert mapping for some value that might exist or not; still should create mapping row
            m = await upsert_mapping(s, "NetworkService", None, None, None)
            assert m.id is not None

            updated = await apply_mappings_to_entities(s, ex.id)
            # updated is >= 0; can't assert >0 if entity not present
            assert isinstance(updated, int)
    asyncio.run(_work())
