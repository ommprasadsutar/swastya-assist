# Swastya Assist V11.0.5 — Complete Feature List

## Patient and intake workflow
1. Synthetic patient/encounter intake
2. Patient reference generation/validation
3. Patient name, age, gender and synthetic locality/facility reference
4. Preferred-language selection
5. Seven care scenarios plus referral preparation
6. Consent confirmation and consent metadata

## Multilingual and voice
7. English, Hindi, Bengali, Marathi, Tamil, Telugu, Odia, Kannada, Malayalam, Punjabi, Gujarati, Assamese and Urdu UI/workflow language set
8. Browser microphone recording
9. Live browser transcript where supported
10. Audio playback
11. Optional Gemini transcription
12. Optional Gemini translation into a selected target language
13. Browser/connection-safe fallback when Gemini is unavailable

## Reports and documents
14. PNG/JPG/JPEG/PDF report upload
15. Upload size/type/content validation
16. Secure database-backed report storage
17. Original report retrieval for authorized reviewers
18. Local PDF text extraction
19. Optional Gemini multimodal report understanding
20. Structured extracted report fields

## AI triage
21. Structured reviewer-facing AI triage note
22. Symptom/narrative summarization
23. Timeline summarization
24. Key-detail extraction
25. Missing/unclear information detection
26. Suggested follow-up questions
27. Urgency/risk signal tagging
28. Evidence/source mapping
29. Scenario-aware context

## AI safety and reliability
30. Strict Gemini response validation
31. Untrusted patient/report data boundaries
32. Prompt-injection/data-boundary protection
33. Rules-based urgency overlay
34. Safer negation/history handling for urgency signals
35. AI output remains advisory and reviewer-facing
36. No diagnosis, prescription or treatment recommendation functionality
37. AI failure -> clearly labeled manual-review fallback
38. Single-attempt/controlled retry behavior with durable AI request claims
39. No automatic model/provider fallback
40. Direct Gemini GenerateContent REST transport retained

## Reviewer dashboard and human-in-the-loop review
41. Reviewer/doctor dashboard
42. Facility-scoped review queue
43. Risk-prioritized queue sorting
44. Case detail drawer/workspace
45. AI priority shown separately from human final operational priority
46. Human final priority selection
47. Reviewer priority override reason
48. Reviewer status: Needs review / Reviewed / Escalated / Needs more information
49. Explicit Insufficient information priority
50. Reviewer notes
51. Urgent-review human verification before finalizing urgent/escalated decisions
52. Evidence verification: Pending / Verified / Rejected / Unclear
53. Persisted follow-up answers
54. Follow-up answer verification
55. Original report view
56. Printable reviewer packet

## Referral and handoff
57. Referral/handoff status: Not required / Draft / Ready / Sent / Acknowledged / Completed
58. Referral destination validation
59. Escalation requires an active handoff destination
60. State-transition guardrails
61. Handoff acknowledgement timestamp

## Urgent patient contact
62. Reviewer-controlled optional patient/caregiver contact workflow
63. Contact is never initiated automatically by AI
64. Explicit contact consent
65. Encrypted contact number storage
66. Demo mode accepts only the synthetic test number +1-555-010-0100
67. Authorized reviewer Call patient action using client-side tel: handoff
68. Contact-attempt audit metadata without storing the number in the audit event

## Facility, identity and governance
69. Facility model and default synthetic facility
70. User facility isolation
71. Case facility isolation
72. Registration-request facility isolation
73. Patient/clinical access roles
74. Admin approval for Doctor/Reviewer access requests
75. Admin user creation, enable/disable and deletion
76. Synthetic patient encounter deletion

## Consent, privacy and security
77. Consent version
78. Consent timestamp
79. Consent language
80. Consent collection context
81. Synthetic/public-data protection
82. Detection/blocking of phone, email, Aadhaar-like and PAN-like direct identifiers in demo intake
83. Optional Fernet encryption for sensitive database text
84. Optional Fernet encryption for stored report bytes
85. CSRF protection
86. Login CSRF protection
87. Secure/HttpOnly/SameSite cookies
88. HTTPS-aware secure-cookie configuration
89. Security response headers
90. Content-size limits
91. Upload/MIME validation
92. Rate limiting with Redis/Upstash-compatible storage
93. Facility-aware protected case access
94. Audit trail
95. Retention cleanup and retention cron endpoint

## Operations, analytics and deployment
96. Analytics dashboard: total, urgent, reviewed, review rate
97. Risk distribution analytics
98. Language mix analytics
99. Workflow status analytics
100. Health endpoint `/healthz`
101. Readiness endpoint `/readyz`
102. Gemini diagnostics
103. Vercel + Flask deployment support
104. PostgreSQL support
105. SQLite local compatibility
106. Docker/Gunicorn support
107. Idempotent PostgreSQL V10.x -> V11 migration without deleting existing data
108. SQLite V11 column migration
109. Correct PostgreSQL TEXT storage for encrypted reviewer/referral fields
110. Review UI cache-busting
111. Synchronized `public/static` assets
112. `/favicon.ico` route
113. Existing users/cases preserved through schema migration
114. Existing UI structure preserved

## Safety boundary
Swastya Assist is a human-in-the-loop triage-support prototype. It structures patient-reported information, highlights urgency signals, prioritizes reviewer work, supports verification and referral preparation, and records human decisions. It does not independently diagnose, prescribe, or recommend treatment.
