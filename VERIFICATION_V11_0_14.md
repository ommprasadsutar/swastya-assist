# V11.0.14 Verification

- Unified healthcare-document gate: PASS
- Patient Intake and OCR share the same document gate: PASS
- Patient Intake and OCR share the same patient-name verification gate: PASS
- CBC regression: PASS
- Laboratory/radiology/clinical/discharge/prescription/referral/screening/maternal/occupational samples: PASS
- Invoice/resume/bank-statement/assignment samples: PASS blocked
- Matching patient name: PASS
- Mismatching patient name: PASS blocked with detected report name only
- Missing/unreadable report name: PASS blocked
- Python compile: PASS
- JavaScript syntax: PASS
- Focused/contract suite: PASS
- Full runtime smoke suite could not be executed in this build environment because Flask is not installed; deploy-time integration testing remains required.
