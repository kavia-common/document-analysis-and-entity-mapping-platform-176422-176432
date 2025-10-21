from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile
from src.core.config import get_settings
from src.core.logger import get_logger

logger = get_logger(__name__)


def ensure_dirs() -> None:
    base = Path(get_settings().STORAGE_DIR)
    (base / "uploads").mkdir(parents=True, exist_ok=True)
    (base / "reports").mkdir(parents=True, exist_ok=True)
    (base / "tmp").mkdir(parents=True, exist_ok=True)


# PUBLIC_INTERFACE
def save_upload(file: UploadFile) -> Tuple[str, str]:
    """Save uploaded file to storage/uploads and return (job_id, storage_path)."""
    ensure_dirs()
    settings = get_settings()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    # Generate job id and file path
    job_id = str(uuid.uuid4())
    dest_dir = Path(settings.STORAGE_DIR) / "uploads" / job_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename

    size = 0
    with dest_path.open("wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                f.close()
                dest_path.unlink(missing_ok=True)
                raise ValueError("File exceeds MAX_FILE_SIZE_MB")
            f.write(chunk)

    logger.info("Saved upload %s (%d bytes) to %s", file.filename, size, dest_path)
    return job_id, str(dest_path)


# PUBLIC_INTERFACE
def copy_to_tmp(path: str) -> str:
    """Copy a file to storage/tmp for processing and return new path."""
    ensure_dirs()
    src = Path(path)
    tmp_dir = Path(get_settings().STORAGE_DIR) / "tmp"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    tmp_path = tmp_dir / f"{uuid.uuid4()}_{src.name}"
    shutil.copy2(src, tmp_path)
    return str(tmp_path)
