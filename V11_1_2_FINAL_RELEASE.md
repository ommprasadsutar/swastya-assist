# Swastya Assist V11.1.2 — Production Stabilization Release

## Scope
This release is the implementation/stabilization pass requested for the existing Swastya Assist product. Existing clinical features, Gemini transport, safety boundaries, healthcare-document verification, patient-name verification, reviewer workflow, referral lifecycle, optional contact privacy, and the approved healthcare UI direction are preserved.

## Reliability and access hardening
- Implemented the Patient role as a real self-entry account path; patient registration creates an active patient account and routes to `/patient`.
- Clinical case APIs remain restricted to clinical/admin roles; patient users cannot use reviewer case APIs.
- Voice, OCR metadata, and Gemini diagnostics are restricted to clinical/admin roles so patient accounts remain outside AI/reviewer tooling.
- Preserved facility-scoped case access and patient-owned case scoping.
- Preserved encrypted optional contact storage and excluded `contact_phone` from AI prompts/fingerprints and local intake draft storage.
- Added persistent retention-policy settings with bounded values.
- Kept security event / failed-login monitoring visible in Admin Dashboard.
- Friendly 405/500 responses prevent raw framework/database errors from becoming normal user-facing pages.
- Browser/runtime bootstrap errors now use generic user-safe messaging instead of exposing the underlying browser exception text.
- Login submit handling now prevents accidental duplicate submissions and shows an explicit loading state.
- Admin data tables are contained within responsive horizontal-scroll regions on small screens; sign-in role cards use a 3-up desktop / 2-up tablet / 1-up mobile layout.

## UI/UX
- Preserved the existing Swastya Assist logo and logo colors.
- Unified asset cache version to `34.0`.
- Refined sign-in workspace selection into explicit Clinical / Patient / Administrator choices.
- Improved role-aware sign-in hints and password visibility control.
- Maintained responsive desktop/tablet/mobile layout system, touch targets, drawer navigation, reviewer responsiveness, responsive Admin tables, and reduced-motion support.

## 152-item audit
Current audit counts are generated from the itemized table in `FEATURE_152_AUDIT.md`. “Fragile” means externally dependent and not fully provable in this container; it does not mean the implementation is known to be broken.

## Verification run
- Focused regression/contract suite: **104 passed** (`tests/test_smoke.py` excluded because this build container lacks Flask runtime dependencies).
- `python -m py_compile app.py`: PASS.
- JavaScript syntax checks: PASS.
- Template parsing: PASS for all 6 HTML templates.
- Shared `static/` / `public/static/` assets: synchronized.
- `verify_release.py`: PASS after updating its version contract to 11.1.2.
