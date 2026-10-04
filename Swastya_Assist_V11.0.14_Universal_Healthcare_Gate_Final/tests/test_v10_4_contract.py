from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def _load_function_from_app(name):
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[node], type_ignores=[])
    ns = {"str": str, "re": __import__("re"), "os": __import__("os"), "base64": __import__("base64")}
    exec(compile(ast.fix_missing_locations(module), "app.py", "exec"), ns)
    return ns[name]


def test_release_version_and_one_shot_generate_content_transport():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert 'APP_VERSION = "11.0.14"' in app
    assert 'GEMINI_GENERATE_API_VERSION = "v1beta"' in app
    assert 'GEMINI_GENERATE_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"' in app
    assert 'httpx.post(' in app
    assert app.count('httpx.post(') == 1
    assert 'GEMINI_INTERACTION_URL' not in app
    assert 'interactions.create' not in app
    assert 'HttpRetryOptions' not in app
    assert 'client.files.upload' not in app
    assert 'client.files.delete' not in app
    assert 'GEMINI_FALLBACK_MODELS = []' in app
    assert 'follow_redirects=False' in app
    for k in ("GEMINI_API_KEY=", "GEMINI_MODEL=", "GEMINI_VOICE_MODEL=", "GEMINI_GENERATE_API_VERSION=", "DATABASE_URL=", "DATA_ENCRYPTION_KEY=", "REDIS_URL=", "RATELIMIT_STORAGE_URI="):
        assert k in env


def test_generate_content_response_parser():
    parser = _load_function_from_app("_direct_output_text")
    current_response = {
        "candidates": [{
            "content": {"parts": [{"text": '{"ok":true}'}]}
        }],
        "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 7},
    }
    assert parser(current_response) == '{"ok":true}'


def test_generate_content_rest_payload_contract():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'payload = {"contents": [{"role": "user", "parts": parts}]}' in app
    assert '"inline_data"' in app
    assert '"mime_type"' in app
    assert '"data"' in app
    assert 'response_format' not in app
    assert 'generation_config' not in app


def test_durable_idempotency_and_single_retry():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert 'class AIRequestClaim(db.Model)' in app
    assert 'UniqueConstraint("request_id", "attempt_no"' in app
    assert 'attempt_no=2' in app
    assert 'not previous.retry_used' in app
    assert 'secrets.compare_digest(previous.retry_token, retry_token)' in app
    assert 'if (__triageInFlight) return;' in js
    assert 'if (__voiceInFlight) return;' in js
    assert 'if (__ocrInFlight) return;' in js
    assert 'This is the one allowed retry' in js


def test_voice_single_inline_audio_generate_content():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '"type": "audio", "data": base64.b64encode(raw).decode("ascii")' in app
    assert '_direct_gemini_generate_content(GEMINI_VOICE_MODEL, voice_items)' in app
    assert 'gemini_text_generate(trans_prompt, feature="voice_translation")' not in app
    assert 'client.files.upload' not in app
    assert 'client.files.delete' not in app


def test_voice_parser_accepts_structured_json():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'return str(data.get("transcript", "")).strip(), str(data.get("translation", "")).strip()' in app


def test_no_duplicate_dynamic_retry_button_ids_in_template():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    for element_id in ("retryTriageBtn", "retryVoiceAi"):
        assert html.count(f'id="{element_id}"') == 0


def test_public_frontend_is_synced():
    for name in ("app.js", "boot.js", "login.js", "landing.js", "style.css", "packet.css"):
        assert (ROOT / "public" / "static" / name).read_bytes() == (ROOT / "static" / name).read_bytes()


def test_generate_content_media_builder():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'def _generate_content_input' in app
    assert '"type": "document"' in app
    assert '"type": "image"' in app
    assert '"type": "audio"' in app
