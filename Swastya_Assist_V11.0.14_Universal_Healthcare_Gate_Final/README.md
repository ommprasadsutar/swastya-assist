# Swastya Assist V11.0.6 — full-stack triage-support prototype

Swastya Assist is a human-in-the-loop healthcare triage-support prototype for government and institutional health settings in India. It is non-diagnostic and reviewer-facing. Use synthetic/public sample data only.

## V11.0.6 implementation (V10.4.4 UI/API preserved)

The project includes responsive landing/login, role-based Doctor/Reviewer/Admin workflows, access requests and approval, patient intake, browser microphone recording and speech recognition, Gemini transcription/translation, PNG/JPEG/PDF report upload with preview/change/remove controls, Gemini multimodal report extraction, local safety gates, urgency signal overlay, evidence/source mapping, queue prioritization, reviewer decision persistence, printable reviewer packets, analytics, audit events, retention cleanup, privacy controls, secure cookies/headers, health/readiness probes, PostgreSQL support, Redis rate-limit support, Docker, and Vercel configuration.

## Laptop first

From the project folder in Windows PowerShell:

```powershell
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
python app.py
```

Use these minimum local `.env` values:

```text
FLASK_SECRET_KEY=local-change-me-keep-fixed
LOGIN_CSRF_SECRET=local-login-change-me-keep-fixed
ADMIN_USERNAME=admin
ADMIN_PASSWORD=AdminPassword12345!
COOKIE_SECURE=0
SEED_DEMO_DATA=1
GEMINI_API_KEY=YOUR_REAL_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TRANSCRIBE_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODELS=
# V11.0.6 preserves the V10.4.4 no-fallback transport policy; keep this blank.
```

Open `http://127.0.0.1:5000/login`. In the AI reports / OCR view, click the Gemini status pill to run the built-in AI connection test. For a clean V11.0.6 laptop test, do not copy an old `triage.db` or `instance/login_csrf_secret.key`; let V11.0.6 create them. Keep the two local secret values fixed across restarts.

## AI transport

V11.0.6 uses the existing Gemini GenerateContent REST API for text, image, PDF and inline-audio workflows. Small voice recordings are processed inline in one `gemini-3.5-flash-lite` GenerateContent API call that returns transcript and translation together. All model calls use direct httpx REST requests, not the Google GenAI SDK, so there is no SDK interaction retry layer. A durable database claim blocks duplicate attempts, including concurrent Vercel instances, and the user gets at most one explicit single-use Retry token for the same input. No automatic model fallback or hidden second provider attempt is used. If Gemini is unavailable during triage, the current intake is saved as a clearly labeled manual-review fallback; no alternate model/provider call is made.

## Vercel deployment readiness

Vercel supports Flask as a Python Function and serves assets from `public/**`. This bundle mirrors `static/**` to `public/static/**`, sets Python 3.14, and includes a daily retention cron. Before production readiness on Vercel, set:

- `DATABASE_URL` to managed PostgreSQL
- `FLASK_SECRET_KEY` and `LOGIN_CSRF_SECRET` to strong random secrets
- `ADMIN_USERNAME` and `ADMIN_PASSWORD`
- `DATA_ENCRYPTION_KEY` to a Fernet key
- `COOKIE_SECURE=1`
- `CRON_SECRET`
- `RATELIMIT_STORAGE_URI` to Redis/Upstash (`redis://` or `rediss://`)
- `GEMINI_API_KEY` plus the model settings if AI is required

`/readyz` is intentionally strict on Vercel: PostgreSQL, secrets, encryption, cron protection, admin bootstrap configuration and a non-memory rate-limit store must be present. AI must be configured for AI features; `/readyz` focuses on infrastructure readiness and does not make a live Gemini request.

## Verification

```powershell
python -m py_compile app.py tests/test_smoke.py tests/test_frontend_contract.py tests/test_v8_contract.py
node --check static/app.js
node --check static/boot.js
node --check static/login.js
node --check static/landing.js
pytest -q
```

The container used to assemble this release does not have the project's Flask/Google Python packages installed, so only syntax/static contract checks can be executed here. Run `pip install -r requirements.txt` and `pytest -q` on the laptop before deployment.

## Safety boundary

The output is advisory documentation for qualified human reviewers. It must not diagnose or prescribe. Before any real patient use, complete applicable privacy/security, clinical validation, identity/MFA, infrastructure, incident-response, backup/restore and legal/regulatory review.

### Optional local admin reset
If a previous local database has the wrong admin password, set `LOCAL_RESET_ADMIN_PASSWORD=1` in `.env` for one local restart. This flag is ignored on Vercel. Set it back to `0` afterward.
