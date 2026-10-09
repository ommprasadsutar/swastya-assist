from pathlib import Path

ROOT = Path(__file__).resolve().parent
app = (ROOT / "app.py").read_text(encoding="utf-8")
assert 'APP_VERSION = "11.1.8"' in app
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
print("Swastya Assist V11.1.8 GenerateContent transport contract: PASS")

assert "class Facility(db.Model)" in app
assert "def facility_case_query()" in app
assert "def case_for_current_user(cid)" in app
assert "ai_risk = db.Column" in app
assert "final_risk = db.Column" in app
assert "def validate_ai_payload(data, allow_ocr_fields=False):" in app
assert "PATIENT_DATA_START" in app
assert "DEMO_ONLY_MODE" in app
assert '@app.post("/api/cases/<cid>/referral")' in app
print("Swastya Assist V11.1.8 safety hardening contract: PASS")

assert '@app.post("/api/cases/<cid>/contact")' in app
assert "contact_phone = db.Column" in app
assert "contact_consent = db.Column" in app
assert '@app.get("/favicon.ico")' in app
print("Swastya Assist V11.1.8 contact and favicon contract: PASS")

assert "def _unrelated_term_present(text, term):" in app
assert 'def health_relevance_error(symptoms, report, filename="", has_upload=False):' in app
assert "if has_upload:" in app
assert "health_relevance_error(symptoms, report, filename_hint, has_upload=has_upload)" in app
print("Swastya Assist V11.0.16 unified uploaded-document gate regression contract: PASS")

assert "verification-status-ok" in (ROOT / "static/app.js").read_text(encoding="utf-8")
assert "ocr-verified-details" in (ROOT / "static/app.js").read_text(encoding="utf-8")
assert "No extraction or triage output was exposed." in (ROOT / "static/app.js").read_text(encoding="utf-8")
assert (ROOT / "static/app.js").read_bytes() == (ROOT / "public/static/app.js").read_bytes()
assert (ROOT / "static/style.css").read_bytes() == (ROOT / "public/static/style.css").read_bytes()
print("Swastya Assist V11.1.8 verification-first UI contract: PASS")
