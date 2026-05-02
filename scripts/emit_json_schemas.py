"""Emit JSON Schema for every Pydantic model in src/shared/schemas/.

Output: build/schemas/<module>.<ClassName>.schema.json
Used by:
- scripts/validate_fixtures.py (SPEC-B-017)
- tests/contract/test_frontend_types_match_schemas.py (SPEC-A-105)
"""
from __future__ import annotations

import importlib
import inspect
import json
from typing import Any
import pkgutil
import sys
from pathlib import Path

from pydantic import BaseModel

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "build" / "schemas"
PKG_NAME = "src.shared.schemas"


def _iter_models() -> Any:
    sys.path.insert(0, str(REPO))
    pkg = importlib.import_module(PKG_NAME)
    for mod_info in pkgutil.iter_modules(pkg.__path__, prefix=f"{PKG_NAME}."):
        if mod_info.name.endswith(".__pycache__"):
            continue
        try:
            module = importlib.import_module(mod_info.name)
        except Exception as exc:  # pragma: no cover
            print(f"[skip] {mod_info.name}: {exc}", file=sys.stderr)
            continue
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseModel)
                and obj is not BaseModel
                and obj.__module__ == module.__name__
            ):
                yield mod_info.name.rsplit(".", 1)[-1], name, obj


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for module_short, cls_name, model in _iter_models():
        schema = model.model_json_schema()
        out = OUT_DIR / f"{module_short}.{cls_name}.schema.json"
        out.write_text(json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True))
        count += 1
    print(f"emitted {count} schemas to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
