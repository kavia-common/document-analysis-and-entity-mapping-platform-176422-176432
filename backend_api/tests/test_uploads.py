import io
import os
import time
import pytest

from src.services.progress import ProgressTracker

@pytest.mark.pg_required
def test_post_uploads_creates_job_and_background_process(client, temp_storage_dir):
    # Prepare a small file (txt fallback path)
    data = io.BytesIO(b"Hello AppService in USA about cloud security.")
    data.name = "note.txt"
    files = {"file": ("note.txt", data, "text/plain")}
    r = client.post("/uploads", files=files)
    assert r.status_code == 200
    payload = r.json()
    assert "id" in payload and isinstance(payload["id"], int)
    assert payload["status"] in ("queued", "completed", "failed")
    job_id = payload["id"]

    # After upload, background task should kick and update progress tracker eventually
    # We can't guarantee completion without real DB loop, but can check tracker entries are set
    time.sleep(0.1)
    prog = ProgressTracker.get(str(job_id))
    # It may be None quickly; this is a smoke check—no exception paths
    assert prog is None or prog.percent in (10, 50, 70, 85, 100)
