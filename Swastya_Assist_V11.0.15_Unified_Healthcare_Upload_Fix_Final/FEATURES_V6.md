# Swastya Assist V6

## Voice reliability update

- Uses Gemini 3.5 Transcribe for dedicated audio-file transcription when Gemini is available.
- A Gemini 503/temporary-unavailable response no longer makes the voice UI fail with HTTP 502 when a browser transcript exists.
- Browser transcript is retained as the safe fallback and can be copied into Symptoms.
- Gemini translation remains best-effort and cannot block transcription.
- Adds GEMINI_TRANSCRIBE_MODEL to `.env.example`.

This remains non-diagnostic and human-reviewed.
