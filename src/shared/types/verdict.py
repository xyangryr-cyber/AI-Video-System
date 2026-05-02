"""[SPEC-D-001] Reviewer Verdict / Gate check result types.

Authority:
  - docs/specs/SPEC-D-pipeline-phases.md "Reviewer / Gate / Verdict unified binding"
  - SPEC-C SPEC-5.2 for veredict format
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Verdict(BaseModel):
    """Reviewer veredict: PASS|FAIL with notes and blocking issues.

    Enforced by AC-4: *verdict* is Literal["PASS","FAIL"], *notes* and
    *blocking_issues* are required lists of strings (empty list is fine for
    PASS with no notes).
    """

    verdict: Literal["PASS", "FAIL"]
    notes: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
