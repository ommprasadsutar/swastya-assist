# Swastya Assist V11.0.5 — Final Release Notes

This is the consolidated final package for the Swastya Assist prototype.

## Release status
- Version: 11.0.5
- Python compile check: PASS
- JavaScript syntax check: PASS
- Release verifier: PASS
- V11 security/frontend/Gemini/V10/V8 contract tests: PASS
- Total targeted contract tests: 32 passed
- `public/static` synchronized with `static`

## Included corrections from earlier deployments
- Existing PostgreSQL databases can receive V11 columns without deleting existing data.
- PostgreSQL encrypted reviewer/referral columns use TEXT, matching the EncryptedText implementation.
- Review UI assets use a new cache version so updated reviewer controls are loaded.
- Urgent human verification is enforced for both AI-urgent cases and reviewer-upgraded urgent cases.
- Escalated cases require an active referral/handoff status and destination.
- Urgent contact is human-controlled, consent-gated and never AI-initiated.
- Favicon route prevents the `/favicon.ico` 404 noise.
- SQLite migration includes the same urgent-contact fields.

## Demo contact behavior
Demo mode stays synthetic-only. The contact feature uses the fictional test number `+1-555-010-0100`; production deployments should disable demo-only mode and apply the facility's approved privacy/contact policy before collecting real numbers.

## Deployment
Deploy the project contents from this package to the GitHub/Vercel project. Keep the existing PostgreSQL database and do not delete it for the migration.
