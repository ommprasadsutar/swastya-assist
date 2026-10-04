# Swastya Assist — final implemented feature checklist

## Patient-to-reviewer workflow
- Patient intake: name, age, gender, facility/location reference, patient reference, language, care scenario, symptoms and consent.
- Voice capture: browser microphone, timer, playback, live browser transcript, source and target language selection.
- AI voice: optional Gemini transcription + translation; browser transcript fallback remains available without the key.
- Reports: PNG/JPG/JPEG/PDF upload with content validation and persistent database storage.
- Local PDF text extraction plus optional Gemini multimodal image/PDF analysis.
- Structured AI output: summary, timeline, key details, missing information, follow-up questions, risk category, urgency signals, evidence/source mapping, report fields and reviewer handoff.
- Deterministic urgency overlay: emergency signals cannot be downgraded by model output.
- Scenario-aware handling for outpatient, occupational health, campus fever, maternal follow-up, chronic disease, public-health camp and referral preparation.
- Reviewer packet: patient context, structured triage note, source traceability and printable human handoff.

## Human review and governance
- Doctor/Reviewer/Admin role checks.
- Human status: Needs review, Reviewed, Escalated, Needs more information.
- Reviewer note and audit event stored with the encounter.
- Admin approval flow for Doctor/Reviewer registration requests.
- Admin create, enable/disable and delete user accounts; self-disable/self-delete blocked.
- Admin synthetic patient encounter deletion, including stored report bytes.
- Audit events for authentication, case creation/viewing, report/packet access, review and admin actions.

## Privacy and security
- CSRF protection on state-changing browser/API actions.
- HttpOnly + SameSite session cookies; Secure cookies enabled by default on Vercel.
- Proxy-aware HTTPS handling.
- CSP, frame denial, referrer, permissions, cross-origin and content-sniffing headers.
- Request body, text and media size limits.
- MIME/content validation for images/PDFs and restricted audio types.
- Optional Fernet encryption for patient name, address, symptoms, report text, reviewer notes and stored reports; required for deployed readiness.
- No public upload-serving route.
- Configurable retention cleanup through an authenticated scheduled endpoint.
- Distributed rate-limit storage option for Redis/Upstash-style deployments.

## India-wide accessibility
- English, Hindi, Bengali, Marathi, Tamil, Telugu, Odia, Kannada, Malayalam, Punjabi, Gujarati, Assamese and Urdu choices.
- Responsive desktop/tablet/mobile workflow.
- Low-connectivity behavior: browser-side voice transcript capture can remain usable without Gemini; AI triage/report analysis intentionally stops and exposes the configured single Retry flow when Gemini is unavailable.

## Deployment
- Standard Flask application compatible with Vercel's Flask runtime.
- PostgreSQL URL normalization for common hosted Postgres connection strings.
- `vercel.json` includes function duration and daily retention cron.
- `/healthz` and `/readyz` probes.
- Docker/Gunicorn local production-style runner remains available.
