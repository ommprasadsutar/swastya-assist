# Swastya Assist V11.1.8 — Start Here

## Run locally

1. Extract the ZIP.
2. Install Python from the version used by your deployment.
3. Install the OS-level Tesseract OCR package. For Docker, the included Dockerfile installs `tesseract-ocr`.
4. Create `.env` from `.env.example`. Keep `DEMO_ONLY_MODE=1` for the hackathon demo. Keep `PRIVACY_GATE_ENABLED=1`.
5. Install dependencies: `python -m pip install -r requirements.txt`.
6. Start: `python app.py`.
7. Sign in with an authorized clinical/reviewer account and select **Offline capture & sync**.
8. Open that page online once so its generic shell can be cached. Create a passphrase of at least 12 characters. Drafts are encrypted in this browser.

## Offline capture behavior

- Only text fields are queued; no image, PDF, raw audio, or AI response is stored by this queue.
- The local queue is encrypted using AES-GCM and a key derived from the passphrase. Do not forget the passphrase.
- After reconnect, the page attempts sync while unlocked. Manual sync is also available. A server-created case remains `Needs review`; no Gemini request is made by the sync endpoint.
- Idempotency receipts prevent duplicate cases when a synchronization request is repeated. Successful synchronization deletes the local encrypted payload and retains a minimal receipt.
- If the session is expired, sign in again in the main app and retry synchronization.

## Media redaction behavior

- A separate unchecked-by-default consent is still required before external AI processing.
- Local Tesseract OCR inspects every page/image and masks complete lines that look like identifiers or match the intake name. PDFs are flattened and rebuilt before external transfer.
- If OCR cannot inspect a page or the report name does not match, the upload is blocked. The source file is not attached to Gemini by the updated triage route.
- OCR redaction can miss text, so it is not guaranteed anonymization. Use synthetic/public data only in the educational demo.

## Deployment note

The default native Python deployment configuration may not install the OS Tesseract binary. OCR-backed media transfer will fail closed unless the binary is available. The included Dockerfile installs it. Configure `DATA_ENCRYPTION_KEY`, `FLASK_SECRET_KEY`, HTTPS/cookies, database persistence, rate-limit storage, backups and retention before any real-world use. Never use real patient data in a hackathon demo.
