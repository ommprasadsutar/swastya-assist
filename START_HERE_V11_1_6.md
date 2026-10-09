# Swastya Assist V11.1.6 — Start Here

This is an additive update to the existing Swastya Assist application. Existing app routes and workflows have been retained.

## Run locally (Windows PowerShell)

1. Extract this ZIP.
2. Open the extracted `swastya_v114_work` folder in PowerShell.
3. Install packages:

```powershell
python -m pip install -r requirements.txt
```

4. Create the local environment file if not present:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

5. For local demo only, set fixed local secrets, `COOKIE_SECURE=0`, and use synthetic/public sample data. Set a real `GEMINI_API_KEY` only if you want to test existing Gemini-supported paths. Never commit `.env` or place API keys into frontend files.
6. Start the app:

```powershell
python app.py
```

7. Open `http://127.0.0.1:5000/login`. Navigate to the Clinical Console and choose **Readiness Passport**.

## New additions

- Case Readiness Passport inside the existing console.
- Intake-completeness checklist (not a clinical-risk score).
- Illustrative privacy preview, best-effort masking, JSON copy/download and reset controls.
- Offline state and pending queue simulation.
- Landing page feature-card addition.
- Updated static asset cache keys and Vercel public/static mirrors.

## What the new Passport does not do

The Passport showcase is local-only and synthetic-data-only. It makes no AI/API call, writes no case to the database, and does not perform real offline sync. Its masking is not a production privacy gate or proof of anonymization. Use the existing Patient Intake, AI Reports/OCR, and reviewer workflow for the application's pre-existing backend-backed prototype features.

## Checks

The added source-contract tests are in `tests/test_v11_16_case_readiness_passport.py`. Install requirements before running the complete pytest suite.
