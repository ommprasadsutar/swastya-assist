> Historical V8 checklist; retained for project history. Current implementation is V10.4.3.

V8.0.1 FINAL PATCH

# V8 final laptop-to-Vercel checklist

## Laptop acceptance
- Login succeeds in a fresh browser window.
- Dashboard loads and refreshes.
- Start microphone prompts for permission and records.
- Stop shows playback and a usable browser transcript.
- AI transcription uses `gemini-3.5-transcribe` when a key is present.
- OCR view Gemini status pill can run the built-in connection test and show a readable service/key error.
- Gemini 503 leaves the browser transcript available.
- Image/PDF chooser opens the native picker.
- Selected image previews immediately.
- Change/choose new replaces the file.
- Remove clears the file and preview.
- Patient intake creates a queue case.
- OCR/report workflow creates a queue case and shows extracted reviewer data or a safe fallback.
- Doctor dashboard opens the case drawer.
- Reviewer status and note save and survive a case reload.
- Unsaved reviewer changes warn before switching/closing.
- Analytics values refresh after new/reviewed cases.
- Original report opens only after authentication.
- Admin governance and synthetic case deletion work.

## Vercel acceptance
- Managed PostgreSQL configured.
- Encryption key configured and stable.
- Redis/Upstash rate limiter configured.
- `COOKIE_SECURE=1`.
- `CRON_SECRET` configured.
- Gemini key configured if AI is required.
- `/healthz` returns 200.
- `/readyz` returns 200 with all checks true.
- Static `/static/*` assets load from the Vercel public bundle.
- Daily retention cron path is `/api/maintenance/retention`.
