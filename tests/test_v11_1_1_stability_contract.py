from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
JS = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
ADMIN = (ROOT / 'templates' / 'admin.html').read_text(encoding='utf-8')
ADMIN_JS = (ROOT / 'static' / 'admin.js').read_text(encoding='utf-8')

def test_release_version_and_asset_sync():
    assert 'APP_VERSION = "11.1.10"' in APP
    assert (ROOT/'static'/'app.js').read_bytes() == (ROOT/'public'/'static'/'app.js').read_bytes()
    assert (ROOT/'static'/'style.css').read_bytes() == (ROOT/'public'/'static'/'style.css').read_bytes()
    assert (ROOT/'static'/'admin.js').read_bytes() == (ROOT/'public'/'static'/'admin.js').read_bytes()

def test_analytics_is_facility_scoped():
    body = APP[APP.index('def analytics():'):APP.index('def diagnostics():')]
    assert 'cases = facility_case_query().all()' in body
    assert 'Case.query.all()' not in body

def test_queue_serialization_hides_contact_data():
    assert 'def serialize_case(c, *, include_sensitive=False):' in APP
    cases_body = APP[APP.index('def cases_api():'):APP.index('def case_api(cid):')]
    detail_body = APP[APP.index('def case_api(cid):'):APP.index('def referral_transition_allowed')]
    assert 'serialize_case(c, include_sensitive=False)' in cases_body
    assert 'serialize_case(c, include_sensitive=True)' in detail_body
    serializer = APP[APP.index('def serialize_case'):APP.index('def risk_sort_key')]
    assert 'if include_sensitive:' in serializer
    sensitive_block = serializer[serializer.index('if include_sensitive:'):]
    assert 'contact_phone' in sensitive_block and 'contact_consent' in sensitive_block

def test_referral_lifecycle_is_forward_only():
    assert 'REFERRAL_TRANSITIONS' in APP
    assert '"Not required": {"Not required", "Draft"}' in APP
    assert '"Draft": {"Draft", "Ready"}' in APP
    assert '"Ready": {"Ready", "Sent"}' in APP
    assert '"Sent": {"Sent", "Acknowledged"}' in APP
    assert '"Acknowledged": {"Acknowledged", "Completed"}' in APP
    assert 'if not referral_transition_allowed(c.referral_status, referral_status)' in APP
    assert 'if not referral_transition_allowed(c.referral_status, status)' in APP

def test_voice_draft_survives_initial_page_setup():
    assert 'function resetVoiceUI(clearDraft = false)' in JS
    assert 'if(clearDraft){try{sessionStorage.removeItem(VOICE_DRAFT_KEY);}' in JS
    assert 'restoreVoiceDraft();' in JS
    assert 'resetVoiceUI(false);' in JS
    assert JS.index('resetVoiceUI(false);') < JS.index('restoreVoiceDraft();')
    assert 'window.__swastyaResetVoice = () => resetVoiceUI(true);' in JS

def test_voice_uses_structured_gemini_response_schema():
    assert '_direct_gemini_generate_content(GEMINI_VOICE_MODEL, voice_items, response_schema=GEMINI_VOICE_RESPONSE_SCHEMA)' in APP

def test_admin_scope_management_and_operations_ui_present():
    for marker in ('/admin/facilities', '/admin/facilities/{{f.id}}/toggle', '/admin/users/{{u.id}}/facility', '/admin/users/{{u.id}}/role', '/admin/retention'):
        assert marker in ADMIN
    for marker in ('/api/admin/system', '/api/admin/audit', 'adminSystemBadge', 'auditTable'):
        assert marker in ADMIN_JS or marker in ADMIN

def test_no_raw_stacktrace_ui_copy_in_frontend():
    blob = (ROOT/'static'/'app.js').read_text() + (ROOT/'static'/'admin.js').read_text()
    assert 'Traceback' not in blob
    assert 'Internal Server Error' not in blob


def test_multilingual_local_relevance_gate_preserves_unicode() :
    marker = 'def health_relevance_error(symptoms, report, filename="", has_upload=False):'
    section = APP[APP.index(marker):APP.index('def validate_report', APP.index(marker))]
    assert 'body.casefold()' in section
    assert 're.sub(r"\\s+", " ", body.casefold())' in section
    assert 'context_present = any(_unrelated_term_present(normalized, term) for term in HEALTH_CONTEXT_TERMS)' in section
    assert '[^a-z0-9+/#.' not in section

def test_ocr_inflight_lock_is_released() :
    assert '__ocrInFlight = false' in JS
    assert 'finally { __ocrInFlight = false; setBusy(btn,false); }' in JS

def test_voice_retry_uses_accessible_status_region() :
    section = JS[JS.index("voiceAi?.addEventListener"):JS.index('// Report upload previews')]
    assert 'voiceAiStatus' in section
    assert "document.createElement('button')" in section
    assert '.innerHTML =' not in section

def test_clinical_role_copy_covers_all_supported_roles() :
    login = (ROOT/'templates/login.html').read_text(encoding='utf-8')
    register = (ROOT/'templates/register.html').read_text(encoding='utf-8')
    for role in ('Health Worker','Nurse','Doctor','Medical Officer','Reviewer'):
        assert role in register
    assert 'Authorized clinical team members are routed to the Clinical Console.' in login
