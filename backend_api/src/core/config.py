from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # AI/OCR
    GEMINI_API_KEY: str | None
    GEMINI_MODEL: str
    OCR_LANG: str

    # Storage and uploads
    STORAGE_DIR: str
    MAX_FILE_SIZE_MB: int

    # CORS and logging
    ALLOWED_ORIGINS: List[str]
    LOG_LEVEL: str

    def __init__(self) -> None:
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")

        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or None
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.OCR_LANG = os.getenv("OCR_LANG", "eng")

        self.STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))

        allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
        self.ALLOWED_ORIGINS = [o.strip() for o in allowed_origins.split(",")] if allowed_origins else ["*"]

        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return cached application settings."""
    return _get_cached_settings()


@lru_cache(maxsize=1)
def _get_cached_settings() -> Settings:
    return Settings()
