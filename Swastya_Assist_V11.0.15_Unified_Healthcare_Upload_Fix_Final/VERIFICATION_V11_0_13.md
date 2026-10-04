# Swastya Assist V11.0.13 Verification

## Changes in this release
- Healthcare-document gate now recognizes clear medical/laboratory reports more reliably, including Complete Blood Count (CBC) reports, even if the model returns a transient high-level false-negative classification.
- The gate still blocks clear non-health documents and never trusts filenames as proof of a medical document.
- Patient Intake results now display the detected report patient name and verified/matched status when a report is accepted.
- Patient-name mismatch returns an explicit `PATIENT_NAME_MISMATCH` response with the detected report name, while withholding OCR/report extraction/triage output.
- Optional contact number remains separate from AI/Gemini payloads.

## Verification performed
- 50 repository contract/unit tests passed.
- Python syntax compilation passed for `app.py`.
- JavaScript syntax check passed for `static/app.js`.
- Release verification contract passed.
- Public/static frontend copies are synchronized with the main static assets.
- A focused regression simulation using the supplied CBC report content confirmed that the medical-document evidence score accepts the report and rejects an invoice example.

## Runtime limitation
A full live Flask/Gemini/browser integration test was not executed in this environment because the runtime dependency set could not be installed: outbound package-network access was unavailable and Flask was not preinstalled. The released source therefore has static/unit/contract verification, but the deployed environment must still be exercised end-to-end after deployment with a configured `GEMINI_API_KEY` and production database.
