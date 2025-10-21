import io
import pytest

@pytest.mark.pg_required
def test_get_job_status_404_when_missing(client):
    r = client.get("/jobs/999999/status")
    assert r.status_code == 404

@pytest.mark.pg_required
def test_flow_status_and_entities_empty_initial(client):
    # Upload to create job
    data = io.BytesIO(b"Initial text about AppSvc and Network domain in USA.")
    data.name = "t.txt"
    r = client.post("/uploads", files={"file": ("t.txt", data, "text/plain")})
    assert r.status_code == 200
    job = r.json()
    jid = job["id"]

    r = client.get(f"/jobs/{jid}/status")
    assert r.status_code == 200
    status = r.json()
    assert status["job_id"] == jid
    assert status["status"] in ("queued", "completed", "failed")

    # Entities may be empty early; ensure 200 and object shape
    r = client.get(f"/jobs/{jid}/entities")
    # Could be 200 or 404 if background not yet created entities; be lenient:
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        entities = r.json()
        assert isinstance(entities, dict)
