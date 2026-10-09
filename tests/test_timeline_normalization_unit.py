import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_normalizer():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_normalize_timeline_value")
    module = ast.Module(body=[node], type_ignores=[])
    ns = {}
    exec(compile(ast.fix_missing_locations(module), "app.py", "exec"), ns)
    return ns["_normalize_timeline_value"]


def test_timeline_string_remains_string():
    normalize = load_normalizer()
    assert normalize("Day 1: fever began") == "Day 1: fever began"


def test_timeline_list_becomes_text():
    normalize = load_normalizer()
    assert normalize(["Day 1: fever", "Day 3: cough"]) == "Day 1: fever; Day 3: cough"


def test_timeline_nested_object_becomes_text():
    normalize = load_normalizer()
    value = [{"day": 1, "event": "fever began"}, {"day": 3, "event": "cough"}]
    result = normalize(value)
    assert "day: 1" in result and "event: fever began" in result
