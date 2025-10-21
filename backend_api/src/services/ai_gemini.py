from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.core.config import get_settings
from src.core.logger import get_logger

logger = get_logger(__name__)

try:
    import google.generativeai as genai  # type: ignore
    GENAI_AVAILABLE = True
except Exception as e:  # pragma: no cover - environment dependent
    logger.warning("google-generativeai client not available: %s", e)
    GENAI_AVAILABLE = False
    genai = None  # type: ignore


def _fallback_extract(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Simple heuristic extraction when AI not available."""
    import re

    tokens = set(re.findall(r"[A-Z][a-zA-Z0-9_-]{2,}", text))
    apps = [t for t in tokens if any(k in t.lower() for k in ("app", "svc", "service"))]
    locations = [t for t in tokens if t.lower() in {"us", "usa", "europe", "apac", "emea", "india"}]
    domains = [t for t in tokens if any(k in t.lower() for k in ("data", "cloud", "security", "network"))]
    statuses = []
    result: Dict[str, List[Dict[str, Any]]] = {
        "applications": [{"value": v, "confidence": 0.4} for v in apps][:25],
        "domains": [{"value": v, "confidence": 0.4} for v in domains][:25],
        "locations": [{"value": v, "confidence": 0.3} for v in locations][:25],
        "statuses": [{"value": v, "confidence": 0.2} for v in statuses][:25],
    }
    return result


# PUBLIC_INTERFACE
async def extract_entities_with_gemini(text: str) -> Tuple[bool, Dict[str, Any], str | None]:
    """Use Gemini to extract entities from text. Returns (success, raw_entities, error)."""
    settings = get_settings()
    if not settings.GEMINI_API_KEY or not GENAI_AVAILABLE:
        logger.warning("Gemini not configured; using fallback extraction")
        return True, _fallback_extract(text), None

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        prompt = (
            "Extract key entities from the following text. "
            "Return a JSON object with keys: applications, domains, locations, statuses. "
            "Each key maps to a list of objects with 'value' and optional 'confidence' fields. "
            "Text:\n"
            f"{text[:50_000]}"
        )
        resp = await model.generate_content_async(prompt)  # type: ignore[attr-defined]
        # The SDK returns a response; try to parse JSON from text
        out_text = resp.text if hasattr(resp, "text") else str(resp)
        import json
        try:
            data = json.loads(out_text)
        except Exception:
            # try to extract json block
            import re
            m = re.search(r"\{.*\}", out_text, re.DOTALL)
            data = json.loads(m.group(0)) if m else _fallback_extract(text)
        return True, data, None
    except Exception as e:
        logger.warning("Gemini extraction failed, using fallback: %s", e)
        return True, _fallback_extract(text), str(e)
