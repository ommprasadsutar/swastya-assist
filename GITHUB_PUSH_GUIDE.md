# GitHub push and deployment guide — Swastya Assist V11.1.8

This repository contains the existing Swastya Assist Flask application plus V11.1.8 offline text capture and OCR-assisted report redaction. Review `README.md`, `START_HERE_V11_1_8.md`, and `V11_1_8_OFFLINE_SYNC_AND_DOCUMENT_REDACTION.md` before deployment.

## 1. Before you push

- Do **not** add `.env`, `triage.db`, uploaded patient files, credentials, API keys, private certificates, or real patient data.
- Keep `.env.example` as a placeholder template only. Generate your own secrets locally and in the host's secret/environment settings.
- Use synthetic/public examples only. Do not put health records in GitHub issues, screenshots, logs, or commit history.
- Review `git status --short` and `git diff --cached --stat` before every push.

## 2. Create a GitHub repository

1. On GitHub, create an empty repository, e.g. `swastya-assist` (no README/license is easiest for first push).
2. Extract this source ZIP to a folder.
3. Open a terminal in that folder (the folder containing `app.py`).

If the folder is not already a Git repository, run:

```bash
git init
git branch -M main
git add .
git status --short
```

Confirm that `.env`, databases, uploads, generated PPTX/PDFs, and secrets are **not** listed. Then commit:

```bash
git commit -m "Swastya Assist V11.1.8 privacy and offline sync"
```

If Git asks you to configure an identity, use your own name/email:

```bash
git config user.name "Your Name"
git config user.email "your-verified-email@example.com"
```

Add your actual repository URL and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Use GitHub's browser sign-in / Git Credential Manager for authentication. **Never paste a personal access token into source code, a command saved in shell history, or `.env.example`.** If you already have `origin`, inspect `git remote -v` and `git status` first; do not overwrite an existing repository blindly.

## 3. Configure deployment secrets

The included `Dockerfile` installs Tesseract so the OCR-assisted media-redaction path can run. The included `render.yaml` selects the Docker runtime. For a persistent hosted app, configure these in the host dashboard (values are different for every deployment):

- `FLASK_SECRET_KEY`: unique, random secret.
- `LOGIN_CSRF_SECRET`: separate unique, random secret.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD`: non-default credentials.
- `DATABASE_URL`: persistent managed PostgreSQL URL; do not use ephemeral filesystem SQLite as a production database.
- `DATA_ENCRYPTION_KEY`: valid Fernet key, stored only as a secret.
- `COOKIE_SECURE=1` behind HTTPS.
- `GEMINI_API_KEY` if Gemini-backed features are enabled.
- `RATELIMIT_STORAGE_URI`: managed Redis/Upstash URL for shared rate-limiting when required by the deployment readiness checks.
- `CRON_SECRET` if the configured retention endpoint/cron is enabled.
- `DEMO_ONLY_MODE=0` only after setting the required secure configuration and reviewing the production controls.

Never commit real values in the repository. Enable persistent storage/managed database backups and verify restore and retention behavior before any real-world use.

## 4. Deploy on Render using Docker

1. Push the repository to GitHub.
2. In Render, create a Blueprint from the repository, or create a Docker web service using the repository root.
3. Let Render build the included `Dockerfile`; this installs system Tesseract.
4. Provision managed PostgreSQL and configure the secrets above in Render's environment settings.
5. Deploy and inspect build/runtime logs.
6. Check `/healthz` for liveness and `/readyz` for readiness after required variables/services are configured.
7. Test sign-in, role isolation, one synthetic intake, PDF/image redaction fail-closed behavior, offline text capture/sync, duplicate retries, and the reviewer handoff.

Do not route real patient data through the app until a qualified review of privacy, security, backup/restore, clinical workflow, compliance, and incident response is complete.

## 5. Run locally first

```bash
python -m pip install -r requirements.txt
# Windows PowerShell:
if (!(Test-Path .env)) { Copy-Item .env.example .env }
python app.py
```

Install the Tesseract OCR binary on your OS. See `START_HERE_V11_1_8.md` for more detailed steps and limitations. For local synthetic demo testing, keep `DEMO_ONLY_MODE=1` and `PRIVACY_GATE_ENABLED=1`.

## 6. What has not been represented as complete

- OCR redaction is best-effort and can miss identifiers. OCR errors or unsupported files should fail closed; that is not a guarantee of anonymization.
- Offline sync only carries encrypted text-only drafts and creates `Needs review` cases; it does not send media/audio or invoke AI.
- The Case Readiness Passport is a synthetic/local demo, not a clinical risk score.
- The full Flask integration suite must be run in an environment where all dependencies install successfully. Local packaging validation does not equal production validation.
