# Swastya Assist V11.0.13 — Report Verification Fix

- Fixes false rejection of clear healthcare reports such as CBC/laboratory reports when Gemini returns a transient false-negative `input_valid=false`.
- Adds a bounded server-side recovery check using multiple high-specificity medical-report markers from model-extracted content; filenames are never used as proof.
- Makes the uploaded-report verification panel visible on the normal Patient Intake result, not only the standalone OCR workflow.
- On patient-name mismatch, returns the detected report name in the error response while withholding OCR/clinical extraction output.
- Patient contact number remains optional and excluded from AI payloads.
- No diagnosis, prescription, or autonomous patient contact is added.
