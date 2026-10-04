# Swastya Assist V11.0.6 — deployment guide

## 1. Laptop acceptance

From Windows PowerShell in the extracted project folder:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env -Force
notepad .env
python app.py
```

Open `http://127.0.0.1:5000/login`.

For live AI, set a valid `GEMINI_API_KEY`. Keep `FLASK_SECRET_KEY` and `LOGIN_CSRF_SECRET` fixed across local restarts. Do not copy an old `triage.db` into a clean acceptance run.

## 2. AI acceptance flow

### Triage
- Enter patient data and symptoms.
- Submit once.
- One Gemini provider interaction is attempted.
- Success creates a reviewer queue case.
- Failure stops the chain and exposes one single-use Retry action.
- A failed Retry does not allow a third automatic/provider attempt.

### Voice
- Record in the browser.
- Stop recording.
- One Gemini 3.8 Flash inline-audio interaction is attempted.
- The same interaction returns transcript and translation as structured JSON.
- There is no separate translation interaction.
- One single-use Retry is available for the failed voice chain.

### Reports/OCR
- PNG/JPEG/PDF validation and preview happen locally.
- Clearly unrelated documents are rejected before unnecessary AI processing.
- Medical-looking filenames are never trusted as proof of medical content.
- Gemini multimodal analysis returns structured JSON.
- Invalid structured output is treated as an AI failure and does not create a case.

## 3. Vercel production requirements

Set these environment variables in the Vercel project:

- `DATABASE_URL` — managed PostgreSQL.
- `GEMINI_API_KEY` — valid Gemini API key with available quota/billing.
- `GEMINI_MODEL=gemini-3.5-flash-lite`.
- `GEMINI_TRANSCRIBE_MODEL=gemini-3.5-flash-lite`.
- `FLASK_SECRET_KEY` — strong stable secret.
- `LOGIN_CSRF_SECRET` — strong stable secret.
- `DATA_ENCRYPTION_KEY` — Fernet key.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` — bootstrap administrator for a fresh DB.
- `COOKIE_SECURE=1`.
- `CRON_SECRET` — strong secret for retention cron.
- `RATELIMIT_STORAGE_URI` — managed Redis/Upstash URL; do not use `memory://` in production.
- `RETENTION_DAYS=30` (or your approved retention period).

`/readyz` intentionally reports `503` until the production infrastructure requirements are configured. It does not make a live Gemini request.

## 4. Vercel deployment

Vercel supports Flask as a Python application and can deploy the top-level Flask app. The project includes `vercel.json`, Python 3.14 metadata, mirrored `public/static` assets, and a retention cron.

From the project folder:

```powershell
npm i -g vercel
vercel login
vercel link
vercel deploy --prod
```

After deployment, check:

```text
https://YOUR-DOMAIN/healthz
https://YOUR-DOMAIN/readyz
https://YOUR-DOMAIN/login
```

`/readyz` should return `status: "ready"` after all required production environment variables and managed services are configured.

## 5. Database boundary

Local laptop: SQLite (`triage.db`).

Vercel: managed PostgreSQL through `DATABASE_URL`.

Do not rely on Vercel's function filesystem for durable application data. Report bytes are stored in the database in this release.

## 6. Gemini reliability contract

The model-interaction path does not use the Google GenAI SDK. It sends one direct HTTP POST with httpx, with redirect following disabled and no automatic retry layer. The HTTP timeout is shorter than the Vercel function maximum so the function can return an application response before the platform deadline.

V11.0.6 also does not use automatic model fallback or an alternate provider call. The application may save a clearly labeled manual-review fallback after a triage provider-unavailable failure and issues a server-generated, single-use Retry token. A new patient/report/recording starts a new chain.

Gemini's current GenerateContent API supports standard `contents[].parts[]` input and inline media for multimodal requests. The release deliberately uses the minimal request shape and validates model output locally.

For audio, the release sends small recordings as base64 inline audio data with an explicit MIME type in the same GenerateContent request used for transcription + translation.

## 7. Safety boundary

Swastya Assist is a human-in-the-loop, non-diagnostic triage-support prototype. AI output is reviewer-facing documentation support. It must not independently diagnose or prescribe treatment. Urgent AI results require explicit qualified human verification before `Reviewed` or `Escalated` is saved.
