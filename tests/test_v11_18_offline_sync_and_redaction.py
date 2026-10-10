"""V11.1.10 regression checks for offline text sync and OCR media redaction.

Static contract checks run without Flask; pixel-redaction tests require Tesseract.
These tests use synthetic content only and do not call Gemini or any network service.
"""
from __future__ import annotations

import io
import re
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
HTML = (ROOT / "templates" / "offline_capture.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "offline_capture.js").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


def _route_body(source: str, decorator: str, next_decorator: str) -> str:
    start = source.index(decorator)
    end = source.index(next_decorator, start + len(decorator))
    return source[start:end]


def test_offline_capture_uses_encrypted_text_only_and_never_queues_media():
    assert "AES-GCM" in JS
    assert "PBKDF2_ITERATIONS = 310000" in JS
    assert "No AI · No file uploads" in HTML
    assert "Reports and raw audio are not stored or uploaded by this screen" in HTML
    assert "client_id" in JS and "server_case_id" in JS
    assert "crypto.subtle.encrypt" in JS and "crypto.subtle.decrypt" in JS


def test_offline_sync_requires_auth_csrf_encryption_and_is_idempotent():
    route = _route_body(APP, '@app.post("/api/offline-sync")', '@app.')
    assert "@require_role(*CLINICAL_ROLES, \"admin\")" in route
    assert "csrf_ok()" in route
    assert "DATA_ENCRYPTION_KEY" in route
    assert "OfflineSyncReceipt.query.filter_by(client_id=client_id).first()" in route
    assert '"Needs review"' in route
    assert '"Offline capture sync"' in route
    assert "requests.post" not in route and "urlopen" not in route
    assert "ai_request_start" not in route and "GEMINI_MODEL" not in route


def test_sync_rejects_unknown_fields_and_demo_identifiers():
    route = _route_body(APP, '@app.post("/api/offline-sync")', '@app.')
    assert '"UNSUPPORTED_FIELDS"' in route
    assert '"DEMO_IDENTIFIER_BLOCKED"' in route
    for key in ('"patient_ref"', '"patient_name"', '"symptoms"', '"consent"'):
        assert key in route


def test_service_worker_never_caches_authenticated_pages_or_api_responses():
    assert "url.pathname.startsWith('/api/')" in SW and "return;" in SW
    for path in ("/console", "/login", "/register", "/admin", "/patient", "/logout"):
        assert path in SW
    assert "swastya-offline-shell-v1110" in SW


def test_privacy_gate_only_uses_redacted_media_derivative_after_explicit_consent():
    route = _route_body(APP, '@app.post("/api/triage")', '@app.')
    assert 'request.form.get("external_ai_media_consent") == "on"' in route
    assert "redact_document_for_ai(raw, mime, patient_name)" in route
    assert "ai_image_bytes = media_redaction_result.data" in route
    assert 'code="MEDIA_REDACTION_FAILED"' in route
    assert 'code="REPORT_IDENTITY_UNVERIFIED"' in route
    assert 'original_media_sent": False' in route


def test_redaction_module_documents_best_effort_and_fail_closed_behavior():
    module = (ROOT / "privacy_redaction.py").read_text(encoding="utf-8")
    assert "OCR and pattern matching can miss identifiers" in module
    assert "no AI copy is returned" in module
    assert "sanitized.new_page" in module
    assert "insert_image" in module


@pytest.mark.skipif(not shutil.which("tesseract"), reason="Tesseract is needed for OCR redaction test")
def test_image_redaction_masks_synthetic_name_and_phone():
    from PIL import Image, ImageDraw, ImageFont
    from privacy_redaction import redact_document_for_ai

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 42) if Path(font_path).exists() else ImageFont.load_default()
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "LABORATORY REPORT",
        "Patient Name: Synthetic Patient",
        "Phone: 9876543210",
        "Email: test@example.com",
        "Hemoglobin: 13.2 g/dL",
    ]
    for index, line in enumerate(lines):
        draw.text((90, 70 + index * 130), line, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    result = redact_document_for_ai(buffer.getvalue(), "image/png", "Synthetic Patient")
    assert result.mime_type == "image/jpeg"
    assert result.pages == 1
    assert result.redacted_lines >= 2
    assert result.detected_report_name.casefold() == "synthetic patient"
    assert result.data != buffer.getvalue()


@pytest.mark.skipif(not shutil.which("tesseract"), reason="Tesseract is needed for OCR redaction test")
def test_pdf_redaction_flattens_text_layer_and_masks_synthetic_identifiers():
    import fitz
    from privacy_redaction import redact_document_for_ai

    source = fitz.open()
    page = source.new_page(width=595, height=842)
    page.insert_text((60, 90), "LABORATORY REPORT", fontsize=20)
    page.insert_text((60, 140), "Patient Name: Synthetic Patient", fontsize=18)
    page.insert_text((60, 180), "Phone: 9876543210", fontsize=18)
    page.insert_text((60, 240), "Hemoglobin: 13.2 g/dL", fontsize=18)
    original = source.tobytes()
    source.close()

    result = redact_document_for_ai(original, "application/pdf", "Synthetic Patient")
    sanitized = fitz.open(stream=result.data, filetype="pdf")
    try:
        assert result.pages == 1
        assert result.redacted_lines >= 2
        assert result.detected_report_name.casefold() == "synthetic patient"
        assert sanitized.page_count == 1
        assert sanitized[0].get_text().strip() == ""  # raster-only derivative; no original PDF text layer
        assert len(result.data) < 3 * 1024 * 1024
    finally:
        sanitized.close()


def test_unsupported_media_is_blocked_by_redaction_module():
    from privacy_redaction import RedactionError, redact_document_for_ai
    with pytest.raises(RedactionError, match="Only PNG, JPG/JPEG, or PDF"):
        redact_document_for_ai(b"synthetic", "text/plain", "Synthetic Patient")
