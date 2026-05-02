"""[SPEC-A-012] JSON-Lines logging formatter (SPEC-13B).

Stdlib :class:`logging.Formatter` subclass that turns a `LogRecord` into a
SPEC-13B JSON-Lines row. Callers attach the formatter once per service:

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLineFormatter(service="api"))
    handler.setLevel(production_log_level(os.getenv("ENV", "production")))

Per-record fields (`event`, `project_id`, `phase`, `agent`,
`duration_ms`, `error_code`, `extra`) are passed via the standard
`logger.info(msg, extra={...})` mechanism. Field names are validated by
:class:`src.shared.logging.log_schema.LogLine`, so a malformed call fails
fast at emission time rather than producing a silent free-form row.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from src.shared.logging.log_schema import (
    LogLine,
    Service,
    render,
    to_canonical_level,
)

# Stdlib LogRecord attributes we never want to copy into `extra`.
_RESERVED: frozenset[str] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
        # SPEC-13B top-level slots -- consumed explicitly.
        "ts",
        "level",
        "service",
        "event",
        "project_id",
        "phase",
        "agent",
        "duration_ms",
        "error_code",
        "extra",
    }
)


def _isoformat(record_created: float) -> str:
    """RFC3339-ish UTC string with millisecond precision and trailing `Z`."""
    dt = datetime.fromtimestamp(record_created, tz=UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def production_log_level(env_name: str) -> int:
    """Return the stdlib log level for `env_name`.

    Production environments (`production` / `prod`) -> `logging.INFO`
    so DEBUG records are suppressed (SPEC-13B AC-7). Anything else
    (`dev`, `development`, `test`, ...) -> `logging.DEBUG`.
    """
    normalised = (env_name or "").strip().lower()
    if normalised in {"production", "prod"}:
        return logging.INFO
    return logging.DEBUG


class JsonLineFormatter(logging.Formatter):
    """Serialise stdlib `LogRecord` objects to SPEC-13B JSON-Lines rows."""

    def __init__(self, service: str) -> None:
        super().__init__()
        # Validate eagerly so a typo in `service=` fails at boot, not at
        # the first log line.
        self._service: str = Service(service).value

    def format(self, record: logging.LogRecord) -> str:
        ts = _isoformat(record.created)
        level = to_canonical_level(record.levelname)
        event = getattr(record, "event", None) or record.name

        payload: dict[str, Any] = {
            "ts": ts,
            "level": level,
            "service": self._service,
            "event": event,
        }

        for slot in (
            "project_id",
            "phase",
            "agent",
            "duration_ms",
            "error_code",
        ):
            value = getattr(record, slot, None)
            if value is not None:
                payload[slot] = value

        # `extra={...}` keys are flattened onto the LogRecord by the stdlib.
        # Anything not consumed above is rolled into the `extra` slot so
        # the row stays schema-compliant.
        explicit_extra: dict[str, Any] | None = getattr(record, "extra", None)
        rolled: dict[str, Any] = dict(explicit_extra) if explicit_extra else {}
        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            rolled[key] = value
        if rolled:
            payload["extra"] = rolled

        try:
            line = LogLine.model_validate(payload)
        except ValidationError as exc:  # pragma: no cover -- caller bug
            raise ValueError(
                f"JsonLineFormatter rejected a LogRecord that violates SPEC-13B: {exc}"
            ) from exc

        return json.dumps(render(line), ensure_ascii=False, sort_keys=False)


__all__ = ["JsonLineFormatter", "production_log_level"]
