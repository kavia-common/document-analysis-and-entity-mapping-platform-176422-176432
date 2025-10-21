import os
import io
import asyncio
import tempfile
import shutil
from contextlib import asynccontextmanager

import pytest
import anyio
from starlette.testclient import TestClient
from fastapi import FastAPI
from dotenv import load_dotenv

# Make sure env is loaded
load_dotenv()

# Force simple env for tests: storage tempdir, disable real GEMINI, allow sqlite for some unit tests
@pytest.fixture(scope="session")
def _test_env(tmp_path_factory):
    storage_dir = tmp_path_factory.mktemp("storage")
    os.environ.setdefault("STORAGE_DIR", str(storage_dir))
    os.environ.setdefault("MAX_FILE_SIZE_MB", "5")
    os.environ.setdefault("GEMINI_API_KEY", "")  # force fallback path
    # For backend code, DATABASE_URL is required at import time; the app uses asyncpg by default.
    # Many service tests don't hit DB; for route tests that import session engine, we mark as pg_required
    return {"STORAGE_DIR": str(storage_dir)}

@pytest.fixture(scope="session")
def app(_test_env):
    # Import here to ensure env vars above are in effect
    from src.api.main import app as fastapi_app
    return fastapi_app

@pytest.fixture()
def client(app):
    # Starlette TestClient runs sync; our endpoints are async but supported
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def temp_storage_dir(_test_env):
    return _test_env["STORAGE_DIR"]

# Tiny file bytes for uploads and service parsing
@pytest.fixture()
def tiny_pdf_bytes():
    # minimal PDF header and object, acceptable to pdfminer for empty text
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"

@pytest.fixture()
def tiny_docx_file(tmp_path):
    # Create a tiny docx (using python-docx requires writing via library - but to avoid external libs here,
    # we provide a minimal .docx zip structure would be complex. For unit tests of parsing we will skip DOCX if lib fails).
    f = tmp_path / "sample.docx"
    f.write_bytes(b"")  # empty; parser should handle exception and return meta with error
    return f

@pytest.fixture()
def tiny_pptx_file(tmp_path):
    f = tmp_path / "sample.pptx"
    f.write_bytes(b"")  # empty; parser should handle exception
    return f

@pytest.fixture()
def tiny_xlsx_file(tmp_path):
    f = tmp_path / "sample.xlsx"
    # openpyxl requires a valid file; we will generate a small valid workbook via openpyxl
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["A", "B"])
    ws.append([1, 2])
    wb.save(f)
    return f

@pytest.fixture()
def tiny_jpg_file(tmp_path):
    # Create a tiny RGB image via Pillow
    from PIL import Image
    f = tmp_path / "sample.jpg"
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(f, format="JPEG")
    return f

# Async helper to wait for condition in polling tests
@pytest.fixture()
def wait_until():
    async def _wait_until(fn, timeout=2.5, interval=0.05):
        import time
        end = time.time() + timeout
        last = None
        while time.time() < end:
            last = fn()
            if last:
                return last
            await anyio.sleep(interval)
        return last
    return _wait_until
