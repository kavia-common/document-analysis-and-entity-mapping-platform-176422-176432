import io
import pytest

@pytest.mark.pg_required
def test_get_report_generates_xlsx(client):
    # Create a job
    data = io.BytesIO(b"Some content about AppSvc and Data domain in EMEA.")
    r = client.post("/uploads", files={"file": ("r.txt", data, "text/plain")})
    assert r.status_code == 200
    jid = r.json()["id"]

    # Request report; may generate if not exists
    r2 = client.get(f"/jobs/{jid}/report")
    # Could be slow if background not completed; the service generates even with zero entities
    assert r2.status_code == 200
    # In FastAPI, FileResponse returns binary; under TestClient it can be bytes
    ctype = r2.headers.get("content-type") or r2.headers.get("Content-Type")
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in (ctype or "")
