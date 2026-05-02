"""[SPEC-C-010] L2 (LLM-backed) semantic checks for hybrid reviewers.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.3 / SPEC-5.4.

L2 is only consumed by the 6 hybrid reviewers (Completeness, Structure,
Style, FactChecker, MusicFit, BRollFit) and is invoked exclusively after
L1 returns PASS, so pure-L1 reviewers stay at exactly 0 tokens per call
(SPEC-5.3 AC).

The real LLM bridge is provided by :func:`build_llm_l2`, which wraps
:func:`src.backend.services.llm_service.chat_completion` using the
``reviewer`` role (SPEC-5.5). Tests and offline environments inject a
fake callable directly into :class:`HybridReviewer`, so this module's
LLM path is dependency-injected, not imported implicitly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.backend.agents.reviewer_agent import ReviewerOutput

L2Callable = Callable[[Any], ReviewerOutput]


def build_llm_l2(reviewer_name: str) -> L2Callable:
    """Return an L2 callable that routes through llm_service.

    The returned callable performs a structured LLM call under the
    ``reviewer`` role; it only runs when a hybrid reviewer's L1 has
    already passed, so callers never observe an LLM hit on an L1-failing
    artifact.
    """

    def _run(artifact: Any) -> ReviewerOutput:
        # Local import keeps this module free of llm_service at import
        # time -- pure-L1 reviewers and unit tests never pay that cost.
        from src.backend.services import llm_service

        messages = [
            {
                "role": "user",
                "content": (
                    f"You are {reviewer_name}. Review the following artifact "
                    "and respond with JSON of shape "
                    '{"verdict":"PASS"|"FAIL","notes":[],"blocking_issues":[]}. '
                    f"Artifact: {artifact!r}"
                ),
            }
        ]
        result = llm_service.chat_completion(
            role="reviewer",
            messages=messages,
            response_model=ReviewerOutput,
        )
        if not isinstance(result, ReviewerOutput):  # pragma: no cover
            raise TypeError(
                "llm_service returned unexpected type "
                f"{type(result).__name__}; expected ReviewerOutput"
            )
        return result

    return _run


__all__ = ["L2Callable", "build_llm_l2"]
