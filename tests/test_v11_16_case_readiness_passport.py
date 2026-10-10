from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

def test_passport_view_is_added_without_removing_core_views():
    html = (BASE / "templates" / "index.html").read_text(encoding="utf-8")
    for view in ("intake", "dashboard", "readiness", "ocr", "analytics"):
        assert f'data-view="{view}"' in html
        assert f'id="view-{view}"' in html
    assert "Case Readiness Passport" in html

def test_passport_preview_is_explicitly_local_only():
    js = (BASE / "static" / "app.js").read_text(encoding="utf-8")
    block = js[js.index("// Case Readiness Passport:"):]
    assert "LOCAL_DEMO_PREVIEW_ONLY" in block
    assert "will_call_gemini: false" in block
    assert "will_persist_to_database: false" in block
    assert "will_sync_to_server: false" in block
    assert "localStorage" not in block
    assert "sessionStorage" not in block

def test_export_controls_and_consent_gate_exist():
    html = (BASE / "templates" / "index.html").read_text(encoding="utf-8")
    js = (BASE / "static" / "app.js").read_text(encoding="utf-8")
    for item in ("rpCopy", "rpExport", "rpClear"):
        assert f'id="{item}"' in html
        assert f"$rp('{item}')" in js
    assert "!offline || !consent" in js
    assert "!consent" in js

def test_public_assets_mirror_the_updated_local_assets():
    assert (BASE / "public" / "static" / "app.js").read_bytes() == (BASE / "static" / "app.js").read_bytes()
    assert (BASE / "public" / "static" / "style.css").read_bytes() == (BASE / "static" / "style.css").read_bytes()


def test_landing_page_explains_demo_without_claiming_a_clinical_score():
    home = (BASE / "templates" / "home.html").read_text(encoding="utf-8")
    assert "Case Readiness Passport · Demo" in home
    assert "not a clinical-risk score" in home

def test_asset_cache_busting_is_updated():
    html = (BASE / "templates" / "index.html").read_text(encoding="utf-8")
    assert "/static/style.css?v=42.0" in html
    assert "/static/app.js?v=40.0" in html
