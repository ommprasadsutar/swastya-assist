from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
BOOT=(ROOT/'static/boot.js').read_text(encoding='utf-8')
LOGIN=(ROOT/'static/login.js').read_text(encoding='utf-8')
CSS=(ROOT/'static/style.css').read_text(encoding='utf-8')
ADMIN=(ROOT/'templates/admin.html').read_text(encoding='utf-8')


def test_role_guard_redirects_browser_and_json_for_api():
    start=APP.index('def require_role(*roles):')
    section=APP[start:APP.index('def get_login_csrf_secret', start)]
    assert 'if request.path.startswith("/api/"):' in section
    assert 'Authentication required' in section
    assert 'You do not have permission to use this area.' in section
    assert 'u.role == PATIENT_ROLE' in section
    assert 'u.role == "admin"' in section


def test_safe_next_url_enforces_role_boundaries():
    start=APP.index('def safe_next_url(')
    end=APP.index('\n@app.route("/login"', start)
    body=APP[start:end]
    assert 'path.startswith("/api/")' in body
    assert 'role == PATIENT_ROLE' in body
    assert 'path.startswith(("/console", "/admin"))' in body
    assert 'role == "admin"' in body
    assert 'path.startswith("/patient")' in body
    assert 'role in CLINICAL_ROLES' in body


def test_boot_does_not_expose_browser_error_message():
    assert 'Interactive console error:' not in BOOT
    assert "Something went wrong in the console. Please refresh and try again." in BOOT


def test_login_prevents_duplicate_submit():
    assert "dataset.submitting === '1'" in LOGIN
    assert "Signing in…" in LOGIN
    assert "aria-busy" in LOGIN


def test_responsive_admin_tables_and_login_roles():
    assert '.admin-table-wrap' in CSS
    assert 'role-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}' in CSS
    assert '@media(max-width:900px) and (min-width:561px)' in CSS
    assert ADMIN.count('class="admin-table-wrap"') == 6
