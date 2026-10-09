# Swastya Assist V11.1.8 — Offline Sync + OCR-Assisted Media Redaction

## Additive changes

- Adds an offline capture workspace at `/offline-capture`; the shell is non-personalized and can be cached for offline use. Authenticated pages and API responses are never cached by the service worker.
- Requires a user-chosen passphrase to encrypt local draft content in IndexedDB using AES-GCM with a PBKDF2-derived key. The passphrase is not stored. A lost passphrase means drafts cannot be recovered.
- Adds a manual-review synchronization endpoint (`POST /api/offline-sync`) that accepts text-only drafts, requires a clinical/admin login and CSRF validation, performs no AI calls, creates `Needs review` cases, and uses unique client IDs for idempotency.
- A confirmed sync purges the encrypted draft payload from the browser, retaining only a minimal sync receipt. Network restoration triggers a sync attempt only while the queue is unlocked; a Sync button is also provided.
- Adds OCR-assisted masking of likely identifier lines in image/PDF derivatives before Gemini processing. PDF pages are rasterized and rebuilt without the original text layer/metadata. The original is retained under the configured case-storage policy for authorized reviewers.
- Redaction fails closed if OCR fails, the document has more than 10 pages, the report name cannot be locally matched, or output cannot be safely built. The raw source file is never the media attachment sent to Gemini by this route.
- Adds focused tests for line masking, flattened PDF output, offline sync contracts, route protections, and cache boundaries.

## Important constraints

- OCR/pattern-based masking can miss identifiers. This is a best-effort control, not guaranteed anonymization. Use synthetic/public data for the educational demo.
- Local browser encryption helps protect data at rest, but it is not a substitute for managed devices, secure local accounts, HTTPS, server-side encryption, backups/retention controls, or security review.
- The offline queue intentionally stores text only; it does not queue reports or audio. It creates a manual-review case and never invents an AI result while offline.
- Automatic sync requires the offline page to remain open and unlocked when connectivity returns; if the session expires, sign in again and retry.
- In non-demo deployment, offline sync requires `DATA_ENCRYPTION_KEY` to be configured. `DEMO_ONLY_MODE=1` remains recommended for demonstrations.
- Docker installs the Tesseract binary. A platform deployment that does not provide Tesseract will fail closed and block media transfer until OCR is installed.
- No claim of clinical validation, zero external-provider retention, or regulatory certification is made.

## Setup

Install Python requirements. For OCR-assisted redaction, install the system Tesseract OCR executable (the included Dockerfile does this). Run `python app.py`, sign in with a clinical/reviewer account, and open the Offline capture & sync link. Visit it once online before relying on its offline shell.
