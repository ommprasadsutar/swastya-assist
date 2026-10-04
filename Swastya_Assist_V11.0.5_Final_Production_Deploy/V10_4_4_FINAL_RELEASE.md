# Swastya Assist V10.4.4 — Production Deployment Release

This release is based directly on the uploaded V10.4.3 project and preserves its existing product architecture and safety workflow.

## Production changes
- Gemini configuration is set to `gemini-3.5-flash-lite` for triage, report/OCR, diagnostics, and voice processing.
- One direct GenerateContent REST request per AI attempt; no SDK retry layer and no automatic model fallback.
- Durable database-backed AI request claims prevent duplicate provider attempts across concurrent instances.
- At most one explicit server-issued retry for the same input.
- Voice transcription + translation remain one inline-audio AI interaction.
- Expired sessions can be logged out cleanly instead of producing an authentication error.
- Frontend API 401 responses redirect the user to sign-in with a safe return path.
- Multilingual health relevance detection includes common Indian-language health terms.
- Mobile-responsive patient/reviewer interface and browser voice workflow are retained.
- PostgreSQL is the production database boundary; uploaded report bytes remain database-backed in this release.
- Render deployment descriptor and production Gunicorn/Docker port handling are included.
- Vercel deployment configuration remains included.

## Deployment recommendation
For this Flask application, use **Render Web Service + managed PostgreSQL + managed Redis/Key Value** for the production-style deployment. Render's Flask deployment model runs the application as a normal Gunicorn web service. Vercel remains supported for a hackathon/demo deployment.

Do not use a free sleeping service for a real production workload. Use a paid always-on compute plan and a persistent managed PostgreSQL database for the production launch.

## Required production secrets
Set secrets through the deployment platform, never in the repository:
- `FLASK_SECRET_KEY`
- `LOGIN_CSRF_SECRET`
- `GEMINI_API_KEY`
- `DATABASE_URL`
- `DATA_ENCRYPTION_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `CRON_SECRET`
- `RATELIMIT_STORAGE_URI` or `REDIS_URL`

Recommended:
- `COOKIE_SECURE=1`
- `HEALTH_INPUT_GATE=1`
- `RETENTION_DAYS=30`
- `MAX_UPLOAD_MB=4`
- `GEMINI_FALLBACK_MODELS=`
- `GEMINI_VOICE_FALLBACK_MODEL=`
- `GEMINI_RETRY_ATTEMPTS=1`
- `GEMINI_RETRY_BASE_SECONDS=0`

## Acceptance checks
- `/healthz` returns HTTP 200.
- `/readyz` returns HTTP 200 after production secrets/services are configured.
- Login, role routing, session persistence, API authentication, and logout work.
- Patient intake creates a persistent database case only after valid AI processing.
- AI failures stop processing and expose the controlled retry flow.
- Reviewer verification is required for urgent AI results before Reviewed/Escalated is saved.
- Voice recording, upload, transcription, and translation work on supported HTTPS browsers.
- Report/PDF/image data and metadata persist in PostgreSQL.
- Retention cleanup is protected by `CRON_SECRET`.
