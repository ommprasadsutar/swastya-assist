# Swastya Assist V11.0.5 — Final Hardened Release

This package consolidates the V11 hardened workflow and the PostgreSQL compatibility fixes into one release.

## Complete feature set
- Patient intake and synthetic encounter creation
- 13-language Indian accessibility set
- Text symptom/narrative capture
- Browser voice recording, live transcript, optional Gemini transcription/translation, and fallback behavior
- Report upload (PNG/JPG/JPEG/PDF), validation, storage and reviewer access
- Local PDF extraction plus optional Gemini multimodal report understanding
- Structured AI triage summary, timeline, key details, missing information and follow-up questions
- Rules-based urgency overlay with safer negation/history handling
- Strict structured Gemini output validation and prompt/data-boundary protection
- AI failure to manual reviewer fallback
- Reviewer dashboard and prioritized queue
- AI priority separate from final human operational priority
- Reviewer override reason
- Evidence verification: Pending / Verified / Rejected / Unclear
- Follow-up answer persistence and verification
- Insufficient Information workflow
- Facility isolation and facility-scoped access
- Consent metadata: version, timestamp, language and context
- Referral/handoff lifecycle: Draft / Ready / Sent / Acknowledged / Completed
- Printable reviewer packet
- Admin access management and synthetic case data management
- Audit trail and retention controls
- CSRF, secure cookies, security headers, upload validation and rate limiting
- Optional Fernet encryption for sensitive stored text and report bytes
- Health/readiness diagnostics and Gemini diagnostics
- Vercel + Flask + PostgreSQL + SQLite + Docker/Gunicorn deployment support
- PostgreSQL idempotent V10.x -> V11 migration without deleting existing data
- Review UI cache-busting
- Direct `/favicon.ico` route
- Reviewer-controlled urgent patient/caregiver contact using explicit contact consent and client-side `tel:` launch; demo mode uses only the synthetic test number +1-555-010-0100

## Safety boundary
The application is non-diagnostic and does not prescribe or recommend treatment. AI output remains advisory. Patient contact is never initiated automatically by AI; only an authorized human reviewer can initiate it after recording contact consent.
