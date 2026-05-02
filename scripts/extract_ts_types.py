"""SPEC-A-105 AC-2: extract TypeScript interfaces and type aliases.

Output (stdout): JSON {"types": [{"name", "fields": [{"name","type","optional"}]}, ...]}.
This is a deliberately limited parser -- it handles the patterns used in
src/shared/types/*.ts and src/frontend/types/*.ts. If/when type complexity
grows, replace with a Node-side AST tool invoked via subprocess.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

LINE_COMMENT_RE = re.compile(r"//[^\n]*")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

INTERFACE_RE = re.compile(
    r"export\s+interface\s+(?P<name>\w+)\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE | re.DOTALL,
)
FIELD_RE = re.compile(
    r"(?:^|(?<=;))\s*(?P<name>\w+)(?P<opt>\?)?\s*:\s*(?P<type>[^;{}]+?)\s*(?=;|}|$)",
    re.MULTILINE,
)


def _strip_comments(text: str) -> str:
    """Remove TS // line and /* */ block comments before regex parsing.

    Without this, comment text like `// /api/{id}/...` causes INTERFACE_RE
    body matcher `[^}]*` to terminate early at the `}` inside the URL.
    """
    text = LINE_COMMENT_RE.sub("", text)
    text = BLOCK_COMMENT_RE.sub("", text)
    return text


def parse_file(path: Path) -> list[dict[str, Any]]:
    text = _strip_comments(path.read_text(encoding="utf-8"))
    types: list[dict[str, Any]] = []
    for m in INTERFACE_RE.finditer(text):
        body = m.group("body")
        fields: list[dict[str, Any]] = []
        for fm in FIELD_RE.finditer(body):
            name = fm.group("name")
            # Filter only TS keywords that would never be valid field names.
            # `type` IS a valid field name (e.g. discriminator) — do NOT skip it.
            if name in {"interface", "export"}:
                continue
            fields.append({
                "name": name,
                "type": fm.group("type").strip(),
                "optional": bool(fm.group("opt")),
            })
        types.append({"name": m.group("name"), "fields": fields, "source": str(path)})
    return types


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: extract_ts_types.py <dir-or-file> [...]", file=sys.stderr)
        return 2
    out: list[dict[str, Any]] = []
    for arg in argv:
        p = Path(arg)
        files = [p] if p.is_file() else sorted(p.rglob("*.ts"))
        for f in files:
            out.extend(parse_file(f))
    json.dump({"types": out}, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
