"""Tests for [SPEC-A-012] Unified Structured Logging Format (SPEC-13B).

Authority: docs/specs/SPEC-A-contracts.md SPEC-13B + HARNESS §8.

Drives the contract surface in:
  - src/shared/logging/log_schema.py     (Pydantic `LogLine`)
  - src/shared/logging/formatter.py      (stdlib JSON-Lines formatter)
  - src/shared/logging/sanitizer.py      (SECRET_REGEXES + `sanitize`)
  - src/shared/constants/log_events.py   (5 special event names)

Test Mapping (mirrors task card AC-1..AC-9; the card's own Test Mapping
points at `test_spec_a_012.py`, but `allowed_files` only lists this file --
the inconsistency is documented in the SPEC-A-012 commit Decisions).
"""

from __future__ import annotations

import io
import json
import logging

import pytest


# --------------------------------------------------------------------------- #
# AC-1: required fields ts, level, service, event                             #
# --------------------------------------------------------------------------- #
class TestAC1RequiredFieldsPresent:
    """AC-1: Log line schema defines required fields: ts, level, service, event"""

    def test_required_fields_present(self):
        from pydantic import ValidationError

        from src.shared.logging.log_schema import LogLine

        # Happy path -- minimum 4 required fields
        line = LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="INFO",
            service="api",
            event="task.started",
        )
        for field in ("ts", "level", "service", "event"):
            assert hasattr(line, field), f"LogLine missing required field {field!r}"

        # Each required field individually missing must raise
        for missing in ("ts", "level", "service", "event"):
            payload = {
                "ts": "2026-04-24T10:30:00.000Z",
                "level": "INFO",
                "service": "api",
                "event": "task.started",
            }
            payload.pop(missing)
            with pytest.raises(ValidationError):
                LogLine(**payload)


# --------------------------------------------------------------------------- #
# AC-2: optional fields                                                       #
# --------------------------------------------------------------------------- #
class TestAC2OptionalFieldsAccepted:
    """AC-2: Optional fields: project_id, phase, agent, duration_ms, error_code, extra"""

    def test_optional_fields_accepted(self):
        from src.shared.logging.log_schema import LogLine

        # All optional fields default to None / empty
        bare = LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="INFO",
            service="api",
            event="task.started",
        )
        for field in ("project_id", "phase", "agent", "duration_ms", "error_code"):
            assert getattr(bare, field) is None, (
                f"Optional field {field!r} should default to None, got {getattr(bare, field)!r}"
            )
        assert bare.extra == {}, "extra should default to empty dict"

        # All optional fields accepted with realistic values
        full = LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="INFO",
            service="worker",
            event="task.completed",
            project_id="proj_abc123",
            phase=3,
            agent="ScriptAgent",
            duration_ms=1234,
            error_code="EVID_2001",
            extra={"tokens_in": 500, "tokens_out": 200},
        )
        assert full.project_id == "proj_abc123"
        assert full.phase == 3
        assert full.agent == "ScriptAgent"
        assert full.duration_ms == 1234
        assert full.error_code == "EVID_2001"
        assert full.extra == {"tokens_in": 500, "tokens_out": 200}


# --------------------------------------------------------------------------- #
# AC-3: JSON Lines parseable                                                  #
# --------------------------------------------------------------------------- #
class TestAC3JsonLinesParseable:
    """AC-3: Python JSON formatter outputs valid JSON Lines (each line parseable by json.loads)"""

    def test_json_lines_parseable(self):
        from src.shared.logging.formatter import JsonLineFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonLineFormatter(service="api"))

        logger = logging.getLogger("test_spec_a_012.ac3")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        logger.propagate = False

        logger.info(
            "task started",
            extra={
                "event": "task.started",
                "project_id": "proj_xyz",
                "phase": 2,
                "agent": "ScriptAgent",
                "duration_ms": 17,
            },
        )
        logger.warning("router fallback", extra={"event": "router_fallback"})

        raw = stream.getvalue()
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        assert len(lines) == 2, f"expected 2 lines, got {len(lines)}: {raw!r}"

        parsed = [json.loads(ln) for ln in lines]  # raises if not valid JSON
        for record in parsed:
            for required in ("ts", "level", "service", "event"):
                assert required in record, f"missing {required!r} in {record!r}"
            assert record["service"] == "api"

        assert parsed[0]["event"] == "task.started"
        assert parsed[0]["project_id"] == "proj_xyz"
        assert parsed[0]["phase"] == 2
        assert parsed[0]["level"] == "INFO"
        assert parsed[1]["event"] == "router_fallback"
        # WARNING normalised to WARN per SPEC-13B level table
        assert parsed[1]["level"] == "WARN"


