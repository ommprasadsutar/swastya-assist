from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
APP=(ROOT/"app.py").read_text(encoding="utf-8")
INDEX=(ROOT/"templates"/"index.html").read_text(encoding="utf-8")
HOME=(ROOT/"templates"/"home.html").read_text(encoding="utf-8")
CSS=(ROOT/"static"/"style.css").read_text(encoding="utf-8")
JS=(ROOT/"static"/"app.js").read_text(encoding="utf-8")

def test_version_and_asset_bust():
    assert 'APP_VERSION = "11.1.10"' in APP
    assert '/static/style.css?v=43.0' in INDEX
    assert '/static/style.css?v=42.0' in HOME

def test_inline_svg_healthcare_icons_are_present():
    assert 'class="nav-icon icon-dashboard"' in INDEX
    assert '<svg viewBox="0 0 24 24"' in INDEX
    assert '<svg viewBox="0 0 24 24"' in HOME
    assert 'no external icon' not in INDEX.lower()

def test_structured_result_surface_contains_all_triage_sections():
    assert 'Clinical summary' in JS
    assert 'Timeline' in JS
    assert 'Key details' in JS
    assert 'Risk & urgency details' in JS
    assert 'Missing information' in JS
    assert 'Follow-up questions' in JS
    assert 'n.full_report_extraction' not in JS[JS.index('function renderNote'):JS.index('// Voice:', JS.index('function renderNote'))]

def test_contact_privacy_workflow_unchanged():
    assert 'contact_phone' in APP
    assert 'contact_patient' in JS
    assert 'not sent to AI' in INDEX

def test_static_public_copy_matches():
    assert (ROOT/'static'/'app.js').read_bytes() == (ROOT/'public'/'static'/'app.js').read_bytes()
    assert (ROOT/'static'/'style.css').read_bytes() == (ROOT/'public'/'static'/'style.css').read_bytes()
