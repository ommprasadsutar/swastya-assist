"""Fail-closed, OCR-assisted pixel redaction for small healthcare demo uploads.

This module creates a flattened, redacted copy for external AI. It does not modify
or replace the source document saved under the application's storage policy.
OCR and pattern matching can miss identifiers; the caller must retain explicit consent
and display that residual-risk warning. If OCR cannot inspect all pages, no AI copy is returned.
"""
from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

MAX_PAGES = 10
MAX_SIDE = 2600
OCR_TIMEOUT_SECONDS = 12

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_AADHAAR_RE = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I)
_PHONE_RE = re.compile(r"(?<!\w)\+?\d(?:[\s().-]*\d){8,14}(?!\w)")
_LABEL_RE = re.compile(
    r"^\s*(?:patient\s*name|name\s+of\s+patient|full\s*name|name|patient|"
    r"mobile|phone|telephone|e-?mail|address|aadhaar|aadhar|pan|mrn|"
    r"medical\s*record(?:\s*(?:number|no))?|patient\s*(?:id|identifier)|"
    r"date\s*of\s*birth|dob)\b\s*[:#\-]", re.I
)
_NAME_LABEL_VALUE_RE = re.compile(
    r"^\s*(?:patient\s*name|name\s+of\s+patient|full\s*name|name|patient)\b\s*[:#\-]\s*(.+)$", re.I
)

class RedactionError(ValueError):
    """Raised when a trustworthy redacted media copy cannot be produced."""

@dataclass(frozen=True)
class RedactionResult:
    data: bytes
    mime_type: str
    redacted_lines: int
    pages: int
    detected_report_name: str


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)).strip()


def _line_groups(ocr: dict) -> list[dict]:
    groups: dict[tuple, list[int]] = {}
    n = len(ocr.get("text", []))
    for i in range(n):
        word = str(ocr["text"][i] or "").strip()
        if not word:
            continue
        key = (ocr.get("block_num", [0] * n)[i], ocr.get("par_num", [0] * n)[i], ocr.get("line_num", [0] * n)[i])
        groups.setdefault(key, []).append(i)
    output = []
    for indexes in groups.values():
        words = [str(ocr["text"][i]).strip() for i in indexes if str(ocr["text"][i]).strip()]
        if not words:
            continue
        left = min(int(ocr["left"][i]) for i in indexes)
        top = min(int(ocr["top"][i]) for i in indexes)
        right = max(int(ocr["left"][i]) + int(ocr["width"][i]) for i in indexes)
        bottom = max(int(ocr["top"][i]) + int(ocr["height"][i]) for i in indexes)
        output.append({"text": " ".join(words), "box": (left, top, right, bottom)})
    output.sort(key=lambda x: (x["box"][1], x["box"][0]))
    return output


def _is_identifier_line(text: str, known_name: str) -> bool:
    if _LABEL_RE.search(text) or _EMAIL_RE.search(text) or _AADHAAR_RE.search(text) or _PAN_RE.search(text):
        return True
    for match in _PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 10 <= len(digits) <= 15:
            return True
    name = _normalize(known_name)
    if len(name) >= 3 and re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", _normalize(text)):
        return True
    return False


def _extract_report_name(lines: list[dict], known_name: str) -> str:
    for line in lines:
        match = _NAME_LABEL_VALUE_RE.search(line["text"])
        if match:
            candidate = match.group(1).strip(" ,;|-")
            # Trim common same-line fields after the name value.
            candidate = re.split(r"\s+(?:age|sex|gender|dob|date of birth|patient id)\s*[:#\-]", candidate, maxsplit=1, flags=re.I)[0].strip(" ,;|-")
            if candidate:
                return candidate[:160]
    known = str(known_name or "").strip()
    if known and any(_normalize(known) and re.search(r"(?<!\w)" + re.escape(_normalize(known)) + r"(?!\w)", _normalize(line["text"])) for line in lines):
        return known
    return ""


