# Swastya Assist V11.0.14 — Unified Healthcare Document + Name Verification

## What changed
- Patient Intake and standalone OCR now use the same server-side healthcare-document verification gate.
- The gate covers healthcare-related reports broadly: laboratory/pathology, radiology/imaging, clinical notes, discharge summaries, prescriptions/medication documents, screening, referral, maternal-health, occupational-health and other supported healthcare documents.
- Clear non-healthcare documents such as invoices, resumes, bank statements, assignments and other unrelated documents remain blocked.
- Filenames are never treated as proof that a document is medical.
- The gate uses bounded content evidence to recover clear medical-document false negatives while remaining conservative about arbitrary files.
- Patient-name verification is also shared by both Patient Intake and OCR. The report name must be readable and strongly match the Patient Intake name before OCR/report extraction/triage output can be exposed or persisted.
- On mismatch or missing/unreadable report name, only the verification error and detected name (when available) are returned; report/OCR/clinical extraction is withheld.
- Optional patient phone remains separate from AI/Gemini payloads.
- Existing reviewer, human override, evidence verification, follow-up, referral, voice, multilingual, privacy, security and non-diagnostic controls are retained.

## Verification
- Unified document/name regression suite: PASS
- Focused V11.0.13 regression suite: PASS
- Contract/security/frontend/Gemini/timeline tests: PASS (excluding environment-dependent Flask smoke test)
- Python syntax: PASS
- JavaScript syntax: PASS

## Runtime note
A full Flask/Gemini/browser integration run still requires the deployment environment with its configured dependencies and `GEMINI_API_KEY`. After deployment, test both upload paths with matching and mismatching synthetic healthcare reports plus clearly non-health documents.
