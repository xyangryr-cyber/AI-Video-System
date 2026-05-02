"""SPEC-A-105: TS types in src/{shared,frontend}/types match Pydantic schemas.

Strategy:
1. Emit JSON Schema for every Pydantic model in src/shared/schemas/.
2. Extract TS interfaces from src/shared/types/ and src/frontend/types/.
3. For every TS interface whose name matches a Pydantic class name, assert
   field-name parity (same set of required + optional field names).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EMIT = REPO / "scripts" / "emit_json_schemas.py"
EXTRACT = REPO / "scripts" / "extract_ts_types.py"
SCHEMA_DIR = REPO / "build" / "schemas"


@pytest.fixture(scope="module")
def schemas() -> dict[str, dict]:
    subprocess.check_call([sys.executable, str(EMIT)], cwd=REPO)
    out: dict[str, dict] = {}
    for p in sorted(SCHEMA_DIR.glob("*.schema.json")):
        cls = p.stem.split(".", 1)[1].replace(".schema", "")
        out[cls] = json.loads(p.read_text())
    return out


@pytest.fixture(scope="module")
def ts_types() -> dict[str, dict]:
    res = subprocess.run(
        [
            sys.executable,
            str(EXTRACT),
            str(REPO / "src" / "shared" / "types"),
            str(REPO / "src" / "frontend" / "types"),
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert res.returncode == 0, res.stderr
    parsed = json.loads(res.stdout)
    return {t["name"]: t for t in parsed["types"]}


def _required_fields(schema: dict) -> set[str]:
    props = set(schema.get("properties", {}).keys())
    return props


# Documented TS<->Pydantic divergences. Empty after Wave 2 parser fix
# (D14-D17) and SPEC-A reflow (D1, D5-D13). Keep this dict here so that
# new divergences can be allowlisted with explicit reference to a Wave/SPEC.
KNOWN_DIVERGENCES: dict[str, tuple[frozenset[str], frozenset[str]]] = {}


def _find_drift(
    schemas: dict[str, dict],
    ts_types: dict[str, dict],
    known_divergences: dict[str, tuple[frozenset[str], frozenset[str]]] | None = None,
) -> list[str]:
    """Return TS<->Pydantic field-name drift as precise messages.

    Each message names the interface, its source file, and the drifting field
    sets, so AC-4/AC-5 failures point to the exact place to fix.
    """
    known = known_divergences or {}
    mismatches: list[str] = []
    for name, schema in schemas.items():
        if name not in ts_types:
            continue
        ts = ts_types[name]
        ts_field_names = {f["name"] for f in ts["fields"]}
        py_field_names = _required_fields(schema)
        missing_in_ts = py_field_names - ts_field_names
        extra_in_ts = ts_field_names - py_field_names
        known_missing, known_extra = known.get(name, (frozenset(), frozenset()))
        unexpected_missing = missing_in_ts - known_missing
        unexpected_extra = extra_in_ts - known_extra
        if unexpected_missing or unexpected_extra:
            mismatches.append(
                f"{name} ({ts['source']}): "
                f"unexpected_missing_in_ts={sorted(unexpected_missing)}, "
                f"unexpected_extra_in_ts={sorted(unexpected_extra)}"
            )
    return mismatches


def test_all_shared_types_match_schemas(schemas, ts_types):
    mismatches = _find_drift(schemas, ts_types, KNOWN_DIVERGENCES)
    assert not mismatches, "\n".join(mismatches)


def test_missing_field_in_ts_fails():
    """AC-4: dropping a field from a TS interface yields a mismatch message
    naming the interface, its source, and the missing field."""
    from tests.contract.test_frontend_types_match_schemas import _find_drift

    schemas = {
        "ProjectInfo": {"properties": {"project_id": {}, "title": {}, "status": {}}}
    }
    ts_types = {
        "ProjectInfo": {
            "name": "ProjectInfo",
            "fields": [
                {"name": "project_id", "type": "string", "optional": False},
                {"name": "status", "type": "string", "optional": False},
            ],
            "source": "synthetic/ProjectInfo.ts",
        }
    }
    mismatches = _find_drift(schemas, ts_types)
    assert len(mismatches) == 1, mismatches
    msg = mismatches[0]
    assert "ProjectInfo" in msg
    assert "synthetic/ProjectInfo.ts" in msg
    assert "title" in msg
    assert "unexpected_missing_in_ts" in msg


def test_extra_field_in_ts_fails():
    """AC-5: a TS field not present in the Pydantic schema yields a mismatch
    message naming the interface and the extra field."""
    from tests.contract.test_frontend_types_match_schemas import _find_drift

    schemas = {"ProjectInfo": {"properties": {"project_id": {}}}}
    ts_types = {
        "ProjectInfo": {
            "name": "ProjectInfo",
            "fields": [
                {"name": "project_id", "type": "string", "optional": False},
                {"name": "ghost_field", "type": "string", "optional": False},
            ],
            "source": "synthetic/ProjectInfo.ts",
        }
    }
    mismatches = _find_drift(schemas, ts_types)
    assert len(mismatches) == 1, mismatches
    msg = mismatches[0]
    assert "ProjectInfo" in msg
    assert "ghost_field" in msg
    assert "unexpected_extra_in_ts" in msg


def test_known_divergence_is_silenced():
    """Drift listed in KNOWN_DIVERGENCES must not appear as a mismatch (regression
    guard: allowlist is honored both for missing_in_ts and extra_in_ts)."""
    from tests.contract.test_frontend_types_match_schemas import _find_drift

    schemas = {"Foo": {"properties": {"a": {}, "b": {}}}}
    ts_types = {
        "Foo": {
            "name": "Foo",
            "fields": [
                {"name": "a", "type": "string", "optional": False},
                {"name": "legacy", "type": "string", "optional": False},
            ],
            "source": "synthetic/Foo.ts",
        }
    }
    known = {"Foo": (frozenset({"b"}), frozenset({"legacy"}))}
    mismatches = _find_drift(schemas, ts_types, known)
    assert mismatches == []