def _ocr_and_mask(image: Image.Image, known_name: str) -> tuple[Image.Image, int, str]:
    try:
        import pytesseract
        ocr = pytesseract.image_to_data(
            image.convert("RGB"),
            output_type=pytesseract.Output.DICT,
            config="--psm 6",
            timeout=OCR_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        raise RedactionError("Local OCR could not inspect this file. The file was not sent to external AI.") from exc
    lines = _line_groups(ocr)
    if not lines:
        raise RedactionError("No readable text was detected for privacy inspection. The file was not sent to external AI.")
    output = image.convert("RGB").copy()
    draw = ImageDraw.Draw(output)
    redacted = 0
    width, height = output.size
    # Black-out the full OCR line with padding so adjacent characters/diacritics are covered.
    for line in lines:
        if not _is_identifier_line(line["text"], known_name):
            continue
        left, top, right, bottom = line["box"]
        pad_x = max(5, int((right - left) * 0.04))
        pad_y = max(4, int((bottom - top) * 0.25))
        draw.rectangle((max(0, left - pad_x), max(0, top - pad_y), min(width, right + pad_x), min(height, bottom + pad_y)), fill=(0, 0, 0))
        redacted += 1
    report_name = _extract_report_name(lines, known_name)
    return output, redacted, report_name


def redact_document_for_ai(data: bytes, mime_type: str, known_name: str = "") -> RedactionResult:
    """Return only a flattened, OCR-inspected copy suitable for external AI transfer.

    Supported input MIME types are image/png, image/jpeg, and application/pdf.
    PDF source text layers, metadata, and hidden content are not copied into the output;
    each PDF page is rasterized and rebuilt from the inspected image.
    """
    if not data:
        raise RedactionError("The uploaded file is empty. No file was sent to external AI.")
    if mime_type in {"image/png", "image/jpeg"}:
        try:
            source = Image.open(io.BytesIO(data))
            source.verify()
            source = Image.open(io.BytesIO(data))
            source = ImageOps.exif_transpose(source).convert("RGB")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise RedactionError("The image could not be safely decoded. No file was sent to external AI.") from exc
        source.thumbnail((MAX_SIDE, MAX_SIDE))
        redacted_image, redacted_lines, detected_name = _ocr_and_mask(source, known_name)
        out = io.BytesIO()
        redacted_image.save(out, format="JPEG", quality=86, optimize=True, progressive=False)
        return RedactionResult(out.getvalue(), "image/jpeg", redacted_lines, 1, detected_name)

    if mime_type != "application/pdf":
        raise RedactionError("Only PNG, JPG/JPEG, or PDF can use the privacy redaction pipeline. No file was sent to external AI.")
    try:
        import fitz
        pdf = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise RedactionError("The PDF could not be safely opened. No file was sent to external AI.") from exc
    if pdf.page_count < 1 or pdf.page_count > MAX_PAGES:
        pdf.close()
        raise RedactionError(f"PDF redaction supports 1–{MAX_PAGES} pages per request. No file was sent to external AI.")

    pdf_page_count = pdf.page_count
    sanitized = fitz.open()
    total_redacted = 0
    report_name = ""
    try:
        for page_index in range(pdf.page_count):
            page = pdf.load_page(page_index)
            # Render at ~160 dpi for readable OCR with bounded pixel count.
            pix = page.get_pixmap(matrix=fitz.Matrix(160 / 72, 160 / 72), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.thumbnail((MAX_SIDE, MAX_SIDE))
            masked, n, name = _ocr_and_mask(img, known_name)
            total_redacted += n
            if not report_name and name:
                report_name = name
            jpeg = io.BytesIO()
            masked.save(jpeg, format="JPEG", quality=82, optimize=True)
            rect = fitz.Rect(0, 0, page.rect.width, page.rect.height)
            out_page = sanitized.new_page(width=rect.width, height=rect.height)
            out_page.insert_image(rect, stream=jpeg.getvalue())
        out = sanitized.tobytes(garbage=4, deflate=True, clean=True)
    except RedactionError:
        sanitized.close()
        pdf.close()
        raise
    except Exception as exc:
        sanitized.close()
        pdf.close()
        raise RedactionError("The PDF redaction pass failed. The original was not sent to external AI.") from exc
    sanitized.close()
    pdf.close()
    if not out or len(out) > 3 * 1024 * 1024:
        raise RedactionError("The redacted PDF exceeds the safe transfer size. The file was not sent to external AI.")
    return RedactionResult(out, "application/pdf", total_redacted, pdf_page_count, report_name)
