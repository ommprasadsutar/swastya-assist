"""One-shot Gemini GenerateContent connection check for Swastya Assist V11.0.0.

This script makes exactly one provider POST. It does not retry, follow redirects,
or use fallback models.
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "").strip()
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip().removeprefix("models/")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

if not key:
    raise SystemExit("GEMINI_API_KEY is not configured")

payload = {
    "contents": [{
        "role": "user",
        "parts": [{"text": "Reply with exactly: Swastya Assist AI connection test successful."}],
    }]
}

response = httpx.post(
    url,
    headers={"x-goog-api-key": key, "content-type": "application/json"},
    json=payload,
    timeout=60.0,
    follow_redirects=False,
)
print("HTTP", response.status_code)
try:
    body = response.json()
except Exception:
    body = None
if isinstance(body, dict):
    usage = body.get("usageMetadata") or {}
    print("MODEL", model)
    print("INPUT_TOKENS", usage.get("promptTokenCount", ""))
    print("OUTPUT_TOKENS", usage.get("candidatesTokenCount", ""))
    chunks = []
    for candidate in body.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            if isinstance(part, dict) and part.get("text"):
                chunks.append(str(part["text"]))
    print("OUTPUT", "\\n".join(chunks).strip())
else:
    print(response.text[:4000])

if response.status_code >= 400:
    response.raise_for_status()
