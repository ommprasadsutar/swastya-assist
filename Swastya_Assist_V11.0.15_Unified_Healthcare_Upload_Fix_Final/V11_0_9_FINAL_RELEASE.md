# Swastya Assist V11.0.9 — Patient/Report Name Match + Full Report Extraction

This release changes only the report identity gate and report extraction presentation requested for patient intake and AI reports/OCR.

- When a report is uploaded, Gemini must return the patient name printed on the report.
- The server conservatively compares the intake patient name with the report patient name before any OCR/report extraction/triage output is returned or persisted.
- If the names do not match, or the report name cannot be verified, the API returns a clear patient-name verification error and no OCR/report/triage output is shown or saved.
- Patient intake and the AI reports/OCR workflow both show the full readable report extraction plus structured extracted report fields.
- Existing UI, Gemini transport, safety controls, review workflow, and all other features remain unchanged.
