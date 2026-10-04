from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_healthcare_document_gate_present_and_before_identity_gate():
    assert "def uploaded_healthcare_document_error(data, is_ocr_workflow=False):" in APP
    health_gate = APP.index("verification_error, verification_code, detected_report_name = verify_uploaded_report_identity(")
    identity_gate = APP.index("def verify_uploaded_report_identity")
    assert identity_gate < health_gate
    assert "uploaded_healthcare_document_error(data, is_ocr_workflow=is_ocr_workflow)" in APP
    assert '"NON_HEALTH_DOCUMENT"' in APP
    assert '"HEALTH_DOCUMENT_NOT_VERIFIED"' in APP


def test_non_health_document_cannot_be_unlocked_by_filename_or_fallback():
    assert "A filename such as \"medical-report.pdf\" is untrusted and is NOT evidence that the document is medical." in APP
    assert "if processing_mode != \"AI\":" in APP
    assert "The uploaded document could not be verified as a healthcare document. No OCR, report extraction, or triage output was generated." in APP


def test_ocr_document_type_is_healthcare_constrained():
    assert '"ocr_document_type": {"type": "string", "enum": sorted(OCR_HEALTHCARE_DOCUMENT_TYPES)}' in APP
    assert "Do not diagnose, prescribe, or recommend treatment." in APP
