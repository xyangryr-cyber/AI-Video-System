"""[SPEC-D-017] RollbackCascade -- compute downstream invalidation on phase rollback."""

from __future__ import annotations


class RollbackCascade:
    """When a phase is rolled back, compute phases that must be invalidated."""

    @staticmethod
    def compute_cascade(*, invalid_phase: int, max_phase: int) -> set[int]:
        invalidated: set[int] = set()
        for p in range(invalid_phase, max_phase + 1):
            invalidated.add(p)
        if invalid_phase > 0:
            invalidated.discard(0)  # P0 preserved
        return invalidated