# --------------------------------------------------------------------------- #
# AC-4: 5 special event names                                                 #
# --------------------------------------------------------------------------- #
class TestAC4SpecialEventConstants:
    """AC-4: 5 special event names defined as constants."""

    def test_special_event_constants(self):
        from src.shared.constants import log_events

        expected = {
            "router_fallback",
            "capability_gap",
            "source_fallback",
            "cost_warning",
            "leak_scan_hit",
        }
        assert log_events.ROUTER_FALLBACK == "router_fallback"
        assert log_events.CAPABILITY_GAP == "capability_gap"
        assert log_events.SOURCE_FALLBACK == "source_fallback"
        assert log_events.COST_WARNING == "cost_warning"
        assert log_events.LEAK_SCAN_HIT == "leak_scan_hit"
        # Frozen registry covering exactly these 5
        assert log_events.SPECIAL_EVENT_NAMES == frozenset(expected)


# --------------------------------------------------------------------------- #
# AC-5: source_fallback requires extra fields                                 #
# --------------------------------------------------------------------------- #
class TestAC5SourceFallbackExtraFields:
    """AC-5: source_fallback events require extra fields:
    source_attempted, reason_failed, source_used."""

    def test_source_fallback_extra_fields(self):
        from pydantic import ValidationError

        from src.shared.logging.log_schema import LogLine

        # All three present -> OK
        ok = LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="WARN",
            service="worker",
            event="source_fallback",
            extra={
                "source_attempted": "yahoo_finance",
                "reason_failed": "rate_limit_429",
                "source_used": "alpha_vantage",
            },
        )
        assert ok.extra["source_used"] == "alpha_vantage"

        # Each one individually missing -> ValidationError
        for missing in ("source_attempted", "reason_failed", "source_used"):
            extra = {
                "source_attempted": "yahoo_finance",
                "reason_failed": "rate_limit_429",
                "source_used": "alpha_vantage",
            }
            extra.pop(missing)
            with pytest.raises(ValidationError) as excinfo:
                LogLine(
                    ts="2026-04-24T10:30:00.000Z",
                    level="WARN",
                    service="worker",
                    event="source_fallback",
                    extra=extra,
                )
            assert missing in str(excinfo.value)

        # Other events do NOT require these extras
        LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="INFO",
            service="api",
            event="task.started",
            extra={},
        )


# --------------------------------------------------------------------------- #
# AC-6: log level usage rules documented                                      #
# --------------------------------------------------------------------------- #
class TestAC6LogLevelDocumentation:
    """AC-6: Log level rules documented:
    DEBUG=dev-only, INFO=business-events, WARN=non-fatal, ERROR=fatal"""

    def test_log_level_documentation(self):
        from src.shared.logging.log_schema import LOG_LEVEL_USAGE, LogLevel

        # Exactly 4 levels in the canonical set
        assert {level.value for level in LogLevel} == {"DEBUG", "INFO", "WARN", "ERROR"}

        # Each level has a human-readable usage rule
        assert set(LOG_LEVEL_USAGE.keys()) == {"DEBUG", "INFO", "WARN", "ERROR"}
        assert "dev" in LOG_LEVEL_USAGE["DEBUG"].lower()
        assert (
            "business" in LOG_LEVEL_USAGE["INFO"].lower()
            or "event" in LOG_LEVEL_USAGE["INFO"].lower()
        )
        assert (
            "non-fatal" in LOG_LEVEL_USAGE["WARN"].lower()
            or "degrad" in LOG_LEVEL_USAGE["WARN"].lower()
        )
        assert (
            "fatal" in LOG_LEVEL_USAGE["ERROR"].lower()
            or "crash" in LOG_LEVEL_USAGE["ERROR"].lower()
        )


