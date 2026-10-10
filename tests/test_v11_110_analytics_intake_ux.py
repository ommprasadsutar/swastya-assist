from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_analytics_explains_empty_data_without_showing_zero_only():
    assert 'id="analyticsEmpty" class="status-box hidden" role="status" aria-live="polite"' in INDEX
    assert "No encounters are available yet." in JS
    assert "Zero values here reflect an empty dataset, not measured facility performance." in JS
    assert "filter(([,v])=>Number(v)>0)" in JS


def test_intake_stops_empty_submission_before_an_ai_request():
    submit = JS[JS.index("async function submitTriage"):JS.index("const TRIAGE_DRAFT_KEY")]
    assert "hasNarrativeOrReportText" in submit
    assert "More information needed" in submit
    assert "No AI request was made." in submit
    assert "if (!retry && !uploadChosen && !hasNarrativeOrReportText)" in submit


def test_intake_and_ocr_purposes_are_distinct():
    assert "use AI Reports & OCR when a document is the main input" in INDEX
    assert "Use this focused report-first workflow" in INDEX


def test_v11_1_10_release_metadata_matches():
    assert VERSION == "11.1.10"
    assert 'APP_VERSION = "11.1.10"' in APP
    assert 'app.js?v=40.0' in INDEX


def test_analytics_does_not_turn_zero_buckets_into_empty_bars():
    assert "Object.entries(obj||{}).filter(([,v])=>Number(v)>0)" in JS
