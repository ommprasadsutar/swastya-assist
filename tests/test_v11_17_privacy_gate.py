from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
HTML = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

def test_privacy_gates_default_on_and_separate_external_media_opt_in():
    assert 'PRIVACY_GATE_ENABLED = os.getenv("PRIVACY_GATE_ENABLED", "1") == "1"' in APP
    assert 'EXTERNAL_MEDIA_CONSENT_REQUIRED' in APP
    assert 'EXTERNAL_AUDIO_CONSENT_REQUIRED' in APP
    assert 'external_ai_media_consent' in HTML
    assert 'external_ai_audio_consent' in APP

def test_patient_contact_and_intake_identity_do_not_enter_prompt_template():
    start = APP.index('prompt = f"""', APP.index('@app.post("/api/triage")'))
    end = APP.index('""".strip()', start)
    prompt = APP[start:end]
    assert 'Symptoms: {ai_symptoms}' in prompt
    assert 'Report text: {ai_report}' in prompt
    assert 'contact_phone' not in prompt
    assert 'patient_ref' not in prompt
    assert 'address: {address}' not in prompt

def test_minimization_patterns_exist_and_privacy_center_is_visible():
    assert 'def privacy_minimize_text(value, known_name=""):' in APP
    assert '[REDACTED_EMAIL]' in APP
    assert '[REDACTED_POSSIBLE_ID]' in APP
    assert 'data-view="privacy"' in HTML
    assert 'id="view-privacy"' in HTML
    assert 'OCR inspects every page and masks likely identifier lines' in HTML or 'redacted derivative' in HTML

def test_deployed_static_assets_match_source():
    assert (ROOT / "public" / "static" / "app.js").read_bytes() == (ROOT / "static" / "app.js").read_bytes()
    assert (ROOT / "public" / "static" / "style.css").read_bytes() == (ROOT / "static" / "style.css").read_bytes()
