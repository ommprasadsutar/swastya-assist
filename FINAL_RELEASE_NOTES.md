# Swastya Assist V11.1.6 — BPUT PS03 showcase additions

This package preserves the existing Swastya Assist website and adds a Case Readiness Passport showcase to the existing clinical console. No core application routes were removed or replaced.

- Retained patient intake, dashboard/queue, AI reports/OCR, case review, contact/referral, analytics, admin, RBAC, access requests, audit and retention workflows from the source package.
- Added local synthetic-only completeness checklist and privacy preview.
- Added preview JSON copy/download and reset controls.
- Added consent gating to preview export and offline-demo queueing.
- Mirrored frontend assets to `public/static/` for deployment consistency.
- Added source-contract tests.

The Case Readiness Passport remains demonstration-only: it has no backend persistence, no real network sync and no Gemini call. It does not diagnose, prescribe or assign clinical priority. Use synthetic/public sample data only.
