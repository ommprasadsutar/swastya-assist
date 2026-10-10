# Swastya Assist V10.4.3 — Final Hardened Release

## Release goals
- Strict one-provider-attempt behavior: model generation uses a direct one-shot HTTP POST, bypassing SDK interaction retries.
- One explicit user retry per failed AI chain; retry tokens are server-issued and single-use.
- No automatic model fallback.
- Triage, report/OCR, voice transcription and translation stop the current chain on failure.
- Invalid structured AI output never creates a patient case.
- Voice uses one Gemini 3.8 Flash multimodal audio interaction to return both transcription and translation.
- Urgent AI output requires explicit human verification before Reviewed/Escalated.
- Local SQLite remains the laptop default; Vercel requires managed PostgreSQL through DATABASE_URL.
- Vercel readiness requires persistent DB, secure secrets, cron secret and non-memory rate-limit storage.
- Static asset cache version is 18.0 and favicon is included.

## AI contract
1. User submits an AI operation.
2. Exactly one provider attempt is made.
3. Success continues the workflow.
4. Failure stops the workflow and returns a single-use Retry token.
5. User may click Retry once.
6. If Retry fails, no third attempt is accepted for that input.
7. A new patient/report/recording starts a fresh chain.

## Important
AI output is reviewer-facing documentation support only. It is not a diagnosis or treatment recommendation. Qualified healthcare personnel remain responsible for final decisions.

## V10.4 fixes
- Gemini Interactions model calls now use a direct one-shot HTTP POST, bypassing SDK interaction retry behavior.
- Voice transcription and translation are combined into one Gemini 3.8 Flash audio interaction, so one voice submission makes one model interaction instead of two.
- Voice returns structured transcript + translation from that single interaction.
- Gemini HTTP errors are surfaced with their status without automatic provider retries or model fallback.
- Static asset cache version is 18.0.
