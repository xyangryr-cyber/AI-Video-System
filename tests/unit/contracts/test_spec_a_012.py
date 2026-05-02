"""Tests for [SPEC-A-012] Unified Structured Logging Format (SPEC-13B)."""

from __future__ import annotations

import io
import json
import logging

import pytest
from pydantic import ValidationError


class TestAC1RequiredFieldsPresent:
    """AC-1: Log line schema defines required fields: ts, level, service, event"""

    def test_required_fields_present(self):
        from src.shared.logging.log_schema import LogLine

        line = LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="INFO",
            service="api",
            event="task.started",
        )
        for field in ("ts", "level", "service", "event"):
            assert hasattr(line, field)

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


class TestAC2OptionalFieldsAccepted:
    """AC-2: Log line schema defines optional fields: project_id, phase, agent, duration_ms, error_code, extra"""

    def test_optional_fields_accepted(self):
        from src.shared.logging.log_schema import LogLine

        bare = LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="INFO",
            service="api",
            event="task.started",
        )
        for field in ("project_id", "phase", "agent", "duration_ms", "error_code"):
            assert getattr(bare, field) is None

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
        assert full.duration_ms == 1234
        assert full.extra == {"tokens_in": 500, "tokens_out": 200}


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
            },
        )
        logger.warning("router fallback", extra={"event": "router_fallback"})

        raw = stream.getvalue()
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        assert len(lines) == 2

        parsed = [json.loads(ln) for ln in lines]
        for record in parsed:
            for required in ("ts", "level", "service", "event"):
                assert required in record
            assert record["service"] == "api"
        assert parsed[0]["event"] == "task.started"
        assert parsed[1]["event"] == "router_fallback"


class TestAC4SpecialEventConstants:
    """AC-4: 5 special event names defined as constants: router_fallback, capability_gap, source_fallback, cost_warning, leak_scan_hit"""

    def test_special_event_constants(self):
        from src.shared.constants import log_events

        assert log_events.ROUTER_FALLBACK == "router_fallback"
        assert log_events.CAPABILITY_GAP == "capability_gap"
        assert log_events.SOURCE_FALLBACK == "source_fallback"
        assert log_events.COST_WARNING == "cost_warning"
        assert log_events.LEAK_SCAN_HIT == "leak_scan_hit"
        assert log_events.SPECIAL_EVENT_NAMES == frozenset(
            {
                "router_fallback",
                "capability_gap",
                "source_fallback",
                "cost_warning",
                "leak_scan_hit",
            }
        )


class TestAC5SourceFallbackExtraFields:
    """AC-5: source_fallback events require extra fields: source_attempted, reason_failed, source_used"""

    def test_source_fallback_extra_fields(self):
        from src.shared.logging.log_schema import LogLine

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

        for missing in ("source_attempted", "reason_failed", "source_used"):
            extra = {
                "source_attempted": "yahoo_finance",
                "reason_failed": "rate_limit_429",
                "source_used": "alpha_vantage",
            }
            extra.pop(missing)
            with pytest.raises(ValidationError):
                LogLine(
                    ts="2026-04-24T10:30:00.000Z",
                    level="WARN",
                    service="worker",
                    event="source_fallback",
                    extra=extra,
                )

        # Other events do not require these extras
        LogLine(
            ts="2026-04-24T10:30:00.000Z",
            level="INFO",
            service="api",
            event="task.started",
            extra={},
        )


class TestAC6LogLevelDocumentation:
    """AC-6: Log level rules documented: DEBUG=dev-only, INFO=business-events, WARN=non-fatal, ERROR=fatal"""

    def test_log_level_documentation(self):
        from src.shared.logging.log_schema import LOG_LEVEL_USAGE, LogLevel

        assert {level.value for level in LogLevel} == {"DEBUG", "INFO", "WARN", "ERROR"}
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


class TestAC7ProductionNoDebug:
    """AC-7: Production config suppresses DEBUG level output"""

    def test_production_no_debug(self):
        from src.shared.logging.formatter import JsonLineFormatter, production_log_level

        assert production_log_level("production") == logging.INFO
        assert production_log_level("prod") == logging.INFO
        assert production_log_level("development") == logging.DEBUG

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
        assert len(out) == 1
        assert json.loads(out[0])["event"] == "task.started"


class TestAC8SanitizerStripsSecrets:
    """AC-8: Sanitizer strips patterns matching SECRET_REGEXES before log output"""

    def test_sanitizer_strips_secrets(self):
        from src.shared.logging.sanitizer import SECRET_REGEXES, sanitize

        assert len(SECRET_REGEXES) >= 7

        cases = [
            "leaked sk-AbCdEfGhIjKlMnOpQrStUvWxYz1234567890123456",
            "anthropic key sk-ant-api03-AbCdEfGhIjKlMnOpQrStUv-Wx12345678",
            "Authorization: Bearer abc.def.ghi-jkl_mno1234567890",
            "AWS=AKIAIOSFODNN7EXAMPLE",
            "email=alice.bob@example.com",
            "phone=+1-415-555-0199",
            "card=4111-1111-1111-1111",
        ]
        for raw in cases:
            cleaned = sanitize(raw)
            assert "[REDACTED]" in cleaned

        # Structure-preserving for dicts
        d = sanitize({"prompt": "key=sk-AbCdEfGhIjKlMnOpQrStUvWxYz1234567890123456"})
        assert "[REDACTED]" in d["prompt"]

        # Harmless text untouched
        assert sanitize("hello world phase=3") == "hello world phase=3"


class TestAC9ServiceFieldEnum:
    """AC-9: service field constrained to 'api' | 'worker'"""

    def test_service_field_enum(self):
        from src.shared.logging.log_schema import LogLine, Service

        for svc in ("api", "worker"):
            line = LogLine(
                ts="2026-04-24T10:30:00.000Z",
                level="INFO",
                service=svc,
                event="task.started",
            )
            assert line.service == svc

        assert {s.value for s in Service} == {"api", "worker"}

        for bad in ("frontend", "API", "worker_2", ""):
            with pytest.raises(ValidationError):
                LogLine(
                    ts="2026-04-24T10:30:00.000Z",
                    level="INFO",
                    service=bad,
                    event="task.started",
                )
