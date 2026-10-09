# Swastya Assist V11.1.4 — Final UI + Feature Package

## Included
- V11.1.3 blue/teal/white healthcare UI and responsive clinical/admin workspaces.
- Patient Intake, voice/transcription, multilingual workflow, medical-report upload, healthcare-document verification, patient-name verification, OCR/report extraction, structured triage, reviewer workspace, evidence verification, follow-ups, human priority, referral lifecycle, optional contact privacy, RBAC/facility isolation, audit/security controls, health/readiness and deployment configuration.
- Existing Gemini GenerateContent integration preserved.
- Optional Qwen2.5-7B-Instruct QLoRA/SFT training kit under `model_training/`.

## Important status
The QLoRA kit is training infrastructure, not a claim that a fine-tuned model has already been trained or clinically validated. The current application remains compatible with the existing Gemini configuration until a locally evaluated model is explicitly integrated.

## Safety
The application remains non-diagnostic and reviewer-facing. Use synthetic/public data for the demonstration. Fine-tuning does not by itself guarantee privacy or clinical safety.