# --------------------------------------------------------------------------- #
# AC-7: production config suppresses DEBUG                                    #
# --------------------------------------------------------------------------- #
class TestAC7ProductionNoDebug:
    """AC-7: Production config suppresses DEBUG level output."""

    def test_production_no_debug(self):
        from src.shared.logging.formatter import (
            JsonLineFormatter,
            production_log_level,
        )

        # Production -> INFO (no DEBUG)
        assert production_log_level("production") == logging.INFO
        assert production_log_level("prod") == logging.INFO
        # Dev/staging may emit DEBUG
        assert production_log_level("development") == logging.DEBUG
        assert production_log_level("dev") == logging.DEBUG

        # End-to-end: a logger configured at production level drops DEBUG records
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonLineFormatter(service="api"))
        handler.setLevel(production_log_level("production"))

        logger = logging.getLogger("test_spec_a_012.ac7")
        logger.handlers = [handler]
        logger.setLevel(production_log_level("production"))
        logger.propagate = False

        logger.debug("hidden", extra={"event": "debug.noise"})
        logger.info("kept", extra={"event": "task.started"})

        out = [ln for ln in stream.getvalue().splitlines() if ln.strip()]
        assert len(out) == 1, f"DEBUG should be suppressed in production: {out!r}"
        assert json.loads(out[0])["event"] == "task.started"


# --------------------------------------------------------------------------- #
# AC-8: sanitizer strips secrets                                              #
# --------------------------------------------------------------------------- #
class TestAC8SanitizerStripsSecrets:
    """AC-8: Sanitizer strips patterns matching SECRET_REGEXES before log output."""

    def test_sanitizer_strips_secrets(self):
        from src.shared.logging.sanitizer import SECRET_REGEXES, sanitize

        # SPEC-13.3 mandates 7 SECRET_REGEXES rules
        assert len(SECRET_REGEXES) >= 7, (
            f"expected >=7 SECRET_REGEXES per SPEC-13.3, got {len(SECRET_REGEXES)}"
        )

        # Each canonical secret format is stripped to [REDACTED]
        cases = [
            "leaked sk-AbCdEfGhIjKlMnOpQrStUvWxYz1234567890123456",  # OpenAI sk-
            "anthropic key sk-ant-api03-AbCdEfGhIjKlMnOpQrStUv-Wx12345678",
            "Authorization: Bearer abc.def.ghi-jkl_mno1234567890",
            "AWS=AKIAIOSFODNN7EXAMPLE",
            "email=alice.bob@example.com",
            "phone=+1-415-555-0199",
            "card=4111-1111-1111-1111",
        ]
        for raw in cases:
            cleaned = sanitize(raw)
            assert "[REDACTED]" in cleaned, (
                f"sanitize() did not redact: {raw!r} -> {cleaned!r}"
            )

        # Sanitiser is structure-preserving for dicts -- recurses into values
        d = sanitize({"prompt": "key=sk-AbCdEfGhIjKlMnOpQrStUvWxYz1234567890123456"})
        assert "[REDACTED]" in d["prompt"]
        assert "sk-AbCdEf" not in d["prompt"]

        # Plain harmless text is left untouched
        assert sanitize("hello world phase=3") == "hello world phase=3"


# --------------------------------------------------------------------------- #
# AC-9: service field is constrained to api|worker                            #
# --------------------------------------------------------------------------- #
class TestAC9ServiceFieldEnum:
    """AC-9: service field constrained to 'api' | 'worker'."""

    def test_service_field_enum(self):
        from pydantic import ValidationError

        from src.shared.logging.log_schema import LogLine, Service

        # Both allowed values pass
        for svc in ("api", "worker"):
            line = LogLine(
                ts="2026-04-24T10:30:00.000Z",
                level="INFO",
                service=svc,
                event="task.started",
            )
            assert line.service == svc

        # Service is a 2-value enum
        assert {s.value for s in Service} == {"api", "worker"}

        # Anything else rejected
        for bad in ("frontend", "API", "worker_2", ""):
            with pytest.raises(ValidationError):
                LogLine(
                    ts="2026-04-24T10:30:00.000Z",
                    level="INFO",
                    service=bad,
                    event="task.started",
                )
