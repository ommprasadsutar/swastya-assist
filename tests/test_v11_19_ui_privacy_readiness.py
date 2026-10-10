from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")
OFFLINE_HTML = (ROOT / "templates" / "offline_capture.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


def test_checkbox_rules_override_text_input_sizing():
    assert 'input[type="checkbox"],input[type="radio"]' in CSS
    assert "min-height:18px!important" in CSS
    assert "flex:0 0 18px" in CSS


def test_workspace_header_and_navigation_are_consistent():
    assert '<h1 id="pageTitle">{% if current_user.role == "admin" %}Admin Console{% else %}Clinical Console{% endif %}</h1>' in INDEX
    assert "AI Reports &amp; OCR" in INDEX
    assert "Privacy &amp; Security Overview" in INDEX
    assert "PS03 Demo Simulator" in INDEX
    assert "textContent = document.body?.dataset.userRole === 'admin' ? 'Admin Console' : 'Clinical Console'" in JS
    assert '{% if current_user.role == "admin" %}Admin dashboard' in INDEX


def test_passport_is_unambiguously_a_simulator_and_consent_is_not_prechecked():
    assert "SIMULATOR ONLY" in INDEX
    assert 'id="rpConsent" type="checkbox"><span>' in INDEX
    assert "Add simulated item" in INDEX
    assert "Simulate reconnect" in INDEX
    assert "live synchronization test" in INDEX
    assert "rpConsent: false" in JS


def test_demo_serialization_masks_legacy_direct_identifiers():
    assert '"patient_name": "Demo patient" if DEMO_ONLY_MODE else c.patient_name' in APP
    assert '"address": "Synthetic facility / locality" if DEMO_ONLY_MODE else c.address' in APP
    assert 'def _demo_safe_value(value, known_name=""):' in APP
    assert '"contact_phone": "" if DEMO_ONLY_MODE else' in APP
    assert 'def _demo_safe_reference(value, case_id):' in APP


def test_rate_limit_store_reads_vercel_redis_integration_and_checks_backend():
    assert 'os.getenv("swastya_assist_REDIS_URL", "").strip()' in APP
    assert 'rate_store.startswith(("redis://", "rediss://"))' in APP
    assert "limiter.limiter.storage.check()" in APP
    assert "rate_limit_store" in APP


def test_privacy_copy_matches_the_actual_redacted_derivative_flow():
    assert "only the redacted derivative if redaction and report-identity checks succeed" in INDEX
    assert "OCR can miss identifiers" in INDEX
    assert "A failed required redaction or report-identity check blocks external transfer" in INDEX
    assert 'data-view="privacy"' in INDEX
    assert 'id="view-privacy"' in INDEX


def test_offline_style_cache_is_bumped_and_service_worker_avoids_sensitive_pages():
    assert "/static/offline_capture.css?v=2" in OFFLINE_HTML
    assert "/static/offline_capture.js?v=2" in OFFLINE_HTML
    assert "swastya-offline-shell-v119" in SW
    for route in ("'/console'", "'/login'", "'/register'", "'/admin'", "'/logout'"):
        assert route in SW


def test_core_views_and_public_asset_mirrors_remain():
    for view in ("intake", "dashboard", "ocr", "analytics", "privacy"):
        assert f'data-view="{view}"' in INDEX
        assert f'id="view-{view}"' in INDEX
    assert 'href="/offline-capture"' in INDEX
    assert (ROOT / "static" / "app.js").read_bytes() == (ROOT / "public" / "static" / "app.js").read_bytes()
    assert (ROOT / "static" / "style.css").read_bytes() == (ROOT / "public" / "static" / "style.css").read_bytes()
    assert (ROOT / "static" / "offline_capture.css").read_bytes() == (ROOT / "public" / "static" / "offline_capture.css").read_bytes()
