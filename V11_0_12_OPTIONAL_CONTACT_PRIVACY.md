# V11.0.12 — Optional Patient Contact Privacy Addition

Only requested change: Patient Intake now has an optional contact-number field.

Safety/privacy behavior:
- Optional during Patient Intake; not required by PS3.
- Stored in the existing encrypted `contact_phone` field.
- Excluded from Gemini prompt content, AI response schema, and AI request fingerprint.
- Not shown to or processed by AI.
- Existing reviewer contact workflow remains unchanged.
- OCR workflow is unchanged.
- All other existing features/UI/workflows are unchanged.
