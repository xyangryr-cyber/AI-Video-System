"""[SPEC-B-016] Infra-level exceptions shared across gateway + worker layers.

Authority:
  docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-4
  (``OutboundBlockedException`` is the block-side exception the outbound
  gateway raises on a non-whitelisted egress attempt. SPEC-14.4 lists it
  as a P0 alert with render-team owner.)
"""

from __future__ import annotations


class OutboundBlockedException(Exception):
    """Raised when the outbound gateway refuses an agent egress attempt.

    Attributes:
        host:   Target hostname the agent tried to reach.
        agent:  Agent name as registered in ``outbound_whitelist.yaml``.
        reason: Human-readable reason recorded alongside the block event.
    """

    def __init__(self, *, host: str, agent: str, reason: str) -> None:
        self.host = host
        self.agent = agent
        self.reason = reason
        super().__init__(f"outbound blocked: agent={agent!r} host={host!r} reason={reason!r}")
