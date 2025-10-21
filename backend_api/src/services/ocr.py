from __future__ import annotations

from typing import Optional

from PIL import Image
from src.core.logger import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)

try:
    import pytesseract  # type: ignore
    TESS_AVAILABLE = True
except Exception as e:  # pragma: no cover - environment dependent
    logger.warning("pytesseract not available or misconfigured: %s", e)
    pytesseract = None  # type: ignore
    TESS_AVAILABLE = False


# PUBLIC_INTERFACE
def ocr_image(image: Image.Image, lang: Optional[str] = None) -> str:
    """OCR an image to text. Falls back to empty string if OCR is not configured."""
    if not TESS_AVAILABLE or pytesseract is None:
        return ""
    language = lang or get_settings().OCR_LANG
    try:
        return pytesseract.image_to_string(image, lang=language)
    except Exception as e:
        logger.warning("OCR failed, continuing without text: %s", e)
        return ""
