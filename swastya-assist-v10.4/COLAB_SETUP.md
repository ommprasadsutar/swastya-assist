# Swastya Assist — Colab / laptop setup

1. Upload the project ZIP and extract it.
2. Install dependencies with `pip install -r requirements.txt`.
3. Set `ADMIN_PASSWORD` and optionally `GEMINI_API_KEY`.
4. The default Gemini model is `gemini-3.8-flash`; the application uses the GenerateContent REST endpoint.
5. Run `python app.py` or a normal Flask/Gunicorn command.
6. Open the local/forwarded HTTPS URL. Microphone access requires HTTPS except on localhost.

The app uses synthetic/public sample data only and is non-diagnostic. A qualified reviewer must verify AI output.
