import ast
import base64
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_transport():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {"_normalize_gemini_model", "_gemini_error_details", "_direct_gemini_generate_content"}
    nodes = [n for n in tree.body if (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and (n.name in wanted or n.name == "GeminiHTTPError"))]
    module = ast.Module(body=nodes, type_ignores=[])
    ns = {"str": str, "re": __import__("re"), "os": os, "base64": base64, "GEMINI_GENERATE_URL_TEMPLATE": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"}
    exec(compile(ast.fix_missing_locations(module), "app.py", "exec"), ns)
    return ns["_direct_gemini_generate_content"]


class FakeResponse:
    def __init__(self, status_code=200, body=None, text=""):
        self.status_code = status_code
        self._body = body if body is not None else {
            "candidates": [{"content": {"parts": [{"text": '{"ok":true}'}]}}]
        }
        self.text = text or json.dumps(self._body)

    def json(self):
        return self._body


def test_text_request_is_exactly_one_generate_content_post(monkeypatch):
    calls = []
    fake_httpx = types.SimpleNamespace()

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    fake_httpx.post = post
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    transport = _load_transport()

    result = transport("models/gemini-3.8-flash", "hello")
    assert result["candidates"][0]["content"]["parts"][0]["text"] == '{"ok":true}'
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    assert kwargs["follow_redirects"] is False
    assert kwargs["headers"]["x-goog-api-key"] == "test-key"
    assert kwargs["json"] == {"contents": [{"role": "user", "parts": [{"text": "hello"}]}]}


def test_audio_is_inline_data_and_still_one_post(monkeypatch):
    calls = []
    fake_httpx = types.SimpleNamespace()
    fake_httpx.post = lambda url, **kwargs: (calls.append((url, kwargs)) or FakeResponse())
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    transport = _load_transport()

    transport("gemini-3.8-flash", [
        {"type": "text", "text": "Transcribe."},
        {"type": "audio", "mime_type": "audio/webm", "data": base64.b64encode(b"abc").decode("ascii")},
    ])
    assert len(calls) == 1
    parts = calls[0][1]["json"]["contents"][0]["parts"]
    assert parts[1]["inline_data"]["mime_type"] == "audio/webm"
    assert parts[1]["inline_data"]["data"] == base64.b64encode(b"abc").decode("ascii")


def test_provider_400_is_exposed_without_retry(monkeypatch):
    calls = []
    fake_httpx = types.SimpleNamespace()
    fake_httpx.post = lambda url, **kwargs: (calls.append((url, kwargs)) or FakeResponse(400, {"error": {"status": "INVALID_ARGUMENT", "message": "bad payload"}}))
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    transport = _load_transport()

    try:
        transport("gemini-3.8-flash", "hello")
    except RuntimeError as exc:
        assert getattr(exc, "status_code", None) == 400
        assert getattr(exc, "provider_code", None) == "INVALID_ARGUMENT"
        assert "bad payload" in getattr(exc, "body", "")
    else:
        raise AssertionError("400 provider error must be raised")
    assert len(calls) == 1
