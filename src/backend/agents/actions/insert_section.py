"""[SPEC-C-101] insert_section action params (v3.16 C-BDD-2).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-2.

Idempotency: (SHA-256(anchor_json), SHA-256(content_intent)) — 5 min.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ExpectedDiffScope = Literal["adjacent", "trailing", "local"]


class InsertSectionAnchor(BaseModel):
    """Anchor locating where the new section goes (segment OR outline)."""

    model_config = ConfigDict(extra="forbid")

    after_segment_id: str | None = None
    after_outline_section: str | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> InsertSectionAnchor:
        if self.after_segment_id is None and self.after_outline_section is None:
            raise ValueError("anchor requires either `after_segment_id` or `after_outline_section`")
        return self


class InsertSectionParams(BaseModel):
    """Params for user-requested insertion of a new section into an artifact."""

    model_config = ConfigDict(extra="forbid")

    anchor: InsertSectionAnchor
    content_intent: str = Field(min_length=1)
    expected_diff_scope: ExpectedDiffScope


__all__ = [
    "ExpectedDiffScope",
    "InsertSectionAnchor",
    "InsertSectionParams",
]
