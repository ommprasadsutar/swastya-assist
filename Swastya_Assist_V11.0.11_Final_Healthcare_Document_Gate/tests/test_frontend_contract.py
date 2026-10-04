from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def test_id_helper_and_runtime_ids():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "const $ = id => document.getElementById(id);" in js
    ids = set(re.findall(r'id="([^"]+)"', html))
    used = set(re.findall(r"\$\('([^']+)'\)", js))
    dynamic = {"reviewForm", "reviewSaveState", "retryOcrBtn", "retryTriageBtn", "retryVoiceAi", "callPatientBtn", "contactState"}
    assert not (used - ids - dynamic)

def test_upload_and_voice_controls():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    for ident in ["triageFile","triagePreview","removeTriageFile","changeTriageFile","ocrFile","preview","ocrRemove","changeOcrFile","voice","voiceStop","voiceAi","liveTranscript","aiTranslation","voiceDiagnostic","dashboardQueue","detailBody","ocrResult","riskBars","langBars","statusBars"]:
        assert f'id="{ident}"' in html


def test_review_cache_and_contact_ui():
    html = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "static/app.js").read_text(encoding="utf-8")
    assert '/static/app.js?v=21.0' in html
    assert 'Final operational priority' in js
    assert 'name="contact_patient"' in js
    assert 'name="contact_phone"' in js
    assert 'name="contact_consent"' in js
    assert 'callPatientBtn' in js
