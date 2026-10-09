# Swastya Assist — 152-Item Functional Audit (V11.1.2)

## Audit basis
This audit reviews each item in the 152-item functional checklist against the current V11.1.2 source, templates, static frontend and existing contract/regression tests in this release workspace.

**Status meanings**
- **Fully working** — implementation is present and deterministic enough to verify from the current source/contracts; external production dependencies may still require deployment verification.
- **Partially working** — an implementation exists, but the current scope is narrower than the checklist item or an important piece is not yet complete.
- **Fragile** — implementation is present, but reliable operation depends on browser/provider/database/cloud configuration that cannot be exercised end-to-end in this build environment.
- **Only claimed** — the item is referenced by the product/checklist but there is no substantiated current implementation for it.

The uploaded PS3 problem statement explicitly requires multimodal intake, report extraction, timelines, missing information, follow-up questions, and a non-diagnostic human-review workflow; OCR, translation, risk tagging, queue prioritization, referral preparation and a reviewer dashboard are permitted extensions. Outputs must remain advisory/reviewer-facing and synthetic/public sample data must be used. See the source PDF for the authoritative problem statement.

**Important test limitation:** the current build container does not have Flask/Flask-SQLAlchemy/Flask-Limiter/Redis/Psycopg/Gunicorn installed and package installation is unavailable. Therefore this is a source/contract audit, not a claim of live production E2E success against PostgreSQL/Redis/Gemini/browser hardware.

