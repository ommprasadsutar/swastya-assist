> Historical V8 release notes; retained for project history. Current implementation is V10.4.3.

# Swastya Assist V8.0.0 final release

Laptop-first and Vercel-ready release. Test the complete workflow locally before deployment.

## Included
- Flask full-stack application and role-based access
- Stable local login CSRF/session secrets
- Patient intake with browser microphone, browser transcript, Gemini transcription and translation
- PNG/JPEG/PDF upload with preview, change and remove controls
- Gemini multimodal report extraction and deterministic reviewer-safe fallback
- Doctor/reviewer queue, case drawer, review status/note persistence and print packet
- Analytics and governance/admin workflows
- Audit events, encrypted sensitive DB fields when `DATA_ENCRYPTION_KEY` is set, retention cleanup
- PostgreSQL/Redis production settings and Vercel cron/readiness configuration
- Current Gemini Interactions API request format with structured JSON response schema
- Current public static asset bundle for Vercel

## Local test
1. `python -m pip install -r requirements.txt`
2. `Copy-Item .env.example .env -Force`
3. Set fixed `FLASK_SECRET_KEY`, `LOGIN_CSRF_SECRET`, `COOKIE_SECURE=0`, admin credentials, and `GEMINI_API_KEY`.
4. `python app.py`
5. Open `http://127.0.0.1:5000/login`.
6. Complete the acceptance checklist in `V8_FINAL_CHECKLIST.md`.

## Vercel
Use managed PostgreSQL, Redis/Upstash, stable production secrets, `COOKIE_SECURE=1`, `CRON_SECRET`, and the Gemini key/model settings. `/readyz` is intentionally strict for those production requirements.
