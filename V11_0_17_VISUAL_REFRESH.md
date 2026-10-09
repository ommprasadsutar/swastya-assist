# V11.0.17 — Visual Refresh + Small UX Fixes

- Visual-only clinical UI refresh: calmer blue/teal palette, clearer cards, buttons, status states and consistent navigation icons. The existing Swastya Assist logo is unchanged.
- Phone/tablet responsive improvements for intake, dashboard, OCR and voice controls.
- Voice UX: lower audio bitrate for faster uploads, shorter chunk cadence, editable transcript/translation fields, and a short same-device session cache for the current synthetic voice draft.
- Patient Intake and AI Reports/OCR result screens no longer display the raw full report extraction. Verification still happens internally first; the reviewer workspace remains the place to inspect the full report extraction.
- OCR screen removes the manual context textarea from the visible UI; the server-side field remains supported for compatibility and no workflow capability is removed.
- Invalid credentials and role mismatch now return the normal sign-in page with a friendly error instead of a framework/Vercel 401/403 error page.
- No new clinical features, no change to Gemini transport, no change to privacy/contact separation, and no change to safety gates.
