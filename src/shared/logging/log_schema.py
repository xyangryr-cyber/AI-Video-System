"""[SPEC-A-012] LogLine Pydantic schema (SPEC-13B).

Single Python authority for the JSON-Lines wire format defined in
HARNESS §8 / SPEC-A-contracts.md SPEC-13B. Mirrored 1:1 in
:file:`src/shared/logging/log_schema.ts` for TypeScript callers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.shared.constants.log_events import (
    SOURCE_FALLBACK,
    SOURCE_FALLBACK_REQUIRED_EXTRAS,
)


class Service(str, Enum):
    """SPEC-13B AC-9 -- only `api` and `worker` may emit unified-format logs."""

    API = "api"
    WORKER = "worker"


class LogLevel(str, Enum):
    """SPEC-13B level table.

    Note: the WARN spelling is canonical (stdlib's WARNING is normalised
    to WARN by :class:`JsonLineFormatter` before the line is emitted).
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


LOG_LEVEL_USAGE: Dict[str, str] = {
    "DEBUG": "Dev-only diagnostics (suppressed in production by default).",
    "INFO": "Normal business events: task start/finish, phase advance, "
    "downgrade switch.",
    "WARN": "Non-fatal anomalies: degradation events "
    "(capability_gap / source_fallback), cost warnings, retries.",
    "ERROR": "Fatal exceptions: agent crash, DB error, uncaught exception.",
}
"""SPEC-13B AC-6 -- per-level usage rules. Dashboards key off these strings."""


class LogLine(BaseModel):
    """One JSON-Lines log row.

    Required: ts, level, service, event (SPEC-13B AC-1).
    Optional: project_id, phase, agent, duration_ms, error_code, extra
    (SPEC-13B AC-2). `service` constrained to api|worker (AC-9). When
    `event == source_fallback`, `extra` must carry the 3 fields in
    :data:`SOURCE_FALLBACK_REQUIRED_EXTRAS` (AC-5).
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    ts: str
    level: LogLevel
    service: Service
    event: str

    project_id: Optional[str] = None
    phase: Optional[int] = None
    agent: Optional[str] = None
    duration_ms: Optional[int] = None
    error_code: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_source_fallback_extras(self) -> "LogLine":
        if self.event == SOURCE_FALLBACK:
            missing = [
                key for key in SOURCE_FALLBACK_REQUIRED_EXTRAS if key not in self.extra
            ]
            if missing:
                raise ValueError(
                    "source_fallback log line is missing required extra "
                    f"fields: {sorted(missing)} (SPEC-13B AC-5)."
                )
        return self


def to_canonical_level(stdlib_level_name: str) -> str:
    """Normalise a stdlib level name to the SPEC-13B level set.

    `WARNING` -> `WARN`; everything else passes through uppercased.
    """
    name = stdlib_level_name.upper()
    if name == "WARNING":
        return "WARN"
    return name


def render(line: LogLine) -> Mapping[str, Any]:
    """Return the dict representation suitable for `json.dumps`."""
    return line.model_dump(exclude_none=True, mode="json")


__all__ = [
    "LOG_LEVEL_USAGE",
    "LogLevel",
    "LogLine",
    "Service",
    "render",
    "to_canonical_level",
]
