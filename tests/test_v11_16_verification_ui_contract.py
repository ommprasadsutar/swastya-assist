from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')


def test_verified_status_is_shown_before_report_extraction():
    verified = JS.index('verification-status-ok')
    details = JS.index('ocr-verified-details')
    assert verified < details
    assert 'Healthcare document verified and patient name matched.' in JS
    assert 'reviewer-full-extraction' in JS


def test_failed_verification_exposes_no_extraction_in_error_ui():
    blocked = JS.index('No extraction or triage output was exposed.')
    not_verified = JS.index('Verification status:</b> NOT VERIFIED')
    assert not_verified < blocked
    assert 'Patient-name verification:</b> NOT MATCHED' not in JS[JS.rfind('const detected = err.data?.code', 0, blocked):blocked]


def test_both_upload_error_paths_use_not_verified_status():
    assert JS.count('Report verification stopped') >= 2
    assert JS.count('Verification status:</b> NOT VERIFIED') >= 2
