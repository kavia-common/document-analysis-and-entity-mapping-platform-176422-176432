from __future__ import annotations

import logging
import sys
from typing import Optional

from .config import get_settings


# PUBLIC_INTERFACE
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger with level from settings."""
    logger = logging.getLogger(name if name else "app")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(get_settings().LOG_LEVEL)
    return logger
