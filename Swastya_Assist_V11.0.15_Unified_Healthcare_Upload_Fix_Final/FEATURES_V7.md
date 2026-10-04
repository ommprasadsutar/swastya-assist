# Swastya Assist V7

Reviewer decision persistence hardening: deterministic URL-encoded save, explicit CSRF header/body, transaction rollback on failure, dirty-state indicator, saved-state verification, session-check endpoint, and frontend cache bust.


### V7.1 login reliability
- Dedicated persistent login CSRF secret for local development.
- `.env` takes precedence during local testing.
- Login page responses are non-cacheable.

- Gemini resilience: transient 429/5xx responses now fail over to configured fallback models for multimodal analysis; voice falls back from the dedicated transcribe model to a general multimodal model, and the API returns a usable warning/fallback instead of a 502.
