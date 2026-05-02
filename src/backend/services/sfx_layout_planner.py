"""[SPEC-C-019] SfxLayoutPlanner -- P6 Step 1 output-schema validator.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-4 item 3.

The task-card scope for this class is deliberately narrow: *this* service
is NOT the LLM agent itself. It is the orchestration hand-off point where
an already-generated layout payload (dict produced by the upstream LLM
agent or loaded from disk) is validated against the SPEC-A-014
``SfxLayoutPlan`` schema and returned as a Pydantic model. Downstream
``SfxSegmentMixService`` + ``FinalAudioAssembler`` consume the validated
model, never the raw dict.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.shared.schemas.sfx_layout_plan import SfxLayoutPlan


class SfxLayoutPlanner:
    """Validate + project an LLM-shaped layout payload onto SfxLayoutPlan."""

    def plan_from_payload(self, payload: Mapping[str, Any]) -> SfxLayoutPlan:
        """Validate a dict already shaped like ``sfx_layout_plan.json``."""
        return SfxLayoutPlan.model_validate(dict(payload))

    def plan_from_file(self, path: Path) -> SfxLayoutPlan:
        """Load ``sfx_layout_plan.json`` from disk and validate."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"sfx_layout_plan.json at {path} must be a JSON object")
        return SfxLayoutPlan.model_validate(data)


__all__ = ["SfxLayoutPlanner"]
