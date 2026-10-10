from pathlib import Path
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
AUDIT = (ROOT / "FEATURE_152_AUDIT.md").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

ALLOWED = {"Fully working", "Partially working", "Fragile", "Only claimed"}
EXPECTED = {"Fully working": 103, "Partially working": 1, "Fragile": 48}

def rows():
    out=[]
    for line in AUDIT.splitlines():
        m=re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|", line)
        if m:
            out.append((int(m.group(1)), m.group(3).strip()))
    return out

def test_all_152_items_are_present_once_and_statused():
    rs=rows()
    assert len(rs)==152
    assert [i for i,_ in rs]==list(range(1,153))
    assert set(s for _,s in rs) <= ALLOWED
    assert Counter(s for _,s in rs)==EXPECTED

def test_audit_summary_matches_item_rows():
    for label, count in EXPECTED.items():
        assert f"- {label}: **{count}**" in AUDIT

def test_key_current_hardening_items_are_reflected_in_source():
    assert 'if include_sensitive:' in APP
    assert 'app.js?v=40.0' in (ROOT/'templates/index.html').read_text(encoding='utf-8')
    assert 'style.css?v=42.0' in (ROOT/'templates/index.html').read_text(encoding='utf-8')
    assert '__ocrInFlight = false' in JS
    assert 'voiceAiStatus' in JS
    assert 'ADMIN_MANAGED_ROLES' in APP
