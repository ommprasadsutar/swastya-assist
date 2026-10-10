> Historical release notes; retained for project history. Current implementation is V10.4.3.

# Swastya Assist V10.4.2 Final

This patch addresses provider HTTP 400 invalid_request responses observed during live triage tests.

## Gemini transport
- Uses exactly one direct HTTP POST per user AI attempt.
- No Google SDK interaction transport.
- No automatic retry and no fallback-model retry.
- Uses the documented documented `/v1beta/models/{model}:generateContent` endpoint.
- Removes optional `store` and structured `response_format` fields from production transport to minimize request validation surface.
- Text-only interactions use the documented string `input` form.
- JSON is requested in the prompt and validated locally before a case can be created.
- Provider error details are logged server-side in truncated form for diagnosis without exposing the API key.

## Voice
- One inline audio interaction per user attempt.
- No Files API upload/delete cycle.
- No second translation interaction.
- Transcript and translation are parsed locally from the single model text response.

## Safety
All existing non-diagnostic, consent, human-review, non-health-input, audit, and single-user-retry controls remain in place.

## Verification
Historical V10.4.2 static/contract tests covered its then-current transport and retry contracts. V10.4.3 supersedes that transport with GenerateContent REST.
