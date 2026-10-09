from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
JS = (ROOT / "static/app.js").read_text(encoding="utf-8")


def test_cbc_medical_markers_are_present_for_false_negative_recovery():
    assert '"complete blood count"' in APP
    assert '"hemoglobin"' in APP
    assert '"platelet count"' in APP
    assert '"reference value"' in APP
    assert '"investigation"' in APP
    assert '"unit"' in APP
    assert "healthcare_document_evidence_score(data)" in APP
    assert "_healthcare_content_is_sufficient(data" in APP


def test_name_mismatch_returns_detected_name_but_not_clinical_output():
    mismatch = 'code="PATIENT_NAME_MISMATCH"'
    assert '"PATIENT_NAME_MISMATCH"' in APP
    assert 'report_patient_name = (data.get("report_patient_name") or "").strip()' in APP
    assert 'payload["report_patient_name"] = detected_report_name' in APP
    assert "def verify_uploaded_report_identity" in APP
    helper_start = APP.index("def verify_uploaded_report_identity")
    helper_chunk = APP[helper_start:helper_start + 1200]
    assert "No OCR, report extraction, or triage output was generated." in helper_chunk


def test_patient_intake_renders_report_name_verification():
    assert "Uploaded report verification" in JS
    assert "Patient name on report:" in JS
    assert "VERIFIED" in JS
    assert "Healthcare document verified and patient name matched." in JS


def test_mismatch_error_ui_surfaces_name_without_ocr_details():
    assert "Detected report name:" in JS
    assert "PATIENT_NAME_MISMATCH" in JS
    assert "Verification status:</b> NOT VERIFIED" in JS
