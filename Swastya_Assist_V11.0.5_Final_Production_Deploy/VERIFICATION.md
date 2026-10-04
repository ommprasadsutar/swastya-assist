# V4 verification

- Fixed the shared DOM helper bug that caused `Cannot set properties of null (setting 'innerHTML')` across dashboard, review, voice, upload, and OCR controls.
- `$()` now uses `document.getElementById()` because its callers pass IDs.
- Removed duplicate navigation ownership from `boot.js`; `app.js` is the sole view controller.
- Added a visible client-side error area.
- Bumped static asset cache versions to v9.0.
- Static checks: Python compile, Node syntax, HTML ID audit, ZIP integrity.

The real browser microphone permission and Gemini network call still depend on the user's browser/device and GEMINI_API_KEY.
