from pathlib import Path

ROOT = Path(__file__).resolve().parent
app = (ROOT / "app.py").read_text(encoding="utf-8")
assert 'APP_VERSION = "10.4.3"' in app
assert 'httpx.post(' in app
assert app.count('httpx.post(') == 1
assert 'GEMINI_GENERATE_URL_TEMPLATE' in app
assert ':generateContent' in app
assert 'interactions.create' not in app
assert 'HttpRetryOptions' not in app
assert 'client.files.upload' not in app
assert 'client.files.delete' not in app
assert 'GEMINI_FALLBACK_MODELS = []' in app
assert '"type": "audio"' in app
assert '"type": "image"' in app
assert '"type": "document"' in app
assert 'data.get("candidates")' in app
print("Swastya Assist V10.4.3 GenerateContent transport contract: PASS")
