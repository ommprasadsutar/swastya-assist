# Swastya Assist — BPUT PS03 Judge Demo Notes

## What changed in this package
- Added a **Case Readiness Passport** view to the existing clinical console. Existing routes and existing pages were retained.
- Passport checklist measures only whether intake fields are present. It is **not** a medical-risk, diagnosis, or urgency score.
- Added an illustrative privacy-receipt preview, including sample fields, best-effort masking of common identifier patterns, and intentionally withheld categories.
- Added local copy/download controls for the preview-only JSON and a reset-to-sample button; export is disabled unless consent is represented.
- Added an offline/connectivity state demonstration with an in-memory queue. The module explicitly states that it does not make AI calls, persist the demo case, or perform an actual background sync.
- Updated the landing page feature list and preserved the current login, registration, intake, dashboard, OCR, case review, referrals, analytics, RBAC, audit, and admin workflows.

## Suggested live demonstration
1. Sign in with the configured demo reviewer account and open **Readiness Passport**.
2. Edit the synthetic narrative or clear the onset field; show the checklist and intake-completeness percentage update.
3. Toggle **Simulate low connectivity**, then choose **Save to demo queue**. Point out that it remains pending and makes no AI request while offline.
4. Open the privacy receipt and explain that this is a local illustrative preview, not a log of a live Gemini request.
5. Return to the real **Patient intake** or **AI reports / OCR** section for the application's actual prototype workflow. Use synthetic/public sample data only.

## Safety / claims boundary
- No real patient data. No diagnosis, prescription, or treatment decisions. Qualified human review remains required.
- The passport's score is intake completeness only and must never be described as clinical safety or clinical readiness.
- The module is a front-end demonstration; it does not claim that a privacy receipt, local queue or sync transaction is persisted by the backend.
- Real Gemini/OCR and live deployment behavior still depend on the configured runtime and credentials.
