# Swastya Assist V10

## Reliability and safety hardening

- One failed remote AI request opens a per-user/session circuit for that feature; the server makes no automatic retry or fallback call after the failure. A new explicit submission resets the feature circuit.
- Gemini 429/5xx/other request failures return a safe reviewer fallback/warning without repeated remote calls.
- OCR/report intake rejects clearly unrelated text locally before spending an AI request. A filename alone never proves a file is medical; image-only/PDF content is checked by the multimodal AI prompt.
- Added assignment/homework/invoice/identity/travel and other unrelated-input checks.
- Voice transcription uses Gemini 3.5 Transcribe with the selected BCP-47 locale and supports automatic language identification. Translation uses a plain-text generation path rather than the triage JSON schema.
- Voice stops after one failed upload/transcription call and does not attempt translation unless transcription succeeded.
- Reviewer decisions for AI-marked `Urgent review` require an explicit human verification checkbox before saving `Reviewed` or `Escalated`; verification is audited.
- Dashboard analytics and case loading remain parallelized.

## Important

The AI is advisory and non-diagnostic. A qualified reviewer remains responsible for the final decision.
