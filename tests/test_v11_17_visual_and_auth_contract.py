from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

def test_invalid_credentials_render_friendly_page_not_framework_error():
    assert 'Invalid username or password. Please check your credentials and try again.' in APP
    assert 'selected_role=selected_role), 401' not in APP

def test_intake_and_ocr_results_do_not_expose_full_raw_extraction():
    marker = "function renderNote(n, warning, el = $('result'))"
    section = JS[JS.index(marker):JS.index('// Voice:', JS.index(marker))]
    assert 'full_report_extraction' not in section
    assert 'report-extraction' not in section

def test_reviewer_screen_retains_full_report_extraction():
    assert 'reviewer-full-extraction' in JS
    assert 'n.full_report_extraction' in JS

def test_voice_translation_is_editable_and_cached():
    assert 'VOICE_DRAFT_KEY' in JS
    assert "$('aiTranslation').value" in JS
    assert "$('liveTranscript').value" in JS

def test_visual_refresh_and_phone_touch_targets_present():
    assert '--blue:#176b87' in CSS
    assert 'class="nav-icon' in INDEX
    assert 'min-height:44px' in CSS
    assert '/static/style.css?v=43.0' in INDEX
