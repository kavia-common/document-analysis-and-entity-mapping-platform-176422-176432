import pytest
from src.services.ai_gemini import extract_entities_with_gemini

@pytest.mark.asyncio
async def test_gemini_uses_fallback_when_key_missing(monkeypatch):
    # Ensure GEMINI_API_KEY empty
    monkeypatch.setenv("GEMINI_API_KEY", "")
    ok, data, err = await extract_entities_with_gemini("CloudApp provides network security in USA")
    assert ok is True
    assert isinstance(data, dict)
    # Should include keys with lists
    for k in ("applications", "domains", "locations", "statuses"):
        assert k in data
        assert isinstance(data[k], list)
