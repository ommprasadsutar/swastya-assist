> Historical V8 release notes; retained for project history. Current implementation is V10.4.3.

V8.0.1 FINAL PATCH RELEASE

This V8 package includes the complete V8 implementation plus test-suite portability and Gemini media contract corrections.

# Swastya Assist V8

V8 is the laptop-first, Vercel-ready build. It keeps the V7 login and reviewer persistence fixes and updates Gemini integration to the current GenerateContent API.

## Laptop
1. Extract into a clean folder.
2. `python -m pip install -r requirements.txt`
3. `Copy-Item .env.example .env -Force`
4. Set fixed `FLASK_SECRET_KEY`, `LOGIN_CSRF_SECRET`, admin credentials, `COOKIE_SECURE=0`, and a valid `GEMINI_API_KEY`.
5. `python app.py`
6. Open `http://127.0.0.1:5000/login`.

Do not copy an old `triage.db` or `instance/login_csrf_secret.key` for the first V8 test.

## AI
- `gemini-3.8-flash` via GenerateContent API for reviewer packet + image/PDF input.
- `gemini-3.5-transcribe` via GenerateContent API for audio.
- Bounded retry/fallback for transient 429/5xx responses.
- Deterministic reviewer-facing fallback if AI is unavailable.

## Vercel
Set `DATABASE_URL` to managed PostgreSQL, `FLASK_SECRET_KEY`, `LOGIN_CSRF_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DATA_ENCRYPTION_KEY`, `COOKIE_SECURE=1`, `CRON_SECRET`, and a Redis/Upstash `RATELIMIT_STORAGE_URI`. The static bundle is mirrored under `public/static/`.
