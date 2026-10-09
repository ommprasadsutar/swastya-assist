# Swastya Assist V11.1.8 — full-stack triage-support prototype

Swastya Assist is a human-in-the-loop healthcare triage-support prototype for government and institutional health settings in India. It is non-diagnostic and reviewer-facing. Use synthetic/public sample data only.

## Existing implementation preserved (V10.4.4 UI/API base)

The project includes responsive landing/login, role-based Clinical team/Admin workflows, access requests and approval, patient intake, browser microphone recording and speech recognition, Gemini transcription/translation, PNG/JPEG/PDF report upload with preview/change/remove controls, Gemini multimodal report extraction, local safety gates, urgency signal overlay, evidence/source mapping, queue prioritization, reviewer decision persistence, printable reviewer packets, analytics, audit events, retention cleanup, privacy controls, secure cookies/headers, health/readiness probes, PostgreSQL support, Redis rate-limit support, Docker, and Vercel configuration.

## V11.1.6 — Case Readiness Passport demonstration

The existing application has been preserved and extended with a local-only **Case Readiness Passport** showcase in the Clinical Console. It demonstrates intake-field completeness, an illustrative minimized privacy preview, copy/download of preview-only JSON, and an offline/pending state simulation. The module is synthetic-data-only and intentionally does not call Gemini, write to the database, or perform network synchronization. It is not a clinical risk score and not a production privacy gate.

The updated `static/app.js` and `static/style.css` are mirrored to `public/static/` for deployment static-asset delivery. See `V11_1_6_CASE_READINESS_PASSPORT.md` for the exact scope; this Passport remains a local synthetic-data demonstration.

## V11.1.7 — Privacy & AI Gate

Text sent for AI processing is minimized on a best-effort basis. Report media and raw audio require separate explicit consent before external AI processing. Never assume this guarantees anonymization or controls retention by the external AI provider.

## V11.1.8 — Offline text capture and OCR-assisted media redaction

- `/offline-capture` stores text-only drafts in browser IndexedDB, encrypted with AES-GCM using a passphrase-derived key. The passphrase is not stored; forgotten passphrases cannot be recovered.
- `POST /api/offline-sync` is authenticated, CSRF-protected, facility-scoped and idempotent. It creates `Needs review` cases, does not call Gemini, and accepts no media or audio.
- The service worker caches only the generic offline capture shell and its assets; it does not cache authenticated pages, API responses, reports, or AI output.
- Before report media is sent to Gemini, local Tesseract OCR masks likely identifier lines and the derivative is flattened/rebuilt. OCR failure, unsupported files, excessive PDF pages, or unverified report-name matching blocks the transfer. A separate explicit consent remains required.
- OCR/pattern redaction can miss identifiers. This is a best-effort safeguard, not guaranteed anonymization. Use synthetic/public samples in the educational prototype.
- For non-demo deployment, offline sync requires a persistent database and `DATA_ENCRYPTION_KEY`; media processing requires system Tesseract. The included Dockerfile installs Tesseract.

See `V11_1_8_OFFLINE_SYNC_AND_DOCUMENT_REDACTION.md` and `START_HERE_V11_1_8.md` for the behavior and limits.

## Laptop first

From the project folder in Windows PowerShell:

```powershell
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
python app.py
```

For a local synthetic-data demo, start with `.env.example`, keep `DEMO_ONLY_MODE=1` and `PRIVACY_GATE_ENABLED=1`, and replace the example secrets before use. Generate a persistent local Flask secret with `python -c "import secrets; print(secrets.token_hex(32))"`; generate the data-encryption key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Use these variable names in `.env`:

```text
FLASK_SECRET_KEY=PASTE_GENERATED_RANDOM_SECRET
LOGIN_CSRF_SECRET=PASTE_DIFFERENT_RANDOM_SECRET
ADMIN_USERNAME=admin
ADMIN_PASSWORD=REPLACE_WITH_A_STRONG_UNIQUE_PASSWORD
DATA_ENCRYPTION_KEY=PASTE_GENERATED_FERNET_KEY
DEMO_ONLY_MODE=1
PRIVACY_GATE_ENABLED=1
COOKIE_SECURE=0
SEED_DEMO_DATA=1
GEMINI_API_KEY=YOUR_REAL_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TRANSCRIBE_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODELS=
# Keep fallback model settings blank unless intentionally configured.
```

