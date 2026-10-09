# V11.0.18 — Clinical UI Redesign

- Preserves the full V11.0.x healthcare triage feature set and safety gates.
- Refines the existing interface toward the approved Swastya Assist visual reference: clinical blue/teal palette, clearer iconography, stronger hierarchy, cards, status chips and responsive spacing.
- Existing logo artwork and branding colors are unchanged.
- Uses inline SVG icons only; no external icon/CDN dependency.
- Patient Intake and OCR now surface the complete structured triage-support output after a successful Generate/Submit action, including summary, timeline, key details, risk/urgency signals, missing information and follow-up questions.
- Reviewer workspace continues to show all structured triage information plus the full raw report extraction.
- Verification failures continue to expose only the verification failure state and no clinical/OCR output.
- Optional contact information remains outside Gemini/AI payloads.
- No new clinical capability and no change to Gemini transport/API workflow.
