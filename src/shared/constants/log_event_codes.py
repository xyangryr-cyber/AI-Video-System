"""[SPEC-A-018] Constrained `event` field for SPEC-13B unified-log format.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6
(PRD-DELTA-08 / TECH-DELTA-07).

HARNESS §8.1 defines the unified JSON log format. SPEC-13B v3.17 further
constrains the `event` field of P8 render-failure / shot-block log rows to
exactly the 3 v3.17 SPEC-13A error aliases -- so log-aggregation dashboards
can key off a fixed enum rather than a free-form string.

Callers hand a candidate event name to :func:`validate_log_event_code`; on
success the call returns the code unchanged, on failure it raises
:class:`InvalidLogEventError` so the caller can distinguish "log-event
constraint" from ordinary ``KeyError`` / ``ValueError`` control flow.
"""

from __future__ import annotations

from typing import FrozenSet


ALLOWED_LOG_EVENT_CODES: FrozenSet[str] = frozenset(
    {
        "render_failed",
        "material_missing",
        "material_unverified",
    }
)
"""The 3 SPEC-13A v3.17 aliases permitted in P8 failure/block log `event` fields.

These aliases also exist in
``src.shared.constants.error_codes.ERROR_CODE_ALIASES`` and resolve (via
:func:`src.shared.constants.error_codes.resolve_error_code`) to the
corresponding EVID_* canonical code.
"""


class InvalidLogEventError(Exception):
    """Raised when a log row's `event` field is not one of ALLOWED_LOG_EVENT_CODES.

    Deliberately NOT a subclass of :class:`KeyError` -- callers should be
    able to distinguish "log-event constraint violation" from generic lookup
    failure (``catch KeyError`` must not accidentally swallow this error).
    """


def validate_log_event_code(name: str) -> str:
    """Return ``name`` if it is an allowed log event code, else raise.

    Raises:
        InvalidLogEventError: when ``name`` is not in ALLOWED_LOG_EVENT_CODES.
    """
    if name not in ALLOWED_LOG_EVENT_CODES:
        raise InvalidLogEventError(
            f"Log event {name!r} is not in ALLOWED_LOG_EVENT_CODES. "
            f"Expected one of {sorted(ALLOWED_LOG_EVENT_CODES)} "
            "(SPEC-13B v3.17 / SPEC-A-018)."
        )
    return name


__all__ = [
    "ALLOWED_LOG_EVENT_CODES",
    "InvalidLogEventError",
    "validate_log_event_code",
]
