from pathlib import Path

ROOT = Path(__file__).resolve().parent
app = (ROOT / "app.py").read_text(encoding="utf-8")
assert 'APP_VERSION = "11.0.11"' in app
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
print("Swastya Assist V11.0.11 GenerateContent transport contract: PASS")

assert "class Facility(db.Model)" in app
assert "def facility_case_query()" in app
assert "def case_for_current_user(cid)" in app
assert "ai_risk = db.Column" in app
assert "final_risk = db.Column" in app
assert "def validate_ai_payload(data, allow_ocr_fields=False):" in app
assert "PATIENT_DATA_START" in app
assert "DEMO_ONLY_MODE" in app
assert '@app.post("/api/cases/<cid>/referral")' in app
print("Swastya Assist V11.0.11 safety hardening contract: PASS")

assert '@app.post("/api/cases/<cid>/contact")' in app
assert "contact_phone = db.Column" in app
assert "contact_consent = db.Column" in app
assert '@app.get("/favicon.ico")' in app
print("Swastya Assist V11.0.11 contact and favicon contract: PASS")
