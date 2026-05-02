"""[SPEC-A-012] Special log event names (SPEC-13B).

The SPEC-13B "special log events" are the 5 cross-cutting events every
operator dashboard MUST be able to key off (router degradations, capability
mismatches, source fallbacks, cost alarms, leak hits). Their names are
fixed strings -- callers MUST import these constants rather than write
free-form event names.

Distinct from :mod:`src.shared.constants.log_event_codes` (SPEC-A-018),
which constrains the *render-failure* `event` field to the 3 SPEC-13A
aliases. The two registries are intentionally non-overlapping.
"""

from __future__ import annotations

# 5 mandatory event names per SPEC-A-contracts.md SPEC-13B.
ROUTER_FALLBACK: str = "router_fallback"
"""Router degradation -- a route resolved to `clarify` after exhausting candidates."""

CAPABILITY_GAP: str = "capability_gap"
"""Provider capability mismatch -- e.g. TTS provider does not support a parameter."""

SOURCE_FALLBACK: str = "source_fallback"
"""Material/data source degradation. extra MUST contain
`source_attempted`, `reason_failed`, `source_used` -- enforced by
:class:`src.shared.logging.log_schema.LogLine`.
"""

COST_WARNING: str = "cost_warning"
"""Project cost crossed the SPEC-13B threshold ($15)."""

LEAK_SCAN_HIT: str = "leak_scan_hit"
"""Sanitiser scan found a SECRET_REGEXES match in candidate output."""

SPECIAL_EVENT_NAMES: frozenset[str] = frozenset(
    {
        ROUTER_FALLBACK,
        CAPABILITY_GAP,
        SOURCE_FALLBACK,
        COST_WARNING,
        LEAK_SCAN_HIT,
    }
)
"""Frozen registry of the 5 SPEC-13B special event names."""

# extra-field contract for source_fallback (SPEC-13B verification #3).
SOURCE_FALLBACK_REQUIRED_EXTRAS: frozenset[str] = frozenset(
    {"source_attempted", "reason_failed", "source_used"}
)


__all__ = [
    "ROUTER_FALLBACK",
    "CAPABILITY_GAP",
    "SOURCE_FALLBACK",
    "COST_WARNING",
    "LEAK_SCAN_HIT",
    "SPECIAL_EVENT_NAMES",
    "SOURCE_FALLBACK_REQUIRED_EXTRAS",
]
