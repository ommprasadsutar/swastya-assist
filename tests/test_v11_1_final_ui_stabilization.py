from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.py").read_text()
CSS=(ROOT/"static/style.css").read_text()
JS=(ROOT/"static/app.js").read_text()
LANDING=(ROOT/"static/landing.js").read_text()
INDEX=(ROOT/"templates/index.html").read_text()
ADMIN=(ROOT/"templates/admin.html").read_text()
HOME=(ROOT/"templates/home.html").read_text()

def test_final_release_version_and_responsive_shell():
    assert 'APP_VERSION = "11.1.10"' in APP
    assert '@keyframes uiFadeIn' in CSS
    assert 'mobileNavToggle' in INDEX and 'mobileNavBackdrop' in INDEX
    assert 'mobileNavToggle' in ADMIN and 'mobileNavBackdrop' in ADMIN

def test_public_and_clinical_error_sanitization():
    assert 'friendlyError' in JS
    assert 'Interface error: ' not in JS
    assert 'Something went wrong in the interface.' in JS

def test_landing_mobile_navigation():
    assert 'landingMenuToggle' in HOME
    assert 'mobile-open' in LANDING

def test_mobile_responsive_rules_and_reduced_motion():
    assert '@media (max-width:760px)' in CSS
    assert 'body.nav-open .sidebar' in CSS
    assert 'prefers-reduced-motion:reduce' in CSS