| # | Functional item | Status | Current implementation / verification note |
|---:|---|---|---|
| 1 | Patient Intake | Fully working | Dedicated Patient Intake form in the Clinical Console; wired to `/api/triage`. |
| 2 | Patient/encounter creation | Fully working | Triage route creates a persisted `Case` with case ID and patient reference. |
| 3 | Patient reference | Fully working | Optional reference accepted; deterministic synthetic fallback generated and validated. |
| 4 | Age, gender and language capture | Fully working | Intake fields plus server-side validation for age/language. |
| 5 | Facility assignment | Fully working | Case stores `facility_id`; new admin users are assigned to an active facility. |
| 6 | Consent capture and metadata | Fully working | Consent flag plus version, timestamp and language persisted. |
| 7 | Patient narrative | Fully working | Editable narrative textarea; voice transcript can be inserted into it. |
| 8 | Voice symptom input | Fragile | Real MediaRecorder/browser microphone path is implemented, but hardware/browser permission and live capture were not runnable here. |
| 9 | Editable voice transcript | Fully working | Transcript is an editable textarea and can be copied into Patient Narrative. |
| 10 | Multilingual input | Fragile | Indian language selectors and locale handling exist; real speech-language coverage is browser/provider dependent. |
| 11 | Translation | Fragile | Gemini translation path exists; live provider translation was not exercised in this environment. |
| 12 | Editable translated text | Fully working | Translation is rendered into an editable textarea before use. |
| 13 | Medical-report upload | Fully working | Multipart upload route and client picker are implemented. |
| 14 | PDF/PNG/JPG/JPEG support | Fully working | Server and UI validate PDF/PNG/JPEG MIME types and content. |
| 15 | Document preview | Fully working | Client preview for images and readable PDF selection state; object URLs are revoked on replacement/removal. |
| 16 | Healthcare-document verification | Fragile | Shared content-based healthcare gate plus multimodal Gemini classification; live provider behavior still needs deployment testing. |
| 17 | Patient-name extraction | Fragile | Gemini extracts the printed report name; live OCR/model extraction was not executed here. |
| 18 | Patient-name matching | Fully working | Deterministic normalized-name comparison blocks mismatches. |
| 19 | Report date extraction | Fragile | OCR schema/prompt requests report date; depends on live document extraction. |
| 20 | Document-type extraction | Fragile | OCR schema constrains supported healthcare document types; live extraction not exercised. |
| 21 | OCR | Fragile | Full source transcription requested through Gemini; PDFs also have local text extraction, but image OCR/provider path needs live testing. |
| 22 | Structured report extraction | Fragile | `extracted_report_fields` are schema validated and displayed; live report-model quality unverified here. |
| 23 | Tables/measurements extraction | Fragile | OCR schema includes measurements and reference ranges; live extraction not verified. |
| 24 | Section/page information | Fragile | OCR sections and document ordering are modeled; exact page-level behavior depends on provider output. |
| 25 | Extraction confidence | Fragile | OCR quality (`Good/Fair/Poor/Unknown`) is represented; live confidence quality is provider dependent. |
| 26 | Unreadable-content identification | Fragile | `ocr_unreadable_portions` and `[unclear]` policy exist; live quality needs real documents. |
| 27 | AI clinical-information summarization | Fragile | Structured `summary` with strict schema; live Gemini response quality not runnable here. |
| 28 | Timeline generation | Fragile | Prompt/schema require plain-text timeline; server normalization hardens list/object drift. Provider output still needs E2E test. |
| 29 | Key-detail extraction | Fragile | Structured `key_details` field exists and is bounded; live quality unverified. |
| 30 | Missing-information detection | Fragile | Structured `missing_information` exists; depends on live Gemini output quality. |
| 31 | Follow-up-question generation | Fragile | Structured `follow_up_questions` exists; provider quality not live-tested. |
| 32 | Follow-up answer capture | Fully working | Reviewer UI persists bounded follow-up answers and verified flags through `/review`. |
| 33 | Evidence mapping | Fully working | Evidence/source mapping is persisted and rendered with reviewer verification states. |
| 34 | Scenario-aware triage | Fully working | Seven supported scenarios are validated and included in prompt guidance. |
| 35 | AI urgency/risk signals | Fragile | AI risk signals are schema-validated and merged with deterministic local safety flags; live AI behavior still needs testing. |
| 36 | AI priority | Fragile | AI `risk_category` is modeled and surfaced as advisory; live provider output not verified. |
| 37 | Insufficient-information status | Fully working | Added deterministic thin-input detection for empty or very short narratives, with missing-information and follow-up prompts. |
| 38 | AI failure/manual fallback | Fragile | Manual fallback exists for text-only flow; uploaded documents intentionally stop when safe verification cannot be completed. Live failure simulation still needed. |
| 39 | Reviewer dashboard | Fully working | Queue/dashboard and reviewer drawer are implemented. |
| 40 | Case queue | Fully working | `/api/cases` queue with sorting/filtering and responsive UI. |
| 41 | Needs Review status | Fully working | Supported in model, validation and reviewer UI. |
| 42 | Reviewed status | Fully working | Supported in model and reviewer save route. |
| 43 | Escalated status | Fully working | Supported with referral/handoff validation. |
| 44 | Needs More Information status | Fully working | Supported in validation and reviewer UI. |
| 45 | Human review | Fully working | Reviewer decision form persists human status, note and final priority. |
| 46 | Human/final priority | Fully working | Separate `final_risk` from `ai_risk`; legacy `risk` mirrors final human-reviewed value. |
| 47 | Reviewer override | Fully working | Priority changes require a reviewer reason. |
| 48 | Override reason | Fully working | Bounded `risk_override_reason` persisted and displayed. |
| 49 | Evidence verification | Fully working | Reviewer can set evidence state and note; server validates allowed states. |
| 50 | Pending/Verified/Rejected/Unclear evidence states | Fully working | All four states are validated and rendered. |
| 51 | Reviewer notes | Fully working | Persisted reviewer note field with UI. |
| 52 | Complete case review | Fully working | Reviewer workspace includes patient info, narrative, report, AI packet, evidence, follow-ups, decision, referral and contact workflow. |
| 53 | Full raw report/OCR extraction on Reviewer | Fully working | `full_report_extraction` is stored in AI note and rendered only in the reviewer workspace/packet. |
| 54 | Structured triage information on Reviewer | Fully working | Summary, timeline, key details, missing info, follow-ups, risk and evidence are rendered. |
| 55 | Patient/contact information for authorized reviewer | Fully working | Case detail requires login and sensitive contact fields are returned only from authorized case detail serialization. |
| 56 | Human-controlled patient contact | Fully working | `/api/cases/<cid>/contact` performs a `tel:` handoff only after reviewer priority/consent checks. |
| 57 | Contact audit trail | Fully working | Contact attempts are stored and initiation is audited. |
| 58 | Referral preparation | Fully working | Referral scenario, destination and handoff fields exist in reviewer UI/API. |
| 59 | Referral lifecycle: Draft | Fully working | Forward-only lifecycle begins at Draft. |
| 60 | Ready | Fully working | Draft → Ready is enforced. |
| 61 | Sent | Fully working | Ready → Sent is enforced. |
| 62 | Acknowledged | Fully working | Sent → Acknowledged is enforced and timestamped. |
| 63 | Completed | Fully working | Acknowledged → Completed is enforced. |
| 64 | Handoff information | Fully working | Destination/status and reviewer handoff are stored and displayed. |
| 65 | Patient role | Fully working | Added dedicated Patient role, self-registration, login routing, Patient portal, own-submission history, and server-side prohibition on clinical review APIs. |
| 66 | Health Worker role | Fully working | Dedicated `health_worker` role is now accepted by the clinical route guards and admin role management. |
| 67 | Nurse/Doctor/Medical Officer review roles | Fully working | Dedicated `nurse`, `doctor`, `medical_officer`, and `reviewer` roles are supported by clinical route guards and admin role management. |
| 68 | Admin role | Fully working | Separate admin role with protected Admin Console routes. |
| 69 | Role-based access control | Fully working | Route decorators enforce admin vs clinical-team access and sensitive operations. |
| 70 | Facility-scoped access | Fully working | Non-admin case queries are filtered to `facility_id`. |
| 71 | Facility isolation | Fully working | `case_for_current_user` blocks cross-facility case access; analytics are facility-scoped. |
| 72 | User approval | Fully working | Registration requests require admin approval before account activation. |
| 73 | User management | Fully working | Admin create/enable/disable/delete and facility/role assignment flows exist. |
| 74 | Facility management | Fully working | Admin can create and activate/deactivate facilities. |
| 75 | Access management | Fully working | Admin controls role, facility and account activation for managed users. |
| 76 | Admin dashboard | Fully working | Separate Admin Console with access, facility, audit, health and retention panels. |
| 77 | User administration | Fully working | Dedicated user management UI/API. |
| 78 | Role/access administration | Fully working | Admin can set user roles and facility assignment with audit events. |
| 79 | Facility administration | Fully working | Facility CRUD-lite and active-state control are present. |
| 80 | Approval management | Fully working | Pending registration requests can be approved/rejected. |
| 81 | Audit logs | Fully working | Dedicated audit table and admin audit API/filter are present. |
| 82 | Security monitoring | Fully working | Admin dashboard now exposes 24-hour security-event and failed-login counts alongside the filtered audit log. |
| 83 | Retention controls | Fully working | Retention duration is persisted in a SystemSetting, editable by Admin, bounded to 1–3650 days, and used by cleanup/readiness surfaces. |
| 84 | System health | Fully working | Admin system health endpoint and dashboard status cards exist. |
| 85 | AI/Gemini diagnostics | Fragile | Diagnostic endpoint and UI test are implemented but require live Gemini configuration/network. |
| 86 | Operational analytics | Fully working | Facility-scoped analytics endpoint and dashboard charts exist. |
| 87 | Optional patient contact number | Fully working | Intake contact number is explicitly optional. |
| 88 | Contact number stored separately | Fully working | Stored in dedicated encrypted `contact_phone` field and only included in sensitive serialization. |
| 89 | Contact number never sent to Gemini/AI | Fully working | Contact phone is excluded from AI prompt construction and request fingerprint payload. |
| 90 | Consent controls | Fully working | Intake consent required; contact consent required before contact; metadata persisted. |
| 91 | Minimal retention | Fully working | A configurable case-retention policy is stored separately from the audit history, with manual Admin cleanup and protected scheduled cleanup endpoint. |
| 92 | Synthetic/public sample-data protection | Fully working | Demo-only gate, disclaimer and direct-identifier blocking are implemented. |
| 93 | PII-like pattern protection | Fully working | Demo-mode phone/Aadhaar/PAN/email-like checks block obvious identifiers. |
| 94 | Auditability | Fully working | Auth, case/review, contact/referral, admin operations, retention-policy changes and CSRF failures are audited; admin can filter recent history. |
| 95 | Secure cookies | Fully working | HTTPOnly/SameSite and deployment-conditional Secure cookie policy are configured. |
| 96 | CSRF protection | Fully working | Login CSRF token plus session CSRF checks protect state-changing workflows. |
| 97 | Security headers | Fully working | CSP, frame denial, referrer, permissions and cross-origin policies are set. |
| 98 | Rate limiting | Fragile | Flask-Limiter is configured, with Redis/Upstash support, but live distributed store behavior is deployment dependent. |
| 99 | Encryption for protected contact information | Fragile | Fernet-backed fields are implemented; production requires configured key and live database verification. |
| 100 | Facility-level data isolation | Fully working | Case retrieval and analytics are filtered for non-admin facility users. |
| 101 | Reviewer authorization checks | Fully working | Reviewer/admin/clinical-role route guards and case scoping are enforced server-side. |
| 102 | Strict Gemini JSON/schema validation | Fully working | Response schemas + server-side structural validation + bounded fields. |
| 103 | Prompt-injection/data-boundary protection | Fully working | Prompt clearly marks patient/report sections as untrusted data and instructs model not to follow embedded instructions. |
| 104 | Bounded AI outputs | Fully working | String/list limits and schema restrictions are enforced before persistence. |
| 105 | Safe urgency-flag handling | Fully working | Local flags are conservative and verification-required; emergency signals cannot be downgraded by model output. |
| 106 | Negation/history-aware urgency handling | Fully working | Context guard ignores obvious negated/historical mentions. |
| 107 | Timeline normalization/validation | Fully working | Plain-text schema rule plus bounded list/object normalization protects transient model shape drift. |
| 108 | No diagnosis | Fully working | Prompt, UI and validation explicitly prohibit diagnosis; diagnostic language is rejected. |
| 109 | No prescription | Fully working | Treatment/prescription language is disallowed in AI output validation. |
| 110 | No treatment recommendation | Fully working | Prompt/UI safety boundary prohibits treatment recommendations. |
| 111 | AI output remains advisory/reviewer-facing | Fully working | UI language and reviewer handoff explicitly label AI information as advisory. |
| 112 | Qualified human remains responsible for final review | Fully working | Reviewer save flow is mandatory for final human status/priority; UI communicates human responsibility. |
| 113 | Upload | Fully working | Clinical and OCR forms support secure multipart uploads. |
| 114 | Healthcare-document verification | Fragile | Same shared gate as item 16; needs live document/provider testing. |
| 115 | Patient-name verification | Fully working | Same deterministic normalized-name check as item 18. |
| 116 | Generate triage only after successful verification | Fully working | Uploaded reports are blocked until shared healthcare/name verification passes. |
| 117 | Invalid/non-healthcare document → no clinical output | Fully working | Gate returns verification failure before persistence and UI suppresses extraction/triage output. |
| 118 | Name mismatch → no clinical output | Fully working | Mismatch returns only verification failure plus detected name; no OCR/triage result exposed. |
| 119 | Missing/unreadable patient name → no clinical output | Fully working | Empty/unreadable `report_patient_name` blocks report output. |
| 120 | No invalid document saved as a clinical case | Fully working | Uploaded-report verification is completed before `Case` creation. |
| 121 | Verified report → full structured extraction | Fragile | Full structured output is implemented; real document extraction quality still requires Gemini/document E2E testing. |
| 122 | Reviewer → complete structured information + full raw extraction | Fully working | Reviewer detail includes structured triage plus `full_report_extraction`; packet also includes the AI information. |
| 123 | Flask application | Fully working | Flask application, routing and deployment files are present; runtime package installation is the current environment limitation. |
| 124 | Gemini GenerateContent REST integration | Fragile | One direct `httpx.post` GenerateContent transport is enforced; live API connectivity/model compatibility needs deployment testing. |
| 125 | PostgreSQL support | Fragile | SQLAlchemy PostgreSQL URL and explicit Postgres migration are implemented; live managed database is not available here. |
| 126 | SQLite support/fallback | Fragile | SQLite default plus idempotent column migrations are implemented; full app runtime is unavailable here. |
| 127 | Idempotent database migration | Fragile | SQLite/Postgres migration routines exist, but a live pre-upgrade database was not available for execution. |
| 128 | Redis/Upstash support | Fragile | Rate limiter selects Redis/Upstash URI when configured; live connection was not exercised here. |
| 129 | Gunicorn | Fully working | `gunicorn` is declared in requirements and the package includes standard Flask deployment configuration. |
| 130 | Docker | Fully working | Dockerfile is present and configured for the application. |
| 131 | Vercel deployment | Fragile | Vercel project/deploy configuration exists and production deployments exist, but the current V11.1.2 source was not proven to be the live production commit in this pass. |
| 132 | `/healthz` | Fully working | Health endpoint is deterministic and does not require AI. |
| 133 | `/readyz` | Fragile | Strict readiness checks are implemented; actual result depends on live PostgreSQL/secrets/Redis/cron configuration. |
| 134 | Gemini diagnostics | Fragile | Authenticated diagnostic route and UI test exist; live provider call not executed here. |
| 135 | Retention/cleanup process | Fragile | Admin and protected maintenance cleanup are implemented; production scheduling/execution requires deployed environment validation. |
| 136 | Responsive application | Fully working | Responsive CSS, navigation drawer and small-screen table/card adaptations are implemented and statically verified. |
| 137 | Low-connectivity fallback | Partially working | Same-device intake text and voice drafts now persist locally for up to 24 hours; full offline case queue/sync remains outside the current architecture. |
| 138 | Local draft preservation | Fully working | Clinical intake and Patient self-entry text fields are restored from same-device session drafts; uploaded files remain intentionally non-persisted. |
| 139 | Audit/security logging | Fully working | Audit events cover auth, security, admin, triage, case access, review, contact, referral and retention operations; live retention/collection still depends on deployment. |
| 140 | English | Fragile | Included in selectors, validation and translation choices; real end-to-end language behavior was not live-tested. |
| 141 | Hindi | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 142 | Bengali | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 143 | Marathi | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 144 | Tamil | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 145 | Telugu | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 146 | Odia | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 147 | Kannada | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 148 | Malayalam | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 149 | Punjabi | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 150 | Gujarati | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 151 | Assamese | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |
| 152 | Urdu | Fragile | Included in language selectors/locale handling; speech/translation provider behavior needs live testing. |

## Current audit totals

- Fully working: **103**
- Partially working: **1**
- Fragile: **48**
- Only claimed: **0**
- Total audited: **152**

The “fragile” category is intentionally conservative: it means the code path exists but this environment cannot prove the live browser/provider/database/cloud behavior. It is **not** a claim that those features are broken. External provider, device and managed-service items remain deployment-verification dependent.
