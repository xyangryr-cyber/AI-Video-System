"""[SPEC-C-104] DiffAuditor (SPEC-6.W).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-5 SPEC-6.W.

Compares an old artifact to a new artifact under an `expected_diff_scope`:
- `allowed_modify_segments`: ids that may legitimately change text.
- `max_unrelated_change_ratio`: upper bound (inclusive) for unrelated changes.

`unrelated_change_ratio` = (# segments outside `allowed_modify_segments` that
either changed text OR were deleted) / (# segments in the OLD artifact).

`verdict` is `PASS` when ratio <= max_unrelated_change_ratio, else `FAIL`.
FAIL populates `violations` and exposes `can_commit=False` so callers can
block artifact commit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Literal


__all__ = [
    "DiffViolation",
    "DiffResult",
    "DiffAuditor",
]


Verdict = Literal["PASS", "FAIL"]


@dataclass(frozen=True)
class DiffViolation:
    segment_id: str
    change_type: str  # "modified" | "deleted"
    details: str


@dataclass
class DiffResult:
    verdict: Verdict
    unrelated_change_ratio: float
    violations: List[DiffViolation] = field(default_factory=list)

    @property
    def can_commit(self) -> bool:
        return self.verdict == "PASS"


class DiffAuditor:
    """Stateless auditor. Safe to instantiate per call."""

    def audit(
        self,
        *,
        old_artifact: dict[str, Any],
        new_artifact: dict[str, Any],
        expected_diff_scope: dict[str, Any],
    ) -> DiffResult:
        allowed = set(expected_diff_scope.get("allowed_modify_segments") or [])
        max_ratio = float(expected_diff_scope.get("max_unrelated_change_ratio", 0.05))

        old_segments = {
            s["segment_id"]: s
            for s in (old_artifact.get("segments") or [])
            if s.get("segment_id")
        }
        new_segments = {
            s["segment_id"]: s
            for s in (new_artifact.get("segments") or [])
            if s.get("segment_id")
        }

        total = len(old_segments)
        if total == 0:
            # Nothing to audit against — trivially PASS, ratio 0.
            return DiffResult(verdict="PASS", unrelated_change_ratio=0.0, violations=[])

        violations: List[DiffViolation] = []
        unrelated_count = 0

        for seg_id, old_seg in old_segments.items():
            if seg_id in allowed:
                # Modifications (or deletion) on allowed ids are expected.
                continue
            new_seg = new_segments.get(seg_id)
            if new_seg is None:
                unrelated_count += 1
                violations.append(
                    DiffViolation(
                        segment_id=seg_id,
                        change_type="deleted",
                        details="segment removed outside allowed_modify_segments",
                    )
                )
                continue
            old_text = old_seg.get("text", "")
            new_text = new_seg.get("text", "")
            if old_text != new_text:
                unrelated_count += 1
                violations.append(
                    DiffViolation(
                        segment_id=seg_id,
                        change_type="modified",
                        details=(
                            f"text changed outside allowed scope: "
                            f"old_len={len(old_text)} new_len={len(new_text)}"
                        ),
                    )
                )

        ratio = unrelated_count / total
        # Use inclusive comparison at the threshold; 5% PASS, 5.01% FAIL.
        verdict: Verdict = "PASS" if ratio <= max_ratio + 1e-12 else "FAIL"
        return DiffResult(
            verdict=verdict,
            unrelated_change_ratio=ratio,
            violations=violations,
        )
