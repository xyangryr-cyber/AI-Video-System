"""[SPEC-B-016] KeyframeRenderAgent 出站网关 — integration test.

End-to-end exercise of :class:`OutboundGateway` with the real
``config/outbound_whitelist.yaml`` loaded from disk:

* Allowed hosts (cdn.internal.aivs / financial-data.internal / localhost)
  pass through without raising.
* Any other host raises :class:`OutboundBlockedException` and emits one
  P0 alert to the in-process alert sink (SPEC-14.4 hook).
* Agents without a declared policy (v3.15 behaviour) are unaffected
  (AC-6 regression guard).
"""

from __future__ import annotations

import pytest

from src.backend.infra.exceptions import OutboundBlockedException
from src.backend.infra.outbound_gateway import (
    OutboundGateway,
    clear_captured_alerts,
    get_captured_alerts,
)


def test_end_to_end_allow_block_and_alert():
    clear_captured_alerts()
    gw = OutboundGateway()

    # Allow-list entries must pass.
    gw.check(
        agent="KeyframeRenderAgent",
        url="https://cdn.internal.aivs/assets/chart_001.png",
    )
    gw.check(
        agent="KeyframeRenderAgent",
        url="https://financial-data.internal/metrics?id=AAPL",
    )
    gw.check(
        agent="KeyframeRenderAgent",
        url="http://localhost:3000/bundle.js",
    )

    # External host is blocked and alerted.
    with pytest.raises(OutboundBlockedException) as excinfo:
        gw.check(
            agent="KeyframeRenderAgent",
            url="https://cdn.external.com/bad.png",
        )
    assert excinfo.value.agent == "KeyframeRenderAgent"
    assert excinfo.value.host == "cdn.external.com"

    alerts = get_captured_alerts()
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "P0"
    assert alerts[0]["owner"] == "render-team"


def test_v315_agents_not_regressed():
    """Agents without an outbound policy must pass through unchanged."""
    gw = OutboundGateway()
    gw.check(agent="NarrationAgent", url="https://any.provider.com/tts")
    gw.check(agent="ScriptAgent", url="https://api.openai.com/v1/chat")
