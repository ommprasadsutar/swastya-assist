# V11.1.8 validation report

## Scope

- Existing Swastya Assist Flask application preserved.
- Added encrypted, text-only offline capture using browser IndexedDB and a passphrase-derived AES-GCM key.
- Added authenticated, CSRF-protected, facility-scoped, idempotent `POST /api/offline-sync`; it creates `Needs review` cases and does not call Gemini.
- Added OCR-assisted, fail-closed redaction for supported image/PDF content before externally consented AI media processing.
- Updated static asset mirrors (`static/` to `public/static/`) and deployment/CI documentation.
- Updated BPUT presentation to describe current behavior conservatively and retain the Team ID supplied by the user.

## Checks passed in the packaging environment

- `pytest -q --ignore=tests/test_smoke.py --tb=short`: **123 passed** after updating the stale Python-version contract test to match Python 3.13.5.
- `python -m compileall -q app.py privacy_redaction.py tests`: passed.
- JavaScript syntax via `node --check` for `static/app.js`, `boot.js`, `login.js`, `landing.js`, `offline_capture.js`, `sw.js`: passed.
- Source/public static mirrors: 14 files checked; 0 mismatches.
- OCR test coverage uses synthetic text in images and a synthetic flattened PDF; tests include blocking unsupported media and failed privacy checks.
- Updated Flask integration smoke tests now assert unreadable media fails closed before a Gemini call and that offline sync is authenticated, idempotent, review-only, and performs no AI call. These new Flask integration assertions are included in CI but could not be executed locally because Flask dependencies are unavailable.
- PowerPoint export re-opened with `python-pptx`: **10 slides**.
- PDF export checked with `pdfinfo`: **10 pages**; page 4 visually reviewed after the final retention wording correction.
- ZIP/source hygiene checked for `.env`, local databases, private keys, and upload files before packaging.

## Checks not completed here

- Full `pytest -q` / Flask end-to-end suite: the packaging environment did not have Flask, Flask-SQLAlchemy, or Flask-Limiter installed. Package-index DNS/network access failed, so those dependencies could not be installed locally. The full test job is configured in `.github/workflows/ci.yml` to install `requirements.txt`, install Tesseract, and run the complete suite on GitHub Actions; a successful CI run has not yet been observed.
- Live Gemini request, live voice/microphone test, live persistent PostgreSQL/Redis configuration, managed host build, `/readyz` production readiness, and actual deployment were not performed.
- No real health data was used in tests.

## Operational limitations

- OCR/pattern redaction is best-effort; do not claim perfect anonymization.
- Browser-offline capture is limited to encrypted text drafts. Media, raw audio, and AI outputs are not stored by this offline queue.
- Successful offline sync creates `Needs review`; it does not invoke Gemini.
- The Case Readiness Passport remains a synthetic/local demo, not a diagnosis, medical risk score, or proof of deployment.
- Do not process real patient data until privacy/security, clinical, operational, and regulatory reviews are completed.
