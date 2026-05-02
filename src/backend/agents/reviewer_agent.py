"""[SPEC-C-010] Reviewer Agent & Dual-Layer Architecture (L1 + L2).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.2 / SPEC-5.3.

What this module is
-------------------
The Reviewer surface for the whole system. Three concerns live here:

1. **Fixed output schema (SPEC-5.2)** -- :class:`ReviewerOutput` encodes
   ``{verdict, notes[], blocking_issues[]}``. ``verdict`` is a Literal of
   exactly ``"PASS"`` or ``"FAIL"``; a model-level validator enforces the
   two-way invariant ``blocking_issues non-empty <=> verdict == FAIL``.
   Any 12 Reviewer output therefore shares one parse path.

2. **Dual-layer execution (SPEC-5.3)** -- :class:`PureL1Reviewer` runs
   only an L1 (programmatic, 0 tokens) callable. :class:`HybridReviewer`
   runs L1 first and invokes L2 (LLM-backed) **only when L1 returns
   PASS**, so the token budget on an L1-failing artifact is guaranteed
   zero. ``tokens_used`` on the returned :class:`ReviewerOutput` records
   the observed L2 spend (0 when L1 fails, or when L2 itself did not
   report any spend).

3. **12-reviewer registry (AC-6)** -- :func:`get_reviewer` and
   :func:`list_reviewers` expose the complete set:

   - 6 pure-L1: ``AudioQualityReviewer``, ``AVSyncReviewer``,
     ``SFXReviewer``, ``StoryboardReviewer``, ``VisualReviewer``,
     ``FinalReviewer``.
   - 6 hybrid: ``CompletenessReviewer``, ``StructureReviewer``,
     ``StyleReviewer``, ``FactCheckerReviewer``, ``MusicFitReviewer``,
     ``BRollFitReviewer``.

Stateless by design
-------------------
Reviewer instances hold only their (name, l1, l2) triple. Each
``review()`` call is an independent function invocation; there is no
cross-call state and no warmup, which makes them safe to instantiate per
request and to cache at the registry level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field, model_validator


Verdict = Literal["PASS", "FAIL"]


# -- Output schema (SPEC-5.2) --------------------------------------------


class ReviewerOutput(BaseModel):
    """Fixed Reviewer output schema.

    Invariant (SPEC-5.2 AC-2): ``len(blocking_issues) > 0`` iff
    ``verdict == "FAIL"``. The validator below enforces both directions
    so the two fields can never disagree at construction time.

    ``tokens_used`` is an observability field used by SPEC-5.3 AC-3/AC-4
    to assert that L2 did not run when L1 failed and that pure-L1
    reviewers stay at 0 tokens. It is a structural counter, not a cost
    estimate, so defaults to 0 when callers omit it.
    """

    verdict: Verdict
    notes: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    tokens_used: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _verdict_matches_blocking(self) -> "ReviewerOutput":
        has_blockers = len(self.blocking_issues) > 0
        if has_blockers and self.verdict != "FAIL":
            raise ValueError(
                "blocking_issues is non-empty but verdict != 'FAIL' "
                "(SPEC-5.2 AC-2 two-way invariant)"
            )
        if not has_blockers and self.verdict != "PASS":
            raise ValueError(
                "blocking_issues is empty but verdict != 'PASS' "
                "(SPEC-5.2 AC-2 two-way invariant)"
            )
        return self


# -- Reviewer implementations (SPEC-5.3) ---------------------------------


L1Callable = Callable[[Any], ReviewerOutput]
L2Callable = Callable[[Any], ReviewerOutput]


@dataclass(frozen=True)
class PureL1Reviewer:
    """A Reviewer that runs only the programmatic L1 check.

    Pure-L1 reviewers are structurally incapable of spending tokens:
    :meth:`review` never invokes an LLM path. The six members of this
    class (AudioQuality, AVSync, SFX, Storyboard, Visual, Final) are the
    SPEC-5.3 AC-4 "0-token on any call" set.
    """

    name: str
    l1: L1Callable

    def review(self, artifact: Any) -> ReviewerOutput:
        out = self.l1(artifact)
        # Normalise tokens_used to 0; the L1 implementation is not
        # supposed to report any and callers rely on this invariant.
        if out.tokens_used != 0:
            out = out.model_copy(update={"tokens_used": 0})
        return out


@dataclass(frozen=True)
class HybridReviewer:
    """A Reviewer that runs L1 first and gates L2 on an L1 PASS.

    SPEC-5.3 AC-3 / AC-5: when L1 returns FAIL the L2 callable MUST NOT
    be invoked, so the observed ``tokens_used`` for an L1-failing
    artifact is exactly 0. When L1 returns PASS, L2 is invoked once and
    its output is returned verbatim.
    """

    name: str
    l1: L1Callable
    l2: L2Callable

    def review(self, artifact: Any) -> ReviewerOutput:
        l1_out = self.l1(artifact)
        if l1_out.verdict == "FAIL":
            # L2 skipped -> zero tokens, L1 output returned as-is with
            # tokens_used normalised to 0.
            if l1_out.tokens_used != 0:
                l1_out = l1_out.model_copy(update={"tokens_used": 0})
            return l1_out
        # L1 PASS -> run L2 semantic review.
        return self.l2(artifact)


# -- 12-reviewer registry (AC-6) -----------------------------------------


PURE_L1_REGISTRY: dict[str, L1Callable] = {}
HYBRID_REGISTRY: dict[str, L1Callable] = {}


def _register_defaults() -> None:
    """Wire the default L1 callables from :mod:`.reviewers.l1_checks`.

    Local import avoids a circular dependency at module import time:
    :mod:`.reviewers.l1_checks` imports :class:`ReviewerOutput` from
    this module.
    """
    from src.backend.agents.reviewers import l1_checks

    PURE_L1_REGISTRY.update(
        {
            "AudioQualityReviewer": l1_checks.audio_quality_l1,
            "AVSyncReviewer": l1_checks.av_sync_l1,
            "SFXReviewer": l1_checks.sfx_l1,
            "StoryboardReviewer": l1_checks.storyboard_l1,
            "VisualReviewer": l1_checks.visual_l1,
            "FinalReviewer": l1_checks.final_l1,
        }
    )
    HYBRID_REGISTRY.update(
        {
            "CompletenessReviewer": l1_checks.completeness_l1,
            "StructureReviewer": l1_checks.structure_l1,
            "StyleReviewer": l1_checks.style_l1,
            "FactCheckerReviewer": l1_checks.fact_checker_l1,
            "MusicFitReviewer": l1_checks.music_fit_l1,
            "BRollFitReviewer": l1_checks.broll_fit_l1,
        }
    )


_register_defaults()


def list_reviewers() -> tuple[str, ...]:
    """Return all 12 registered reviewer names (pure-L1 + hybrid)."""
    return tuple(sorted(set(PURE_L1_REGISTRY) | set(HYBRID_REGISTRY)))


def get_reviewer(
    name: str,
    *,
    l2: L2Callable | None = None,
) -> PureL1Reviewer | HybridReviewer:
    """Look up a Reviewer by name.

    - Pure-L1 reviewers: ``l2`` MUST be omitted; passing one raises.
    - Hybrid reviewers: ``l2`` is required; it is dependency-injected so
      tests and offline environments can avoid a real LLM call.
    """
    if name in PURE_L1_REGISTRY:
        if l2 is not None:
            raise ValueError(
                f"{name} is a pure-L1 reviewer; it does not accept an l2 callable"
            )
        return PureL1Reviewer(name=name, l1=PURE_L1_REGISTRY[name])
    if name in HYBRID_REGISTRY:
        if l2 is None:
            raise ValueError(
                f"{name} is a hybrid reviewer; an l2 callable is required "
                "(inject a test stub or use reviewers.l2_checks.build_llm_l2)"
            )
        return HybridReviewer(name=name, l1=HYBRID_REGISTRY[name], l2=l2)
    raise KeyError(f"unknown reviewer {name!r}; registered: {list_reviewers()}")


__all__ = [
    "HybridReviewer",
    "L1Callable",
    "L2Callable",
    "PureL1Reviewer",
    "ReviewerOutput",
    "Verdict",
    "get_reviewer",
    "list_reviewers",
    "HYBRID_REGISTRY",
    "PURE_L1_REGISTRY",
]
