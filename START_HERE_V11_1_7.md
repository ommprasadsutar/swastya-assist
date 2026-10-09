# Start Here — Swastya Assist V11.1.7 Privacy Gate

## Run locally
1. Extract the ZIP.
2. Open the `swastya_v114_work` folder in a terminal.
3. Create a virtual environment if you prefer, then run `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set a unique `FLASK_SECRET_KEY`, `LOGIN_CSRF_SECRET`, and an appropriate admin password.
5. For demo/presentation use, keep `DEMO_ONLY_MODE=1` and `PRIVACY_GATE_ENABLED=1`. Add `GEMINI_API_KEY` only if you want to use configured Gemini functions.
6. Start with `python app.py`, then open `http://127.0.0.1:5000`.

## New privacy controls
- Open **Privacy & AI Gate** from the clinical console navigation.
- Text entered for AI processing is passed through best-effort server-side identifier minimization. Demo mode blocks some detected direct identifiers.
- A separate checkbox is required before an original PDF/image can be forwarded to Gemini.
- A separate checkbox is required before raw recorded audio can be forwarded to Gemini.
- Without the respective checkbox, client and server gates stop the external AI request.

## Important limitations
- The prototype does **not** automatically mask image/PDF pixels. If you opt in, the original file may be sent to Gemini as-is.
- Text redaction is pattern-based and can miss names or other identifying combinations. It is not a guarantee of anonymization.
- The privacy page does not establish regulatory compliance or guarantee external provider retention/deletion behavior.
- Use synthetic/public sample data only in demo mode. Do not use real patient data until a qualified privacy/security/legal review and deployment hardening are completed.
- Runtime tests require the dependencies in `requirements.txt`.
