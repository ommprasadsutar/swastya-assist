# V11.1.6 — Case Readiness Passport additions

## Preservation
- Based on the supplied Swastya Assist V11.1.5 reference UI package.
- Existing login, registration, intake, dashboard, OCR/Gemini, case review, contact/referral, analytics, RBAC, admin, audit, retention, and health endpoints were retained.
- No existing server route or database schema was replaced by this showcase update.

## Added to the existing console
- Added the Case Readiness Passport navigation/view for synthetic demo data.
- Completeness score represents presence of intake fields only; it is not a clinical-risk score.
- Added best-effort masking in the local preview for common email, phone, and long numeric ID patterns.
- Added copy and download actions for the illustrative JSON preview, plus reset-to-synthetic-sample action.
- Consent-represented checkbox gates preview export and offline-demo queueing.
- Offline queue remains page-memory demonstration only; it does not call AI, write to the database, or sync.
- Mirrored changed `static/app.js` and `static/style.css` into `public/static/` so Vercel's static asset directory includes the updated UI.

## Important boundary
The preview's text masking is best-effort and is not a production privacy gate or proof of anonymization. The new Passport is a demonstration module. The existing Patient Intake, AI Reports/OCR, and reviewer views continue to use their original configured backend workflows. Use synthetic/public sample data only.
