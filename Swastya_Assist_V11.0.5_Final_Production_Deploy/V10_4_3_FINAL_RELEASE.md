# Swastya Assist V10.4.4 Final

## Gemini transport fix
The V10.4.1/V10.4.2 logs showed HTTP 400 responses on the Interactions endpoint. The exact provider error body was not captured in those releases, so the historical 400 cannot be attributed to one field with certainty. V10.4.4 removes that fragile transport from the application path and uses Google's documented GenerateContent REST endpoint for `gemini-3.5-flash-lite`, with the minimal standard `contents[].parts[]` request shape.

V10.4.4 therefore uses:
- direct HTTP POST to GenerateContent REST
- `gemini-3.5-flash-lite`
- `/v1beta/models/{model}:generateContent`
- documented `contents[].parts[]` request shape
- `inline_data` for small image, PDF, and audio uploads
- local response parsing from `candidates[].content.parts[].text`
- exactly one provider POST per user AI attempt
- no SDK retry layer
- no fallback model
- no hidden second translation call

## Voice
One audio GenerateContent request returns both transcript and translation JSON. No Files API upload/delete traffic and no second translation API call are used.

## Diagnostics
`diagnose_gemini.py` now tests the same GenerateContent endpoint used by the application, so the diagnostic script cannot silently test a different API path.

## Safety and application controls
Existing consent, non-diagnostic boundary, non-health input rejection, human verification for urgent results, audit logging, one explicit Retry token, frontend duplicate-submit protection, SQLite local/PostgreSQL production boundary, and production security controls remain in place.

## Verification
Release verification checks:
- one `httpx.post()` transport in `app.py`
- no Interactions API transport
- no SDK interaction retries
- no fallback model call
- GenerateContent request contract
- GenerateContent response parser
- inline media builders for audio/image/PDF
- single-retry/idempotency contract
- synced public frontend
