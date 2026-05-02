"""SPEC-B-017 AC-3: validate every JSON fixture against its declared schema.

Convention: fixture file `tests/fixtures/api/<group>/<name>.json` declares
its target schema via a sibling `_index.json` mapping:

    {
      "list_response.json": {"schema": "project_state.ProjectListResponse"},
      "detail_p3.json": {"schema": "project_state.ProjectStateResponse"}
    }

Schemas are looked up under build/schemas/ (emit via emit_json_schemas.py).
"""
from __future__ import annotations

import json
import subprocess
from typing import Any, cast
import sys
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[1]
FIX_ROOT = REPO / "tests" / "fixtures" / "api"
SCHEMA_ROOT = REPO / "build" / "schemas"


def _ensure_schemas() -> None:
    if not SCHEMA_ROOT.exists() or not any(SCHEMA_ROOT.glob("*.schema.json")):
        subprocess.check_call([sys.executable, str(REPO / "scripts" / "emit_json_schemas.py")])


def _load_index(group_dir: Path) -> dict[str, dict[str, Any]]:
    idx = group_dir / "_index.json"
    if not idx.exists():
        return {}
    return cast(dict[str, dict[str, Any]], json.loads(idx.read_text()))


def main() -> int:
    _ensure_schemas()
    failures: list[str] = []
    for group_dir in sorted(p for p in FIX_ROOT.iterdir() if p.is_dir()):
        index = _load_index(group_dir)
        for fix in sorted(group_dir.glob("*.json")):
            if fix.name == "_index.json":
                continue
            entry = index.get(fix.name)
            if not entry:
                failures.append(f"{fix.relative_to(REPO)}: not registered in {group_dir.name}/_index.json")
                continue
            schema_name = entry["schema"]
            schema_file = SCHEMA_ROOT / f"{schema_name}.schema.json"
            if not schema_file.exists():
                failures.append(f"{fix.relative_to(REPO)}: schema {schema_name} not emitted")
                continue
            payload = json.loads(fix.read_text())
            schema_doc = json.loads(schema_file.read_text())
            items = payload if entry.get("list") else [payload]
            for idx, item in enumerate(items):
                try:
                    jsonschema.validate(instance=item, schema=schema_doc)
                except jsonschema.ValidationError as exc:
                    suffix = f"[{idx}]" if entry.get("list") else ""
                    failures.append(f"{fix.relative_to(REPO)}{suffix}: {exc.message}")
    if failures:
        print("FIXTURE VALIDATION FAILED:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("all fixtures valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
