"""[SPEC-C-100] ResponseGenerator — template renderer with mtime-hot-reload."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.backend.agents.safety.policy_decision import DECISION_LEVELS, DecisionLevel


class ResponseGenerator:
    """Pure-template response renderer; reloads YAML when mtime changes."""

    def __init__(self, templates_path: str | Path) -> None:
        self._path = Path(templates_path)
        self._mtime: float | None = None
        self._templates: dict[DecisionLevel, str] = {}
        self._load()

    def _load(self) -> None:
        raw = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        tpls = raw.get("templates") or {}
        self._templates = {level: str(tpls.get(level, "")) for level in DECISION_LEVELS}
        self._mtime = self._path.stat().st_mtime

    def _maybe_reload(self) -> None:
        try:
            cur = self._path.stat().st_mtime
        except FileNotFoundError:
            return
        if cur != self._mtime:
            self._load()

    def render(self, decision: DecisionLevel, **context: Any) -> str:
        self._maybe_reload()
        template = self._templates.get(decision, "")
        if context:
            try:
                return template.format(**context)
            except (KeyError, IndexError):
                return template
        return template
