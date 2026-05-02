"""[SPEC-A-012] Secret sanitiser (SPEC-13.3 SECRET_REGEXES, SPEC-13B AC-8).

Strips known secret patterns from log payloads before emission. Reuses the
SPEC-13.3 7-rule regex set described in SPEC-B-infra-deploy.md §SPEC-13.3:

  1. OpenAI API keys           (sk-... / sk-proj-...)
  2. Anthropic API keys        (sk-ant-...)
  3. Bearer / Authorization tokens
  4. AWS access key IDs        (AKIA...)
  5. Email addresses
  6. Phone numbers (E.164-ish)
  7. Credit-card-shaped digit groups

Callers MUST sanitise candidate output BEFORE passing it to the unified
JSON-Lines formatter -- HARNESS §11 forbids raw prompt/response text in
logs.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, List, Mapping, Pattern

REDACTED: str = "[REDACTED]"

# Order matters: longer / more-specific patterns first so they swallow
# substrings that a shorter regex would otherwise match.
_SECRET_PATTERNS: List[str] = [
    # 1. Anthropic API keys (must run before generic sk-...)
    r"sk-ant-[A-Za-z0-9_\-]{20,}",
    # 2. OpenAI API keys (sk-, sk-proj-)
    r"sk-(?:proj-)?[A-Za-z0-9]{20,}",
    # 3. Bearer / Authorization tokens
    r"(?i:Bearer)\s+[A-Za-z0-9._\-]+",
    # 4. AWS access key IDs
    r"AKIA[0-9A-Z]{16}",
    # 5. Credit-card-shaped digit groups (4x4) -- run before phone so
    # 16-digit hyphen groups are not partially eaten.
    r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    # 6. Phone numbers (E.164 / hyphenated local)
    r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    # 7. Email addresses
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
]

SECRET_REGEXES: List[Pattern[str]] = [re.compile(p) for p in _SECRET_PATTERNS]


def _sanitize_str(value: str) -> str:
    cleaned = value
    for regex in SECRET_REGEXES:
        cleaned = regex.sub(REDACTED, cleaned)
    return cleaned


def sanitize(value: Any) -> Any:
    """Recursively redact SECRET_REGEXES matches in `value`.

    - `str`            -> redacted copy
    - `Mapping`        -> new dict with each value sanitised
    - `list` / `tuple` -> list of sanitised items
    - any other type   -> returned unchanged

    Pure / no I/O / no logging side-effects.
    """
    if isinstance(value, str):
        return _sanitize_str(value)
    if isinstance(value, Mapping):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        sanitised: Iterable[Any] = (sanitize(item) for item in value)
        return list(sanitised)
    return value


__all__ = ["REDACTED", "SECRET_REGEXES", "sanitize"]
