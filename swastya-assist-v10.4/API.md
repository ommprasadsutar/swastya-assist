# Swastya Assist V8 API

All authenticated state-changing endpoints require the session CSRF token in the form body or `X-CSRF-Token` header. Reviewer/admin endpoints additionally enforce role checks.

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Process health |
| GET | `/readyz` | Production readiness checks |
| GET/POST | `/login` | Sign in with dedicated signed login token |
| POST | `/logout` | End session |
| GET/POST | `/register` | Doctor/Reviewer access request |
| POST | `/api/triage` | Create a triage encounter from patient narrative/report input |
| POST | `/api/voice` | Browser audio → Gemini transcription/translation with safe fallback |
| GET | `/api/cases` | Review queue with risk/status filters |
| GET | `/api/cases/<id>` | Case details |
| GET | `/api/cases/<id>/report` | Authenticated original report stream |
| GET | `/api/cases/<id>/packet` | Printable reviewer packet data |
| POST | `/api/cases/<id>/review` | Persist human reviewer status/note |
| GET | `/api/analytics` | Volume/risk/status/language/scenario metrics |
| GET | `/api/diagnostics` | Authenticated app/runtime diagnostics |
| GET | `/api/ocr` | Gemini/report capability status |
| GET/POST | `/api/maintenance/retention` | Bearer-protected retention cleanup for Vercel cron |

The API never places report bytes inside queue JSON. Report bytes are returned only from the authenticated report route. AI results are advisory and reviewer-facing.
