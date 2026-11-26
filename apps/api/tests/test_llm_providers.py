"""The provider adapter builds the right request for each provider and never puts the key in a URL."""
import json
from app.config import get_settings
from app.services import llm


class _R:
    def __init__(self, body): self._b = json.dumps(body).encode()
    def read(self): return self._b
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _run(monkeypatch, provider, reply):
    seen = {}
    s = get_settings()
    monkeypatch.setattr(s, "llm_provider", provider); monkeypatch.setattr(s, "llm_api_key", "KEY123"); monkeypatch.setattr(s, "llm_model", "m")
    def fake(req, timeout=0):
        seen["url"] = req.full_url; seen["headers"] = {k.lower(): v for k, v in req.header_items()}; seen["body"] = json.loads(req.data)
        return _R(reply)
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake)
    return llm._call("sys", "hi"), seen


def test_gemini(monkeypatch):
    out, seen = _run(monkeypatch, "gemini", {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})
    assert out == "ok" and "KEY123" not in seen["url"] and seen["headers"]["x-goog-api-key"] == "KEY123"
    assert seen["body"]["systemInstruction"]["parts"][0]["text"] == "sys"


def test_groq_and_anthropic(monkeypatch):
    out, seen = _run(monkeypatch, "groq", {"choices": [{"message": {"content": "hey"}}]})
    assert out == "hey" and seen["headers"]["authorization"] == "Bearer KEY123"
    out, _ = _run(monkeypatch, "anthropic", {"content": [{"type": "text", "text": "yo"}]})
    assert out == "yo"


def test_unknown_provider(monkeypatch):
    import pytest
    s = get_settings(); monkeypatch.setattr(s, "llm_provider", "nope")
    with pytest.raises(llm.LlmUnavailable):
        llm._call("a", "b")
