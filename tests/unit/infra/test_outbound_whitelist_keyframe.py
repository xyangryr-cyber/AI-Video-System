"""[SPEC-B-016] KeyframeRenderAgent 出站网关白名单 — unit assertions.

Allowed-files-compliant module holding the real AC-1..AC-6 assertions for
SPEC-B-016. ``tests/unit/infra/test_spec_b_016.py`` delegates to these
classes via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_016.py`` still exercises them
(A-100..A-105, B-015 precedent).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config" / "outbound_whitelist.yaml"


class TestAC1:
    """AC-1: outbound_whitelist.yaml has KeyframeRenderAgent + hosts + blocked apis."""

    def test_config_has_keyframe_section(self):
        yaml = pytest.importorskip("yaml")
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        entries = data.get("outbound_whitelist") or []
        agents = {e.get("agent") for e in entries if isinstance(e, dict)}
        assert "KeyframeRenderAgent" in agents, (
            f"outbound_whitelist missing KeyframeRenderAgent section; got {agents!r}"
        )

    def test_allowed_hosts_present(self):
        yaml = pytest.importorskip("yaml")
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        entry = next(
            e
            for e in data["outbound_whitelist"]
            if isinstance(e, dict) and e.get("agent") == "KeyframeRenderAgent"
        )
        hosts = set(entry.get("allowed_hosts") or [])
        assert {"cdn.internal.aivs", "financial-data.internal", "localhost"} <= hosts, (
            f"allowed_hosts must include internal CDN / DataService / localhost; got {hosts!r}"
        )

    def test_blocked_apis_present(self):
        yaml = pytest.importorskip("yaml")
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        entry = next(
            e
            for e in data["outbound_whitelist"]
            if isinstance(e, dict) and e.get("agent") == "KeyframeRenderAgent"
        )
        blocked = set(entry.get("blocked_apis") or [])
        required = {"b_roll_search", "news_search", "any LLM-generated URL fetch"}
        assert required <= blocked, (
            f"blocked_apis missing required entries; got {blocked!r}"
        )


class TestAC2:
    """AC-2: OutboundBlockedException exposes host / agent / reason."""

    def test_outbound_blocked_exception_class(self):
        from src.backend.infra.exceptions import OutboundBlockedException

        exc = OutboundBlockedException(
            host="cdn.external.com",
            agent="KeyframeRenderAgent",
            reason="host not in allowed_hosts",
        )
        assert isinstance(exc, Exception)
        assert exc.host == "cdn.external.com"
        assert exc.agent == "KeyframeRenderAgent"
        assert exc.reason == "host not in allowed_hosts"
        msg = str(exc)
        assert "KeyframeRenderAgent" in msg and "cdn.external.com" in msg


class TestAC3:
    """AC-3: Internal CDN passes; external host raises OutboundBlockedException."""

    def test_internal_cdn_passes(self):
        from src.backend.infra.outbound_gateway import OutboundGateway

        gw = OutboundGateway()
        gw.check(
            agent="KeyframeRenderAgent",
            url="https://cdn.internal.aivs/assets/chart_001.png",
        )

    def test_external_host_blocked(self):
        from src.backend.infra.exceptions import OutboundBlockedException
        from src.backend.infra.outbound_gateway import OutboundGateway

        gw = OutboundGateway()
        with pytest.raises(OutboundBlockedException) as excinfo:
            gw.check(
                agent="KeyframeRenderAgent",
                url="https://cdn.external.com/bad.png",
            )
        assert excinfo.value.agent == "KeyframeRenderAgent"
        assert excinfo.value.host == "cdn.external.com"
        assert excinfo.value.reason


class TestAC4:
    """AC-4: structured ERROR log with event/agent/host/reason fields on block."""

    def test_log_event_on_block(self, caplog):
        from src.backend.infra.exceptions import OutboundBlockedException
        from src.backend.infra.outbound_gateway import OutboundGateway

        gw = OutboundGateway()
        with caplog.at_level(
            logging.ERROR, logger="src.backend.infra.outbound_gateway"
        ):
            with pytest.raises(OutboundBlockedException):
                gw.check(
                    agent="KeyframeRenderAgent",
                    url="https://evil.external.com/path",
                )
        matches = [r for r in caplog.records if r.getMessage() == "outbound.blocked"]
        assert matches, "expected one ERROR log with msg=outbound.blocked"
        rec = matches[0]
        assert rec.levelname == "ERROR"
        assert rec.__dict__.get("event") == "outbound.blocked"
        assert rec.__dict__.get("agent") == "KeyframeRenderAgent"
        assert rec.__dict__.get("host") == "evil.external.com"
        assert rec.__dict__.get("reason")


class TestAC5:
    """AC-5: alert event captured with P0 severity + render-team owner."""

    def test_alert_event_captured_p0(self):
        from src.backend.infra.exceptions import OutboundBlockedException
        from src.backend.infra.outbound_gateway import (
            OutboundGateway,
            clear_captured_alerts,
            get_captured_alerts,
        )

        clear_captured_alerts()
        gw = OutboundGateway()
        with pytest.raises(OutboundBlockedException):
            gw.check(
                agent="KeyframeRenderAgent",
                url="https://bad.external.com/x",
            )
        alerts = get_captured_alerts()
        assert len(alerts) == 1, f"expected exactly one alert event, got {alerts!r}"
        alert = alerts[0]
        assert alert["severity"] == "P0"
        assert alert["owner"] == "render-team"
        assert alert["agent"] == "KeyframeRenderAgent"
        assert alert["event"] == "outbound.blocked"


class TestAC6:
    """AC-6: agents without a policy (v3.15 agents) are unaffected."""

    def test_other_agents_outbound_unchanged(self):
        from src.backend.infra.outbound_gateway import OutboundGateway

        gw = OutboundGateway()
        # NarrationAgent has no outbound policy: gateway must pass through.
        gw.check(
            agent="NarrationAgent",
            url="https://any.external.provider.com/api/tts",
        )
        gw.check(
            agent="ScriptAgent",
            url="https://api.openai.com/v1/chat",
        )
