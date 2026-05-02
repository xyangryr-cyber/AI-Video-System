"""Cross-language schema alignment checker.

Usage:
    python scripts/contracts/check_schema_alignment.py <name> [<name> ...]

For each <name>, verifies that every Pydantic BaseModel defined in
``src/shared/schemas/<name>.py`` has its ``model_fields`` set equal to the
field set of the same-named TypeScript interface in
``src/shared/types/<name>.ts`` (with ``extends`` inheritance flattened).

Exit code: 0 if all bundles align, 1 on mismatch or import failure, 2 on
invalid arguments.

Closes the PROGRESS.md open follow-up referenced by SPEC-A-013..A-017
verification commands. Equivalent to the per-file
``test_pydantic_ts_alignment_*`` assertions, surfaced as a CLI so task cards
can invoke it without opening pytest.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TYPES_ROOT = REPO_ROOT / "src" / "shared" / "types"
DEFAULT_SCHEMAS_MODULE_PREFIX = "src.shared.schemas"


# ---------------------------------------------------------------------------
# TS parser (single-file, with `extends` resolution).
# ---------------------------------------------------------------------------

_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(text: str) -> str:
    text = _BLOCK_COMMENT.sub("", text)
    text = _LINE_COMMENT.sub("", text)
    return text


def _find_interface_body(text: str, name: str) -> tuple[str, list[str]] | None:
    """Find `interface <name> [extends A, B] { ... }` and return (body, parents).

    Accepts both `export interface` and bare `interface`.
    """
    pattern = re.compile(
        rf"\binterface\s+{re.escape(name)}\b\s*(?:extends\s+([^{{]+))?\{{",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        return None
    parents_raw = m.group(1) or ""
    parents = [p.strip() for p in parents_raw.split(",") if p.strip()]
    start = m.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    body = text[start : i - 1]
    return body, parents


def _extract_field_names(body: str) -> set[str]:
    """Extract top-level field names from an interface body (nested braces ignored)."""
    fields: set[str] = set()
    # Collapse nested `{ ... }` blocks so their inner field-like tokens are not
    # picked up. Run until stable (handles nesting >1 deep).
    flat = body
    while True:
        reduced = re.sub(r"\{[^{}]*\}", "", flat, flags=re.DOTALL)
        if reduced == flat:
            break
        flat = reduced
    for logical in flat.split(";"):
        logical = logical.strip()
        if not logical:
            continue
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\??:", logical)
        if m:
            fields.add(m.group(1))
    return fields


def parse_ts_interfaces(ts_path: Path) -> dict[str, set[str]]:
    """Return {interface_name: set(field_names)} for every interface in the file,
    flattening `extends` inheritance within the same file."""
    text = _strip_comments(ts_path.read_text(encoding="utf-8"))
    # First pass: collect every interface's own body + its declared parents.
    own_fields: dict[str, set[str]] = {}
    parents_of: dict[str, list[str]] = {}
    # Iterate over all interface declarations in order.
    for m in re.finditer(
        r"\binterface\s+([A-Za-z_][A-Za-z0-9_]*)\b", text
    ):
        name = m.group(1)
        if name in own_fields:
            continue
        found = _find_interface_body(text, name)
        if found is None:
            continue
        body, parents = found
        own_fields[name] = _extract_field_names(body)
        parents_of[name] = parents

    # Second pass: resolve `extends` transitively (depth-first, cycle-safe).
    resolved: dict[str, set[str]] = {}

    def _resolve(name: str, stack: tuple[str, ...] = ()) -> set[str]:
        if name in resolved:
            return resolved[name]
        if name in stack:
            return set()  # cycle: stop
        acc = set(own_fields.get(name, set()))
        for parent in parents_of.get(name, []):
            acc |= _resolve(parent, stack + (name,))
        resolved[name] = acc
        return acc

    for name in own_fields:
        _resolve(name)
    return resolved


# ---------------------------------------------------------------------------
# Pydantic introspection.
# ---------------------------------------------------------------------------


def pydantic_classes_in_module(module: ModuleType) -> dict[str, set[str]]:
    """Return {class_name: set(model_fields)} for BaseModel subclasses defined
    in ``module`` (imports from other modules are filtered out)."""
    result: dict[str, set[str]] = {}
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if name.startswith("_"):
            continue
        if not issubclass(cls, BaseModel):
            continue
        if cls is BaseModel:
            continue
        if getattr(cls, "__module__", None) != module.__name__:
            continue
        result[name] = set(cls.model_fields.keys())
    return result


# ---------------------------------------------------------------------------
# Core alignment check.
# ---------------------------------------------------------------------------


def check_alignment(
    name: str,
    ts_path: Path,
    module: ModuleType,
) -> list[str]:
    """Return a list of human-readable error strings; empty means aligned."""
    errors: list[str] = []
    ts_ifaces = parse_ts_interfaces(ts_path)
    py_classes = pydantic_classes_in_module(module)
    if not py_classes:
        errors.append(
            f"{name}: no Pydantic BaseModel classes found in module "
            f"{module.__name__!r}"
        )
        return errors
    for cls_name, py_fields in sorted(py_classes.items()):
        if cls_name not in ts_ifaces:
            errors.append(
                f"{name}.{cls_name}: Pydantic class has no TS interface counterpart "
                f"in {ts_path.name}"
            )
            continue
        ts_fields = ts_ifaces[cls_name]
        if py_fields != ts_fields:
            py_only = sorted(py_fields - ts_fields)
            ts_only = sorted(ts_fields - py_fields)
            errors.append(
                f"{name}.{cls_name}: field mismatch "
                f"py_only={py_only} ts_only={ts_only}"
            )
    return errors


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def _check_one(
    name: str,
    types_root: Path,
    module_prefix: str,
) -> list[str]:
    ts_path = types_root / f"{name}.ts"
    if not ts_path.exists():
        return [f"{name}: TS file not found at {ts_path}"]
    try:
        module = importlib.import_module(f"{module_prefix}.{name}")
    except ModuleNotFoundError as exc:
        return [f"{name}: Pydantic module import failed: {exc}"]
    return check_alignment(name, ts_path, module)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify Pydantic<->TypeScript field parity for one or more "
            "shared-schema bundles."
        )
    )
    parser.add_argument(
        "names",
        nargs="+",
        help="Schema stem(s), e.g. `chart_material` or `sfx_layout_plan sfx_mix_segments`.",
    )
    parser.add_argument(
        "--types-root",
        type=Path,
        default=DEFAULT_TYPES_ROOT,
        help=f"Root directory for TS type files (default: {DEFAULT_TYPES_ROOT}).",
    )
    parser.add_argument(
        "--module-prefix",
        default=DEFAULT_SCHEMAS_MODULE_PREFIX,
        help=f"Python import prefix for schema modules (default: {DEFAULT_SCHEMAS_MODULE_PREFIX}).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Ensure REPO_ROOT is importable so `src.shared.schemas.*` resolves when
    # the script is invoked directly (not via `python -m`).
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    all_errors: list[str] = []
    for name in args.names:
        errs = _check_one(name, args.types_root, args.module_prefix)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK: {name}")

    if all_errors:
        print("", file=sys.stderr)
        for e in all_errors:
            print(f"MISMATCH: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
