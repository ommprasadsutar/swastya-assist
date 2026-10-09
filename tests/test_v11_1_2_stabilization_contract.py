from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
INDEX=(ROOT/'templates/index.html').read_text(encoding='utf-8')
PAT=(ROOT/'templates/patient.html').read_text(encoding='utf-8')
PJS=(ROOT/'static/patient.js').read_text(encoding='utf-8')
ADMIN=(ROOT/'templates/admin.html').read_text(encoding='utf-8')
ADMINJS=(ROOT/'static/admin.js').read_text(encoding='utf-8')
JS=(ROOT/'static/app.js').read_text(encoding='utf-8')
CSS=(ROOT/'static/style.css').read_text(encoding='utf-8')

def test_patient_role_and_portal_are_real():
    assert 'PATIENT_ROLE = "patient"' in APP
    assert '@app.route("/patient", methods=["GET"])' in APP
    assert '@require_role("patient")' in APP
    assert 'patient_user_id = db.Column' in APP
    assert 'patient_user_id=(current_user().id if current_user().role == PATIENT_ROLE else None)' in APP
    assert 'patient_account_created' in APP
    assert 'Patient self-entry' in PAT

def test_patient_cannot_use_clinical_case_apis():
    assert '@app.get("/api/cases")\n@require_role("health_worker", "nurse", "doctor", "medical_officer", "reviewer", "admin")' in APP
    assert '@app.get("/api/cases/<cid>")\n@require_role("health_worker", "nurse", "doctor", "medical_officer", "reviewer", "admin")' in APP
    assert 'AI clinical details are not shown here.' in PAT

def test_retention_policy_is_persisted_and_used():
    assert 'class SystemSetting(db.Model)' in APP
    assert 'def current_retention_days()' in APP
    assert '@app.post("/admin/retention/settings")' in APP
    assert 'current_retention_days()' in APP

def test_security_monitoring_counts_and_csrf_audit():
    assert 'security_events_24h' in APP
    assert 'failed_logins_24h' in APP
    assert 'audit("csrf_validation_failed"' in APP
    assert 'adminSecurityEvents' in ADMIN
    assert 'adminFailedLogins' in ADMINJS

def test_information_completeness_guard():
    assert 'def apply_information_completeness(data, symptoms, report):' in APP
    assert 'Insufficient information' in APP
    assert 'The patient narrative is too brief' in APP

def test_intake_and_patient_drafts_are_local_only():
    assert 'TRIAGE_DRAFT_KEY' in JS
    assert 'sessionStorage.setItem(TRIAGE_DRAFT_KEY' in JS
    draft_section=JS[JS.index('function saveTriageDraft'):JS.index('function restoreTriageDraft')]
    assert 'contact_phone' not in draft_section
    assert "swastya_patient_draft_v112" in PJS

def test_safe_error_handlers():
    assert '@app.errorhandler(405)' in APP
    assert '@app.errorhandler(500)' in APP
    assert 'That action is not available here.' in APP
    assert 'The service is temporarily unavailable.' in APP

def test_assets_sync_and_responsive_css():
    assert (ROOT/'static/app.js').read_bytes()==(ROOT/'public/static/app.js').read_bytes()
    assert (ROOT/'static/style.css').read_bytes()==(ROOT/'public/static/style.css').read_bytes()
    assert '@media(max-width:760px)' in CSS


def test_registration_accepts_patient_role_and_creates_active_user():
    start=APP.index('def register():')
    body=APP[start:APP.index('def logout():',start)]
    assert 'CLINICAL_ROLES | {PATIENT_ROLE}' in body
    assert 'role == PATIENT_ROLE' in body
    assert 'active=True' in body
    assert 'patient_account_created' in body

def test_verified_upload_workflow_order_is_enforced():
    start=APP.index('def triage():')
    body=APP[start:APP.index('def case_report(', start)]
    assert body.index('validate_report(raw, mime)') < body.index('verify_uploaded_report_identity(')
    assert body.index('verify_uploaded_report_identity(') < body.index('db.session.add(c)')

def test_invalid_upload_never_persists_case_before_verification():
    start=APP.index('def triage():')
    body=APP[start:APP.index('def case_report(', start)]
    reject=body.index('HEALTH_DOCUMENT_NOT_VERIFIED')
    persist=body.index('db.session.add(c)')
    assert reject < persist

