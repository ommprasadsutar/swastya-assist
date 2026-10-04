# Project status — requirements to implementation

| Source requirement | Implementation in this build |
|---|---|
| Text / voice intake | Patient intake form + browser MediaRecorder + browser speech recognition + optional Gemini transcription/translation |
| Uploaded reports / visual inputs | PNG/JPEG/PDF validation, DB persistence, PDF text extraction, Gemini multimodal analysis |
| Timeline / key details | Structured AI packet; synthetic demo seed uses a deterministic non-AI note only for demo data |
| Missing information | Structured `missing_information` output + reviewer verification wording |
| Follow-up questions | Structured `follow_up_questions` output |
| Translation | Indian language selectors and Gemini translation workflow |
| Risk-category tagging | Rule overlay + AI risk category; emergency signals cannot be downgraded |
| Queue prioritization | API sorting by urgency/status + dashboard risk filter |
| Reviewer dashboard | Queue, case detail drawer, AI packet, evidence, human status/notes |
| Referral preparation | Referral scenario + reviewer handoff + printable reviewer packet |
| Privacy / responsible AI | Synthetic-data disclaimer, consent flag, optional Fernet encryption, retention cleanup, admin deletion, no public upload endpoint |
| Auditability | Audit events for auth, case views, report/packet views, triage creation, reviews and admin actions |
| Role-based access | Admin / Doctor / Reviewer permissions, approval workflow |
| Accessibility / India-wide context | Responsive UI + Indian language and care-scenario choices |
| Deployment | Standard Flask app, PostgreSQL URL support, Vercel config, health/readiness probes |

## Evaluation alignment

The uploaded problem statement weights safety-first triage, information extraction/summarization, multimodal capability, India-wide relevance/accessibility, human review/escalation, privacy/responsible AI and demo quality.

The implementation is deliberately reviewer-facing and non-diagnostic. It does not prescribe treatment or replace qualified staff.


## V11.0.14
Report verification/name visibility fix: clear CBC/lab reports are no longer falsely rejected solely because the model returns a transient non-health classification; patient/report name verification is now shown on Patient Intake results, and mismatch errors show the detected report name without exposing clinical OCR output.
