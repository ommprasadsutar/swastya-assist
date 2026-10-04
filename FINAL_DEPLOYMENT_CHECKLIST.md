# Swastya Assist V11.0.5 — Final Production Deployment Checklist

Repository must contain these files at the ROOT level:
- app.py
- requirements.txt
- vercel.json
- templates/
- static/
- public/

Do not place the application inside another parent directory in the GitHub repository.

Final source checks completed:
- Python compile/syntax: PASS
- JavaScript syntax: PASS
- 32 release/contract tests: PASS
- GenerateContent REST transport contract: PASS
- V11 safety hardening contract: PASS
- Reviewer/contact/favicon contract: PASS
- PostgreSQL migration contract: PASS
- Static/public app.js and style.css synchronization: PASS
- Favicon files present: PASS
- 13 Indian-language intake/voice choices exposed: PASS

Runtime requirement:
- Configure the production environment variables documented in DEPLOYMENT.md/.env.example.
- Use PostgreSQL for persistent production data.
- Do not delete the existing database during deployment.
- GEMINI_API_KEY enables Gemini-assisted processing; the application has a manual-review fallback when AI output cannot be used safely.

After deployment, verify HTTP 200 for /, /login, /console, /api/analytics and /healthz while authenticated/authorized where required, and verify /favicon.ico returns 200.
