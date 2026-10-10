# Source project requirements

## Project

**Multimodal Healthcare Triage Assistant for Government and Institutional Health Facilities**

## Problem statement

Build a human-in-the-loop healthcare triage assistant that helps government hospitals, primary health centers, public health camps, company clinics, industrial-estate health units, and campus health centers summarize patient-provided symptoms, uploaded reports, and basic visual inputs into a structured triage note for qualified review. The solution should be designed for India-wide contexts where patient load, language diversity, specialist availability, and digital maturity vary significantly across facilities.

## Expected features

The prototype should collect symptoms through text or voice, extract key details from sample medical reports, summarize timelines, identify missing information, and generate follow-up questions for a health worker, nurse, doctor, or medical officer. It may include OCR for lab reports, translation between English/Hindi/regional languages, risk-category tagging, queue prioritization, referral preparation, and a reviewer dashboard.

The system is explicitly non-diagnostic: it should organize information, highlight urgency signals, and support faster review, but it must not prescribe treatment or replace a qualified professional.

Suggested India-wide scenarios include outpatient queue triage, occupational-health screening in industrial estates, campus fever triage, maternal-health follow-up reminders, chronic disease check-in support, public health camp screening, and referral note preparation for higher facilities.

## Evaluation criteria / weightage

- Safety-first triage workflow — 20%
- Quality of information extraction and summarization — 20%
- Multimodal capability such as text, voice, OCR, or image understanding — 15%
- India-wide facility relevance and accessibility — 15%
- Human-review design and escalation logic — 15%
- Privacy and responsible AI controls — 10%
- Demo quality — 5%

## Guidelines

Use synthetic or public sample data only; do not use real patient records. Include a clear disclaimer that the solution is for educational prototype and triage-support purposes only. Recommended technologies include OCR libraries, speech-to-text, translation, lightweight LLM summarization, rules-based risk flags, and secure role-based access mockups. Demonstrate consent, minimal data retention, anonymization, auditability, and handoff to qualified medical staff. Any health-related output must remain advisory and reviewer-facing.

## Implementation mapping

The current build implements the required intake, multimodal report/voice paths, structured reviewer-facing output, deterministic urgency overlay, scenario handling, queue prioritization, reviewer dashboard, admin governance, audit trail, consent, retention cleanup, optional database encryption, multilingual selectors and Vercel deployment support. See `PROJECT_STATUS.md` and `FEATURES_FINAL.md` for the detailed implementation checklist.
