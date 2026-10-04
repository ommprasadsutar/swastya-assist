# Swastya Assist V11.0.11 — Healthcare Document Gate

This release adds only the requested healthcare-document verification hardening on uploaded reports.

- The actual document content must be verified as healthcare-related before OCR, report extraction, triage output, or persistence.
- A non-healthcare document receives a clear no-output response.
- The patient-name mismatch gate remains enforced after the healthcare-document gate.
- OCR-only document type classification is constrained to healthcare document categories.
- Patient Intake, voice, reviewer workflow, risk/priority, referral, consent, facility isolation, analytics, Gemini transport, and other existing features are unchanged.
- No diagnosis, prescription, or treatment recommendation is introduced.
