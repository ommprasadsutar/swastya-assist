from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_current_runtime_and_public_assets():
    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.13.5"
    assert (ROOT / "public" / "static" / "app.js").exists()
    assert (ROOT / "public" / "static" / "style.css").exists()
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in (
        "GEMINI_MODEL", "GEMINI_TRANSCRIBE_MODEL", "GEMINI_VOICE_MODEL", "GEMINI_API_VERSION",
        "GEMINI_FALLBACK_MODELS", "GEMINI_RETRY_ATTEMPTS", "COOKIE_SECURE", "DATABASE_URL",
        "DATA_ENCRYPTION_KEY", "CRON_SECRET", "RATELIMIT_STORAGE_URI",
    ):
        assert re.search(r"^" + re.escape(key) + r"=", env, re.M)


def test_current_generate_content_media_contract():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '"type": "audio"' in app
    assert '"type": "image"' in app
    assert '"type": "document"' in app
    assert "GEMINI_TRIAGE_RESPONSE_SCHEMA" in app
    assert "GEMINI_VOICE_RESPONSE_SCHEMA" in app
    assert 'data.get("candidates")' in app


def test_reviewer_controls_are_present():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    for ident in (
        "triageFile", "triagePreview", "changeTriageFile", "removeTriageFile", "ocrFile", "preview",
        "changeOcrFile", "ocrRemove", "voice", "voiceStop", "voiceAi", "dashboardQueue", "detailBody",
        "riskBars", "statusBars",
    ):
        assert f'id="{ident}"' in html
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "function saveReview" in js
    assert "Saved just now" in js
    assert "reviewer decision" in js.lower()
