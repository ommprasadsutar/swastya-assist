# Swastya Assist V11.1.7 — Privacy & External AI Gates

## Additive changes
- Preserves existing intake, reports/OCR, review, referral, analytics, administration and Case Readiness Passport workflows.
- Adds a Privacy & AI Gate page in the clinical console.
- Adds best-effort server-side text minimization for likely direct identifiers before text is embedded in Gemini prompts, plus an additional direct-identifier scan of text-extractable PDFs in demo-only mode.
- Requires separate explicit opt-in before raw report image/PDF bytes can be forwarded to Gemini.
- Requires separate explicit opt-in before raw recorded audio can be forwarded to Gemini.
- Adds privacy audit events without recording the source narrative or uploaded file contents in event metadata.
- Mirrors `static/app.js` and `static/style.css` to `public/static/` for deployments that serve the public asset directory.

## Important limitations
- The application does not automatically mask identifiers in image/PDF pixels. When media consent is checked, original media may be sent to Gemini as-is.
- Text minimization is pattern-based and may miss names or other identifying combinations. It is not proof of anonymization.
- The application does not guarantee external-provider retention/deletion behavior, nor certify regulatory compliance. Review provider terms, facility policy, hosting, access controls, encryption, backups and retention before real deployment.
- Keep `DEMO_ONLY_MODE=1` for demonstrations and use synthetic/public sample data only.
- This does not replace a formal privacy impact assessment or legal/security review.

## Configuration
`PRIVACY_GATE_ENABLED=1` is the default. Do not disable it for demos.
