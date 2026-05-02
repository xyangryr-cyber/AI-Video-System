#!/usr/bin/env python3
"""[GAPFIX-030] Cross-language error code consistency checker and generator.

Verifies that the 17 EVID_ error codes are consistent across:
  - src/shared/contracts/error_codes.py
  - src/shared/contracts/error_codes.ts

Usage:
  python3 scripts/generate_error_codes.py           # regenerate TS from PY source
  python3 scripts/generate_error_codes.py --check   # exit 0 if consistent, 1 if not
  python3 scripts/generate_error_codes.py --help
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONTRACT_PY = os.path.join(PROJECT_ROOT, "src", "shared", "contracts", "error_codes.py")
CONTRACT_TS = os.path.join(PROJECT_ROOT, "src", "shared", "contracts", "error_codes.ts")

EXPECTED_COUNT = 17


# ---------------------------------------------------------------------------
# extractors (Python source)
# ---------------------------------------------------------------------------

def _extract_py_error_codes(path: str) -> Dict[str, str]:
    """Extract {EVID_XXXX: value} from the ErrorCode enum in error_codes.py."""
    if not os.path.isfile(path):
        return {}
    codes: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(r'^\s+(EVID_\d{4})\s*=\s*"([^"]+)"', content, re.MULTILINE):
        codes[m.group(1)] = m.group(2)
    return codes


def _extract_py_http_map(path: str) -> Dict[str, int]:
    """Extract {EVID_XXXX: http_status} from ERROR_CODE_HTTP_MAP."""
    if not os.path.isfile(path):
        return {}
    mapping: Dict[str, int] = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(
        r'ErrorCode\.(EVID_\d{4})\.value:\s*(\d{3})', content
    ):
        mapping[m.group(1)] = int(m.group(2))
    return mapping


def _extract_py_message_map(path: str) -> Dict[str, str]:
    """Extract {EVID_XXXX: message} from ERROR_CODE_MESSAGE_MAP."""
    if not os.path.isfile(path):
        return {}
    mapping: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(
        r'ErrorCode\.(EVID_\d{4})\.value:\s*"((?:[^"\\]|\\.)*)"', content
    ):
        mapping[m.group(1)] = m.group(2)
    return mapping


# ---------------------------------------------------------------------------
# extractors (TypeScript target)
# ---------------------------------------------------------------------------

def _extract_ts_error_codes(path: str) -> Dict[str, str]:
    """Extract {EVID_XXXX: value} from the ERROR_CODES const in error_codes.ts."""
    if not os.path.isfile(path):
        return {}
    codes: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(r'\b(EVID_\d{4}):\s*"([^"]+)"', content):
        codes[m.group(1)] = m.group(2)
    return codes


def _extract_ts_http_map(path: str) -> Dict[str, int]:
    """Extract {EVID_XXXX: http_status} from ERROR_CODE_HTTP_MAP in TS."""
    if not os.path.isfile(path):
        return {}
    mapping: Dict[str, int] = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(
        r'\[ERROR_CODES\.(EVID_\d{4})\]:\s*(\d{3})', content
    ):
        mapping[m.group(1)] = int(m.group(2))
    return mapping


def _extract_ts_message_map(path: str) -> Dict[str, str]:
    """Extract {EVID_XXXX: message} from ERROR_CODE_MESSAGE_MAP in TS."""
    if not os.path.isfile(path):
        return {}
    mapping: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(
        r'\[ERROR_CODES\.(EVID_\d{4})\]:\s*"((?:[^"\\]|\\.)*)"', content
    ):
        mapping[m.group(1)] = m.group(2)
    return mapping


# ---------------------------------------------------------------------------
# generator: Python → TypeScript
# ---------------------------------------------------------------------------

def _generate_ts_content(codes: Dict[str, str],
                         http_map: Dict[str, int],
                         message_map: Dict[str, str]) -> str:
    """Build the full error_codes.ts content from extracted Python data."""
    sorted_keys = sorted(codes.keys())

    lines: List[str] = []
    lines.append("// [SPEC-13A] Business error codes — TypeScript mirror of")
    lines.append("// src/shared/contracts/error_codes.py.")
    lines.append("// Authority: docs/specs/SPEC-A-contracts.md SPEC-13A "
                 '"Business Error Codes".')
    lines.append(f"// {EXPECTED_COUNT} EVID_ error codes with HTTP status "
                 "and default message mappings.")
    lines.append("")
    lines.append("export const ERROR_CODES = {")
    for key in sorted_keys:
        lines.append(f'  {key}: "{codes[key]}",')
    lines.append("} as const;")
    lines.append("")
    lines.append("export type ErrorCodeType = "
                 "(typeof ERROR_CODES)[keyof typeof ERROR_CODES];")
    lines.append("")
    lines.append("/** HTTP status code for each EVID error code. */")
    lines.append("export const ERROR_CODE_HTTP_MAP: "
                 "Record<ErrorCodeType, number> = {")
    for key in sorted_keys:
        if key in http_map:
            lines.append(f"  [ERROR_CODES.{key}]: {http_map[key]},")
    lines.append("};")
    lines.append("")
    lines.append("/** Default user-facing message for each EVID error code. */")
    lines.append("export const ERROR_CODE_MESSAGE_MAP: "
                 "Record<ErrorCodeType, string> = {")
    for key in sorted_keys:
        if key in message_map:
            escaped = message_map[key].replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'  [ERROR_CODES.{key}]: "{escaped}",')
    lines.append("};")
    lines.append("")
    lines.append("export interface ErrorCodeInfo {")
    lines.append("  code: ErrorCodeType;")
    lines.append("  http_status: number;")
    lines.append("  message: string;")
    lines.append("}")
    lines.append("")
    lines.append("/**")
    lines.append(" * Look up error code metadata.")
    lines.append(" * Throws if the code string is not a known EVID code.")
    lines.append(" */")
    lines.append("export function lookupEvid(code: string): ErrorCodeInfo {")
    lines.append("  const httpStatus = "
                 "ERROR_CODE_HTTP_MAP[code as ErrorCodeType];")
    lines.append("  const message = "
                 "ERROR_CODE_MESSAGE_MAP[code as ErrorCodeType];")
    lines.append("  if (httpStatus === undefined || message === undefined) {")
    lines.append("    throw new Error(`Unknown error code: ${code}`);")
    lines.append("  }")
    lines.append("  return { code: code as ErrorCodeType, "
                 "http_status: httpStatus, message };")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def _write_ts_file(path: str, codes: Dict[str, str],
                   http_map: Dict[str, int],
                   message_map: Dict[str, str]) -> None:
    """Write error_codes.ts from Python source data."""
    content = _generate_ts_content(codes, http_map, message_map)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# check logic
# ---------------------------------------------------------------------------

def _check_error_codes() -> Tuple[bool, List[str]]:
    py_codes = _extract_py_error_codes(CONTRACT_PY)
    ts_codes = _extract_ts_error_codes(CONTRACT_TS)
    py_http = _extract_py_http_map(CONTRACT_PY)
    ts_http = _extract_ts_http_map(CONTRACT_TS)
    py_msg = _extract_py_message_map(CONTRACT_PY)
    ts_msg = _extract_ts_message_map(CONTRACT_TS)

    results: List[str] = []
    all_ok = True

    # Check 1: code set match
    py_keys = set(py_codes.keys())
    ts_keys = set(ts_codes.keys())
    only_py = py_keys - ts_keys
    only_ts = ts_keys - py_keys
    common = py_keys & ts_keys

    if only_py:
        results.append(f"Python-only codes: {sorted(only_py)}")
        all_ok = False
    if only_ts:
        results.append(f"TypeScript-only codes: {sorted(only_ts)}")
        all_ok = False
    if len(common) != EXPECTED_COUNT:
        results.append(f"code count={len(common)}, expected={EXPECTED_COUNT}")
        all_ok = False
    else:
        results.append(f"codes: OK — {len(common)}/{EXPECTED_COUNT} consistent")

    # Check 2: value match
    value_mismatches = []
    for key in common:
        if py_codes[key] != ts_codes[key]:
            value_mismatches.append(f"{key}: py={py_codes[key]}, ts={ts_codes[key]}")
    if value_mismatches:
        results.append(f"value mismatches: {'; '.join(value_mismatches)}")
        all_ok = False
    else:
        results.append("code values: OK")

    # Check 3: HTTP map match
    http_only_py = set(py_http.keys()) - set(ts_http.keys())
    http_only_ts = set(ts_http.keys()) - set(py_http.keys())
    http_common = set(py_http.keys()) & set(ts_http.keys())
    http_mismatches = []
    for key in http_common:
        if py_http[key] != ts_http[key]:
            http_mismatches.append(f"{key}: py={py_http[key]}, ts={ts_http[key]}")

    if http_only_py or http_only_ts or http_mismatches:
        parts = []
        if http_only_py:
            parts.append(f"Python-only: {sorted(http_only_py)}")
        if http_only_ts:
            parts.append(f"TS-only: {sorted(http_only_ts)}")
        if http_mismatches:
            parts.append(f"mismatches: {'; '.join(http_mismatches)}")
        results.append(f"HTTP map: MISMATCH — {'; '.join(parts)}")
        all_ok = False
    else:
        results.append("HTTP map: OK — all 17 mapped")

    # Check 4: Message map match
    msg_only_py = set(py_msg.keys()) - set(ts_msg.keys())
    msg_only_ts = set(ts_msg.keys()) - set(py_msg.keys())
    msg_common = set(py_msg.keys()) & set(ts_msg.keys())
    msg_mismatches = []
    for key in msg_common:
        if py_msg[key] != ts_msg[key]:
            msg_mismatches.append(f"{key}: py={py_msg[key][:40]}, ts={ts_msg[key][:40]}")

    if msg_only_py or msg_only_ts or msg_mismatches:
        parts = []
        if msg_only_py:
            parts.append(f"Python-only: {sorted(msg_only_py)}")
        if msg_only_ts:
            parts.append(f"TS-only: {sorted(msg_only_ts)}")
        if msg_mismatches:
            parts.append(f"mismatches: {'; '.join(msg_mismatches)}")
        results.append(f"Message map: MISMATCH — {'; '.join(parts)}")
        all_ok = False
    else:
        results.append("Message map: OK — all 17 mapped")

    return all_ok, results


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-language error code consistency checker and generator."
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Exit 0 if consistent, 1 if gaps found"
    )
    args = parser.parse_args()

    if not args.check:
        # Generate mode: write TS from PY source, then check
        py_codes = _extract_py_error_codes(CONTRACT_PY)
        py_http = _extract_py_http_map(CONTRACT_PY)
        py_msg = _extract_py_message_map(CONTRACT_PY)
        _write_ts_file(CONTRACT_TS, py_codes, py_http, py_msg)

    all_ok, results = _check_error_codes()

    for r in results:
        prefix = "PASS" if "OK" in r else "FAIL"
        print(f"{prefix}: {r}")

    if args.check:
        return 0 if all_ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
