# V11.0.16 — Verification-First Report UI

- Shared Patient Intake and AI Reports/OCR upload verification remains authoritative on the server.
- Healthcare-document classification and patient-name extraction happen internally before any report/OCR/triage response is exposed.
- On success, the UI shows a clear `VERIFIED` status first; report patient name, OCR sections, measurements and full extraction are displayed only after that verified status.
- On failure, the UI shows `NOT VERIFIED` and the applicable reason; no extraction or triage output is exposed.
- Applies identically to Patient Intake uploads and standalone AI Reports/OCR uploads.
- Existing Gemini, voice, multilingual, risk, follow-up, reviewer, referral, privacy, facility, audit, fallback and deployment features are intentionally unchanged.
