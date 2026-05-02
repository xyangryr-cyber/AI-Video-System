"""[SPEC-B-016] Outbound gateway whitelist enforcement (SPEC-12).

Authority:
  docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-4.

Responsibilities:

* Load per-agent policies from ``config/outbound_whitelist.yaml``.
* On ``OutboundGateway.check(agent=..., url=...)``:
    - If the agent has no declared policy → pass through (v3.15 behaviour
      must not regress; AC-6).
    - If the target host is in ``allowed_hosts`` → pass through.
    - Otherwise emit a structured ERROR log with
      ``event=outbound.blocked`` and required fields (AC-4), append a P0
      alert record to the in-process sink (AC-5), and raise
      :class:`OutboundBlockedException` (AC-3).

The in-process alert sink is a stand-in until SPEC-B-010 observability
plumbing is finalised; AC-5 only requires that a block is observable to
downstream assertions in the same process.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple
from urllib.parse import urlparse

from src.backend.infra.exceptions import OutboundBlockedException


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "outbound_whitelist.yaml"

logger = logging.getLogger("src.backend.infra.outbound_gateway")

# SPEC-14.4 alert sink. A plain in-memory list is enough for AC-5 and the
# integration test; real wiring to the alert pipeline happens in SPEC-B-010.
_ALERT_SINK: List[Dict[str, Any]] = []


@dataclass(frozen=True)
class AgentPolicy:
    agent: str
    allowed_hosts: Tuple[str, ...]
    blocked_apis: Tuple[str, ...]
    log_level: str = "ERROR"
    exception_name: str = "OutboundBlockedException"
    alert_severity: str = "P0"
    alert_owner: str = "render-team"


def _normalize_host(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "http://" + value
    parsed = urlparse(value)
    return (parsed.hostname or "").lower()


def _load_yaml_data(config_path: Path) -> Dict[str, Any]:
    """Load the outbound_whitelist yaml; fall back to a minimal parser when
    pyyaml is unavailable (matches B-001 regex-parse precedent — the schema
    is narrow and author-controlled)."""
    text = Path(config_path).read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return _parse_outbound_yaml_fallback(text)
    return yaml.safe_load(text) or {}


def _parse_outbound_yaml_fallback(text: str) -> Dict[str, Any]:
    """Minimal parser for config/outbound_whitelist.yaml.

    Supports exactly the shape emitted by SPEC-B-016:
      * top-level ``outbound_whitelist:`` -> list of agent mappings
      * each entry has scalar ``agent``, list ``allowed_hosts``,
        list ``blocked_apis``, and nested scalar-only mappings
        ``on_block`` / ``alert``.
    Comments (``#``) and blank lines are ignored.
    """
    entries: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    list_key: Optional[str] = None
    map_key: Optional[str] = None
    in_outbound = False

    def _strip(value: str) -> str:
        return value.strip().strip('"').strip("'")

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0:
            in_outbound = stripped == "outbound_whitelist:"
            current = None
            list_key = None
            map_key = None
            continue
        if not in_outbound:
            continue

        if indent == 2 and stripped.startswith("- "):
            current = {"agent": None, "allowed_hosts": [], "blocked_apis": []}
            entries.append(current)
            list_key = None
            map_key = None
            rest = stripped[2:]
            if ":" in rest:
                k, _, v = rest.partition(":")
                if _strip(v):
                    current[k.strip()] = _strip(v)
            continue

        if current is None:
            continue

        if indent == 4 and stripped.endswith(":"):
            key = stripped[:-1].strip()
            if key in ("allowed_hosts", "blocked_apis"):
                current[key] = []
                list_key = key
                map_key = None
            elif key in ("on_block", "alert"):
                current[key] = {}
                map_key = key
                list_key = None
            continue

        if indent == 4 and ":" in stripped and not stripped.startswith("- "):
            k, _, v = stripped.partition(":")
            current[k.strip()] = _strip(v)
            list_key = None
            map_key = None
            continue

        if indent == 6 and stripped.startswith("- ") and list_key:
            current[list_key].append(_strip(stripped[2:]))
            continue

        if indent == 6 and ":" in stripped and map_key:
            k, _, v = stripped.partition(":")
            current[map_key][k.strip()] = _strip(v)
            continue

    return {"outbound_whitelist": entries}


def load_policies(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> Dict[str, AgentPolicy]:
    """Load per-agent outbound policies from ``config_path``."""
    data = _load_yaml_data(Path(config_path))
    entries = data.get("outbound_whitelist") or []
    policies: Dict[str, AgentPolicy] = {}
    for item in entries:
        if not isinstance(item, dict) or "agent" not in item:
            continue
        on_block = item.get("on_block") or {}
        alert = item.get("alert") or {}
        policies[item["agent"]] = AgentPolicy(
            agent=item["agent"],
            allowed_hosts=tuple(item.get("allowed_hosts") or ()),
            blocked_apis=tuple(item.get("blocked_apis") or ()),
            log_level=str(on_block.get("log_level", "ERROR")),
            exception_name=str(on_block.get("raise", "OutboundBlockedException")),
            alert_severity=str(alert.get("severity", "P0")),
            alert_owner=str(alert.get("owner", "render-team")),
        )
    return policies


class OutboundGateway:
    """Per-agent outbound egress enforcer.

    Policies may be supplied explicitly via ``policies=`` (unit tests);
    otherwise loaded lazily on first ``check`` from ``DEFAULT_CONFIG_PATH``.
    """

    def __init__(
        self,
        policies: Optional[Mapping[str, AgentPolicy]] = None,
        config_path: Path = DEFAULT_CONFIG_PATH,
    ) -> None:
        self._explicit_policies: Optional[Mapping[str, AgentPolicy]] = policies
        self._config_path = config_path
        self._policies_cache: Optional[Dict[str, AgentPolicy]] = None

    @property
    def policies(self) -> Mapping[str, AgentPolicy]:
        if self._explicit_policies is not None:
            return self._explicit_policies
        if self._policies_cache is None:
            self._policies_cache = load_policies(self._config_path)
        return self._policies_cache

    def check(self, *, agent: str, url: str) -> None:
        """Enforce the outbound policy for ``agent``.

        Raises :class:`OutboundBlockedException` if the destination host is
        not in the agent's ``allowed_hosts`` list. Agents without a declared
        policy are passed through unchanged (AC-6).
        """
        policy = self.policies.get(agent)
        if policy is None:
            return
        host = _normalize_host(url)
        allowed = {h.lower() for h in policy.allowed_hosts}
        if host and host in allowed:
            return
        reason = f"host {host!r} not in allowed_hosts for agent {agent!r}"
        self._emit_block(host=host, agent=agent, reason=reason, policy=policy)
        raise OutboundBlockedException(host=host, agent=agent, reason=reason)

    def _emit_block(
        self,
        *,
        host: str,
        agent: str,
        reason: str,
        policy: AgentPolicy,
    ) -> None:
        logger.error(
            "outbound.blocked",
            extra={
                "event": "outbound.blocked",
                "agent": agent,
                "host": host,
                "reason": reason,
            },
        )
        _ALERT_SINK.append(
            {
                "event": "outbound.blocked",
                "severity": policy.alert_severity,
                "owner": policy.alert_owner,
                "agent": agent,
                "host": host,
                "reason": reason,
            }
        )


def get_captured_alerts() -> List[Dict[str, Any]]:
    """Return a snapshot of the in-process alert sink (SPEC-14.4 hook)."""
    return list(_ALERT_SINK)


def clear_captured_alerts() -> None:
    """Reset the in-process alert sink (test helper)."""
    _ALERT_SINK.clear()
