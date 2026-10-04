import ast
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


def _load_helpers():
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    wanted = {
        "HEALTHCARE_DOCUMENT_MARKERS", "HEALTHCARE_STRONG_MARKERS",
        "UNRELATED_TERMS",
        "OCR_HEALTHCARE_DOCUMENT_TYPES",
        "healthcare_document_evidence_score", "_healthcare_content_is_sufficient",
        "uploaded_healthcare_document_error",
        "_normalize_patient_name", "_unrelated_term_present",
        "patient_name_matches_report",
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


def test_observed_cbc_report_is_recognized_as_healthcare_evidence():
    ns = _load_helpers()
    data = {
        "input_valid": False,
        "error": "The uploaded document does not appear to be a healthcare document.",
        "summary": "Complete Blood Count (CBC) laboratory report.",
        "handoff": "Reviewer verify all values.",
        "report_patient_name": "Yashvi M. Patel",
        "full_report_extraction": (
            "DRLOGY PATHOLOGY LAB Complete Blood Count (CBC) Investigation Result "
            "Reference Value Unit Hemoglobin Total RBC count Total WBC count "
            "Differential WBC Count Platelet Count"
        ),
        "extracted_report_fields": [],
    }
    score, markers = ns["healthcare_document_evidence_score"](data)
    assert score >= 3
    assert "complete blood count" in markers
    assert "hemoglobin" in markers
    assert "platelet count" in markers
    assert ns["uploaded_healthcare_document_error"](data, is_ocr_workflow=False) is None


def test_invoice_remains_blocked():
    ns = _load_helpers()
    data = {
        "input_valid": False,
        "error": "Invoice / non-healthcare",
        "summary": "Invoice for goods",
        "handoff": "No clinical review.",
        "report_patient_name": "Yashvi M. Patel",
        "full_report_extraction": "INVOICE Invoice Number Item Quantity Amount Payment Terms",
        "extracted_report_fields": [],
    }
    assert ns["uploaded_healthcare_document_error"](data, False)


def test_yashvi_name_matches_and_other_name_does_not():
    ns = _load_helpers()
    assert ns["patient_name_matches_report"]("Yashvi M. Patel", "Yashvi M. Patel") is True
    assert ns["patient_name_matches_report"]("Yashvi M. Patel", "Patel, Yashvi M.") is True
    assert ns["patient_name_matches_report"]("Yashvi M. Patel", "Amit Kumar") is False
