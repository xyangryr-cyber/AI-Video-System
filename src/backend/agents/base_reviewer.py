"""[SPEC-D-010] BaseReviewer -- abstract base class for all reviewers.

Authority: docs/specs/SPEC-D-pipeline-phases.md "Reviewer/Gate/Verdict binding"

Placed outside reviewers/ package to avoid circular import.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseReviewer(ABC):
    """Abstract reviewer: every reviewer must implement review()."""

    @abstractmethod
    def review(self, artifact: Any) -> dict[str, Any]:
        """Return standard verdict: {verdict, notes[], blocking_issues[]}."""
        ...