Open `http://127.0.0.1:5000/login`. In the AI reports / OCR view, click the Gemini status pill to run the built-in AI connection test. For a clean test, do not copy an old `triage.db` or `instance/login_csrf_secret.key`; let the application create runtime files. Keep your own generated local secrets fixed across restarts.

## AI transport

The existing Gemini integration uses the GenerateContent REST API for text, image, PDF and inline-audio workflows. Small voice recordings are processed inline in one `gemini-3.5-flash-lite` GenerateContent API call that returns transcript and translation together. All model calls use direct httpx REST requests, not the Google GenAI SDK, so there is no SDK interaction retry layer. A durable database claim blocks duplicate attempts, including concurrent Vercel instances, and the user gets at most one explicit single-use Retry token for the same input. No automatic model fallback or hidden second provider attempt is used. If Gemini is unavailable during triage, the current intake is saved as a clearly labeled manual-review fallback; no alternate model/provider call is made.

## Deployment readiness

The included Render Blueprint uses the Dockerfile so the deployment has system Tesseract for the privacy redaction path. Configure a persistent managed PostgreSQL database and all required secrets in the hosting dashboard; do not rely on an ephemeral local SQLite file for a live deployment.

Vercel configuration is also included and serves assets from `public/**`, but the standard Python function runtime may not provide system Tesseract. In that case media redaction fails closed and external media processing is blocked. Choose a Docker-capable host for end-to-end OCR-assisted media redaction. The bundle mirrors `static/**` to `public/static/**` and includes a daily retention cron. Before production readiness on Vercel, set:

- `DATABASE_URL` to managed PostgreSQL
- `FLASK_SECRET_KEY` and `LOGIN_CSRF_SECRET` to strong random secrets
- `ADMIN_USERNAME` and `ADMIN_PASSWORD`
- `DATA_ENCRYPTION_KEY` to a Fernet key
- `COOKIE_SECURE=1`
- `CRON_SECRET`
- `RATELIMIT_STORAGE_URI` to Redis/Upstash (`redis://` or `rediss://`)
- `GEMINI_API_KEY` plus the model settings if AI is required

`/readyz` is intentionally strict on Vercel: PostgreSQL, secrets, encryption, cron protection, admin bootstrap configuration and a non-memory rate-limit store must be present. AI must be configured for AI features; `/readyz` focuses on infrastructure readiness and does not make a live Gemini request.

## GitHub and release checks

See `GITHUB_PUSH_GUIDE.md` for repository hygiene, push commands, required deployment secrets, Render Docker deployment, and smoke-test steps. See `V11_1_8_VALIDATION_REPORT.md` for the exact checks completed and the integration tests still blocked in the packaging environment. The `.github/workflows/ci.yml` workflow runs on GitHub after push.

## Verification

```powershell
python -m compileall -q app.py privacy_redaction.py tests
node --check static/app.js
node --check static/boot.js
node --check static/login.js
node --check static/landing.js
node --check static/offline_capture.js
node --check static/sw.js
pytest -q
```

The packaging environment used for this handoff could not reach the package index and did not have Flask installed. Static/contract and OCR-redaction checks were run locally; the full Flask integration suite must still be run after `python -m pip install -r requirements.txt`. A GitHub Actions workflow at `.github/workflows/ci.yml` installs Tesseract and dependencies and runs the full suite on push and pull request.

## Safety boundary

The output is advisory documentation for qualified human reviewers. It must not diagnose or prescribe. Before any real patient use, complete applicable privacy/security, clinical validation, identity/MFA, infrastructure, incident-response, backup/restore and legal/regulatory review.

### Optional local admin reset
If a previous local database has the wrong admin password, set `LOCAL_RESET_ADMIN_PASSWORD=1` in `.env` for one local restart. This flag is ignored on Vercel. Set it back to `0` afterward.


Privacy update V11.1.7 adds a default-on Privacy & AI Gate, best-effort free-text minimization, and separate explicit consent for sending raw report media or audio to Gemini. See `V11_1_7_PRIVACY_GATE.md` for limitations.
