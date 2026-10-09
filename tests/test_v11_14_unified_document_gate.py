import ast
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


def _load_helpers():
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    wanted = {
        "HEALTHCARE_DOCUMENT_MARKERS", "HEALTHCARE_STRONG_MARKERS", "UNRELATED_TERMS",
        "OCR_HEALTHCARE_DOCUMENT_TYPES", "healthcare_document_evidence_score",
        "_healthcare_content_is_sufficient", "uploaded_healthcare_document_error",
        "_normalize_patient_name", "patient_name_matches_report", "verify_uploaded_report_identity",
        "_unrelated_term_present", "health_relevance_error",
    }
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in wanted for t in node.targets):
            nodes.append(node)
    ns = {"str": str, "re": re, "unicodedata": unicodedata}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(APP_PATH), "exec"), ns)
    return ns


def base(**kw):
    d = {
        "input_valid": True,
        "error": "",
        "summary": "",
        "timeline": "",
        "handoff": "Reviewer verify.",
        "report_patient_name": "Yashvi M. Patel",
        "full_report_extraction": "",
        "extracted_report_fields": [],
        "ocr_document_type": "Other healthcare document",
    }
    d.update(kw)
    return d


def test_cbc_and_general_healthcare_documents_pass_both_workflows():
    ns = _load_helpers()
    samples = [
        base(summary="Laboratory report", full_report_extraction="Patient Name Yashvi M Patel Complete Blood Count CBC Hemoglobin Platelet Count Reference Range Unit"),
        base(summary="Radiology report", full_report_extraction="Patient Name Yashvi M Patel Radiology MRI Clinical History Findings Impression" , ocr_document_type="Radiology report"),
        base(summary="Clinical note", full_report_extraction="Patient Name Yashvi M Patel Clinical Note Chief Complaint Assessment Physician Follow-up", ocr_document_type="Clinical note"),
        base(summary="Discharge summary", full_report_extraction="Patient Name Yashvi M Patel Discharge Summary Hospital Diagnosis Follow-up", ocr_document_type="Discharge summary"),
        base(summary="Prescription", full_report_extraction="Patient Name Yashvi M Patel Prescription Medication Tablet Dose Physician", ocr_document_type="Prescription / medication document"),
        base(summary="Referral", full_report_extraction="Patient Name Yashvi M Patel Referral Note Referring Physician Clinical History Follow-up", ocr_document_type="Referral note"),
        base(summary="Screening", full_report_extraction="Patient Name Yashvi M Patel Health Screening Screening Result Vaccination", ocr_document_type="Screening form"),
        base(summary="Maternal health", full_report_extraction="Patient Name Yashvi M Patel Maternal Antenatal Gestational Follow-up", ocr_document_type="Maternal-health document"),
        base(summary="Occupational health", full_report_extraction="Patient Name Yashvi M Patel Occupational Health Fitness Certificate Medical Officer", ocr_document_type="Occupational-health document"),
    ]
    for sample in samples:
        assert ns["uploaded_healthcare_document_error"](sample, False) is None
        assert ns["uploaded_healthcare_document_error"](sample, True) is None
        assert ns["verify_uploaded_report_identity"](sample, "Yashvi M. Patel", False)[0] is None
        assert ns["verify_uploaded_report_identity"](sample, "Yashvi M. Patel", True)[0] is None


def test_non_healthcare_is_blocked_in_both_workflows():
    ns = _load_helpers()
    samples = [
        base(summary="Invoice", full_report_extraction="Invoice Number Item Quantity Amount Payment Terms", ocr_document_type="Other healthcare document"),
        base(summary="Resume", full_report_extraction="Resume CV Skills Employment Education", ocr_document_type="Other healthcare document"),
        base(summary="Bank statement", full_report_extraction="Bank Statement Account Number Transaction Balance", ocr_document_type="Other healthcare document"),
        base(summary="Assignment", full_report_extraction="College Assignment Question Answer Mathematics", ocr_document_type="Other healthcare document"),
    ]
    for sample in samples:
        assert ns["uploaded_healthcare_document_error"](sample, False)
        assert ns["uploaded_healthcare_document_error"](sample, True)


def test_name_match_is_shared_and_mismatch_blocks_both_workflows():
    ns = _load_helpers()
    sample = base(summary="CBC", full_report_extraction="Complete Blood Count CBC Hemoglobin Platelet Count")
    for is_ocr in (False, True):
        err, code, detected = ns["verify_uploaded_report_identity"](sample, "Amit Kumar", is_ocr)
        assert code == "PATIENT_NAME_MISMATCH"
        assert detected == "Yashvi M. Patel"
        assert "No OCR, report extraction, or triage output was generated." in err


def test_missing_or_unreadable_report_name_blocks_both_workflows():
    ns = _load_helpers()
    sample = base(report_patient_name="", full_report_extraction="Complete Blood Count CBC Hemoglobin Platelet Count")
    for is_ocr in (False, True):
        err, code, detected = ns["verify_uploaded_report_identity"](sample, "Yashvi M. Patel", is_ocr)
        assert code == "PATIENT_NAME_MISMATCH"
        assert detected == ""


def test_uploaded_report_filename_is_not_used_to_reject_healthcare_document():
    ns = _load_helpers()
    # A filename such as cv.jpg must not block a real healthcare upload; content is verified later.
    assert ns["health_relevance_error"]("", "", "cv.jpg", has_upload=True) is None


def test_short_cv_token_does_not_false_positive_healthcare_content_gate():
    ns = _load_helpers()
    medical = base(
        summary="Laboratory report / CBC",
        full_report_extraction="Patient Name Yashvi M Patel Complete Blood Count CBC Hemoglobin Total WBC Platelet Count CV clinical note",
        ocr_document_type="Laboratory report",
    )
    assert ns["uploaded_healthcare_document_error"](medical, False) is None
    assert ns["uploaded_healthcare_document_error"](medical, True) is None
