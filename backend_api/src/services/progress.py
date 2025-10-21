from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Progress:
    stage: str
    message: str
    percent: int


class ProgressTracker:
    """In-memory progress tracker keyed by job id."""

    _lock = threading.Lock()
    _data: Dict[str, Progress] = {}

    @classmethod
    def set(cls, job_id: str, stage: str, message: str, percent: int) -> None:
        with cls._lock:
            cls._data[job_id] = Progress(stage=stage, message=message, percent=percent)

    @classmethod
    def get(cls, job_id: str) -> Optional[Progress]:
        with cls._lock:
            return cls._data.get(job_id)

    @classmethod
    def clear(cls, job_id: str) -> None:
        with cls._lock:
            cls._data.pop(job_id, None)
