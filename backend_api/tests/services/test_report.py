import io
import os
import pytest

@pytest.mark.pg_required
def test_generate_report_meta_sheets_is_five(client, tmp_path):
    # Upload to create a job
    data = io.BytesIO(b"AppOne about data in EMEA")
    r = client.post("/uploads", files={"file": ("g.txt", data, "text/plain")})
    assert r.status_code == 200
    jid = r.json()["id"]

    # Build report via endpoint to populate DB report row, then meta check via service is implicit.
    r2 = client.get(f"/jobs/{jid}/report")
    assert r2.status_code == 200
    # Can't easily read the workbook here without filesystem path. The service sets meta={"sheets": 5}
    # We will import a session and check latest report meta.
    import asyncio
    from src.db.session import get_async_session
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from src.db.models import Report

    async def _check():
        async with get_async_session() as s:  # type: ignore
            rep = (await s.execute(select(Report).where(Report.job_id == jid))).scalars().first()
            assert rep is not None
            assert rep.meta and rep.meta.get("sheets") == 5
    asyncio.run(_check())
