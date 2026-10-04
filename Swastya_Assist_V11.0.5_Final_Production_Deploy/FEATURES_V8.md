> Historical release notes; retained for project history. Current implementation is V10.4.3.

# Swastya Assist V8 features

- Responsive landing page and role-based sign-in.
- Doctor/Reviewer access requests with Administrator approval.
- Patient narrative intake with Indian language and scenario selectors.
- Browser microphone capture, playback and browser speech recognition.
- Gemini 3.5 Transcribe through the current Interactions API.
- Gemini 3.8 Flash multimodal image/PDF analysis through Interactions API.
- Retry/backoff for transient Gemini 429/5xx responses plus model fallback.
- Deterministic non-diagnostic reviewer-support fallback when AI is unavailable.
- Image/PDF preview, change/choose-new and remove controls.
- Original report persisted in PostgreSQL-compatible database storage, optional Fernet encryption.
- Evidence/source mapping, missing information and follow-up questions.
- Rule-based urgency overlay that prevents emergency keyword downgrade.
- Doctor dashboard queue, filters, refresh and case drawer.
- Human reviewer status/note persistence with save-state and unsaved-change warnings.
- Printable reviewer packet.
- Analytics for total, urgent, reviewed, review rate, risks, statuses, languages and scenarios.
- Admin governance, user enable/disable/delete, registration approvals and synthetic case deletion.
- Audit events for login, case access, reports, packets, creation, review and administration.
- Secure cookies, CSRF, rate limits, security headers and upload validation.
- `/healthz` / `/readyz` and Vercel retention cron.
- Vercel `public/static` asset bundle and Python 3.14 selection.

Safety boundary: reviewer-facing, non-diagnostic prototype; synthetic/public sample data only.
