# V11.0.15 — Unified Upload Gate False-Negative Fix

- The Patient Intake and AI reports/OCR upload paths now bypass the early text/filename relevance gate when an actual report file is attached.
- Uploaded PNG/JPEG/PDF content is classified by the shared multimodal healthcare-document gate.
- Short ambiguous token `cv` no longer causes a false non-healthcare rejection.
- Healthcare evidence takes priority over incidental unrelated words in generated context.
- The same healthcare-document and patient-name verification flow remains shared by Patient Intake and standalone OCR.
- No intended change to voice, multilingual, Gemini, timeline, follow-up, risk, reviewer, referral, privacy, facility access, audit, or fallback features.

Verification: focused document-gate regression suite PASS; Python/JS syntax checks PASS. Full Flask/Gemini live integration still requires deployment environment testing.
