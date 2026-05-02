"""[SPEC-D-017] PhaseScenarios -- scenario cards per phase."""

from __future__ import annotations

from typing import Any


class PhaseScenarios:
    """Look up scenario cards for each pipeline phase."""

    _CARDS: dict[int, dict[str, Any]] = {
        0: {"retry_limit": 5, "on_failure": "prompt_user"},
        1: {"retry_limit": 5, "on_failure": "return_to_p0"},
        2: {"retry_limit": 5, "on_failure": "retry_or_return"},
        3: {"retry_limit": 5, "on_failure": "freeze_manual_edit"},
        4: {"retry_limit": 3, "on_failure": "switch_provider"},
        5: {"retry_limit": 3, "on_failure": "skip_phase"},
        6: {"retry_limit": 3, "on_failure": "skip_phase"},
        7: {"retry_limit": 3, "on_failure": "rollback_invalidate"},
        8: {"retry_limit": 3, "on_failure": "degrade_text_card"},
        9: {"retry_limit": 3, "on_failure": "placeholder"},
        10: {"retry_limit": 3, "on_failure": "retry_or_warn"},
        11: {"retry_limit": 3, "on_failure": "retry_or_warn"},
    }

    @classmethod
    def get_scenario(cls, *, phase: int) -> dict[str, Any]:
        return dict(cls._CARDS.get(phase, {"retry_limit": 3, "on_failure": "retry"}))
