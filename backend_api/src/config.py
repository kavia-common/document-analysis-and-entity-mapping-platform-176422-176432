import os
from typing import List


class Settings:
    """Application settings sourced from environment variables with sensible defaults."""

    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()
