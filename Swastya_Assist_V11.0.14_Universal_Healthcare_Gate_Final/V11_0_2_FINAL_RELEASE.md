# Swastya Assist V11.0.2 — final workflow hardening

V11.0.2 keeps the V10.4.4/V11 UI structure and the direct Gemini GenerateContent REST transport. It adds the final workflow-hardening items requested for the triage prototype:

- facility-scoped case access
- separate automated and final reviewer priority
- strict Gemini triage payload validation
- untrusted-data prompt boundaries
- conservative urgency negation/history handling
- reviewer evidence verification
- persisted follow-up answers
- explicit Insufficient information priority
- safe manual fallback when Gemini is unavailable (no alternative model call)
- referral transition guardrails: Sent → Acknowledged → Completed
- consent metadata and synthetic-data safeguards

The system remains non-diagnostic and reviewer-facing. No treatment or prescription capability was added.

Validation performed in the build environment:
- Python compileall: PASS
- JavaScript syntax checks: PASS
- static security/workflow contract checks: PASS
- SQLite migration contract checked without raw `UPDATE case` statements

A full Flask runtime test was not available in the build environment because Flask packages were not installed there.
