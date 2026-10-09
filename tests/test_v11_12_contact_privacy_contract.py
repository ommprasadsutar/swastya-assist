from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text()
HTML = (ROOT / "templates/index.html").read_text()

def test_patient_intake_has_optional_contact_field():
    assert 'name="contact_phone"' in HTML
    intake = HTML.split('<section id="view-dashboard"', 1)[0]
    assert 'name="contact_phone"' in intake
    assert 'not sent to AI' in intake

def test_contact_phone_is_excluded_from_ai_prompt_data():
    triage_start = APP.index('@app.post("/api/triage")')
    triage = APP[triage_start: APP.index('@app.get("/api/cases/<cid>/report")', triage_start)]
    prompt_start = triage.index('prompt = f"""')
    prompt = triage[prompt_start: triage.index('""".strip()', prompt_start)]
    assert '{contact_phone}' not in prompt
    fingerprint_start = triage.index('payload_hash =')
    fingerprint = triage[fingerprint_start: triage.index('started, start_error', fingerprint_start)]
    assert 'contact_phone' not in fingerprint

def test_contact_phone_is_encrypted_and_optional():
    assert 'contact_phone = db.Column(EncryptedText()' in APP
    assert 'contact_phone=contact_phone' in APP
    assert 'if contact_phone and not valid_contact_phone(contact_phone)' in APP
