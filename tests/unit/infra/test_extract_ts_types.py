"""SPEC-A-105 AC-2: extract_ts_types parses TS interfaces and type aliases."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "extract_ts_types.py"


def _run(*paths: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_parses_simple_interface(tmp_path):
    f = tmp_path / "x.ts"
    f.write_text("export interface Foo { a: string; b: number }")
    out = _run(tmp_path)
    foo = next(t for t in out["types"] if t["name"] == "Foo")
    fields = {fld["name"]: fld for fld in foo["fields"]}
    assert fields["a"]["type"] == "string" and not fields["a"]["optional"]
    assert fields["b"]["type"] == "number" and not fields["b"]["optional"]


def test_marks_optional_fields(tmp_path):
    f = tmp_path / "x.ts"
    f.write_text("export interface Bar { a?: string; b: number | null }")
    out = _run(tmp_path)
    bar = next(t for t in out["types"] if t["name"] == "Bar")
    fields = {fld["name"]: fld for fld in bar["fields"]}
    assert fields["a"]["optional"] is True
    assert "null" in fields["b"]["type"]


def test_strips_line_comments_with_braces(tmp_path):
    """B1 regression: comment containing {placeholder} must not truncate body."""
    f = tmp_path / "x.ts"
    f.write_text(
        "export interface Foo {\n"
        "  a: string;\n"
        "  // path /api/{id}/items\n"
        "  b: number;\n"
        "}\n"
    )
    out = _run(f)
    types = {t["name"]: t for t in out["types"]}
    assert "Foo" in types
    names = {fld["name"] for fld in types["Foo"]["fields"]}
    assert names == {"a", "b"}, f"expected both a and b, got {names}"


def test_does_not_skip_field_named_type(tmp_path):
    """B2 regression: a field literally named 'type' must be parsed."""
    f = tmp_path / "y.ts"
    f.write_text('export interface Tag {\n  type: "discrete";\n  value: string;\n}\n')
    out = _run(f)
    types = {t["name"]: t for t in out["types"]}
    assert "Tag" in types
    names = {fld["name"] for fld in types["Tag"]["fields"]}
    assert names == {"type", "value"}, f"expected type+value, got {names}"
