"""[SPEC-C-020] SfxLayoutReviewer — L1 programmatic checks for the
global sfx_layout_plan.json artifact.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

Four L1 checks, all deterministic and 0-token:

* ``check_script_coverage`` — fraction of required narrative nodes that
  have a trigger with a matching ``narrative_role`` must be ≥
  ``SCRIPT_COVERAGE_MIN`` (0.5).
* ``check_keyword_anchor`` — for each trigger, token-Jaccard overlap
  between ``script_anchor.text`` and ``script_text[keyword_span]`` must
  be ≥ ``KEYWORD_ANCHOR_OVERLAP_MIN`` (0.8); any trigger below threshold
  fails the whole check.
* ``check_explanation_completeness`` — every trigger must have non-blank
  ``rationale`` and ``narrative_role`` (whitespace-only strings pass
  schema min_length=1 but fail this semantic check).
* ``check_sparsity`` — average inter-arrival gap must be ≥
  ``SPARSITY_AVG_GAP_MIN_S`` (15 s) **and** no rolling 30 s window may
  contain more than ``SPARSITY_MAX_PER_WINDOW`` (3) triggers.

:class:`ReviewVerdict` / :class:`ReviewReport` are reused from
``music_fit_reviewer`` so both v3.17 reviewers share the same shape
without introducing a new shared module (task card forbids it).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.backend.reviewers.music_fit_reviewer import (
    ReviewReport,
    ReviewVerdict,
    Verdict,
)
from src.shared.schemas.sfx_layout_plan import SfxLayoutPlan

SCRIPT_COVERAGE_MIN = 0.5
KEYWORD_ANCHOR_OVERLAP_MIN = 0.8
SPARSITY_AVG_GAP_MIN_S = 15.0
SPARSITY_WINDOW_S = 30.0
SPARSITY_MAX_PER_WINDOW = 3


def _tokens(text: str) -> set[str]:
    return {t for t in text.lower().split() if t}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


class SfxLayoutReviewer:
    """L1-only Reviewer for the global SFX layout plan."""

    def check_script_coverage(
        self,
        plan: SfxLayoutPlan,
        script_nodes: Sequence[Mapping[str, Any]],
    ) -> ReviewVerdict:
        if not script_nodes:
            return ReviewVerdict(
                check_name="script_coverage",
                verdict="PASS",
                reason="no script_nodes provided; coverage check skipped.",
                metrics={"ratio": 1.0, "covered": 0, "total": 0},
            )
        plan_roles = {t.narrative_role.strip() for t in plan.triggers}
        covered = 0
        for node in script_nodes:
            role = str(node.get("narrative_role", "")).strip()
            if role and role in plan_roles:
                covered += 1
        ratio = covered / len(script_nodes)
        if ratio < SCRIPT_COVERAGE_MIN:
            return ReviewVerdict(
                check_name="script_coverage",
                verdict="FAIL",
                reason=(
                    f"script_coverage={ratio:.2f} < {SCRIPT_COVERAGE_MIN}; "
                    f"{covered}/{len(script_nodes)} narrative nodes covered."
                ),
                metrics={
                    "ratio": ratio,
                    "covered": covered,
                    "total": len(script_nodes),
                },
            )
        return ReviewVerdict(
            check_name="script_coverage",
            verdict="PASS",
            reason=(
                f"script_coverage={ratio:.2f} >= {SCRIPT_COVERAGE_MIN} "
                f"({covered}/{len(script_nodes)} nodes)."
            ),
            metrics={
                "ratio": ratio,
                "covered": covered,
                "total": len(script_nodes),
            },
        )

    def check_keyword_anchor(
        self,
        plan: SfxLayoutPlan,
        script_text: str,
    ) -> ReviewVerdict:
        if not script_text or not plan.triggers:
            return ReviewVerdict(
                check_name="keyword_anchor",
                verdict="PASS",
                reason=("no script_text or no triggers; keyword_anchor skipped."),
                metrics={"per_trigger": []},
            )
        per_trigger: list[dict[str, Any]] = []
        any_fail = False
        for t in plan.triggers:
            start, end = t.keyword_span
            span_text = script_text[start:end]
            overlap = _jaccard(_tokens(t.script_anchor.text), _tokens(span_text))
            per_trigger.append(
                {
                    "trigger_id": t.trigger_id,
                    "overlap": overlap,
                    "anchor_text": t.script_anchor.text,
                    "span_text": span_text,
                }
            )
            if overlap < KEYWORD_ANCHOR_OVERLAP_MIN:
                any_fail = True
        if any_fail:
            return ReviewVerdict(
                check_name="keyword_anchor",
                verdict="FAIL",
                reason=(
                    f"at least one trigger anchor_text overlap < {KEYWORD_ANCHOR_OVERLAP_MIN}."
                ),
                metrics={"per_trigger": per_trigger},
            )
        return ReviewVerdict(
            check_name="keyword_anchor",
            verdict="PASS",
            reason=(f"all triggers anchor_text overlap >= {KEYWORD_ANCHOR_OVERLAP_MIN}."),
            metrics={"per_trigger": per_trigger},
        )

    def check_explanation_completeness(self, plan: SfxLayoutPlan) -> ReviewVerdict:
        missing: list[str] = []
        for t in plan.triggers:
            if not t.rationale.strip() or not t.narrative_role.strip():
                missing.append(t.trigger_id)
        if missing:
            return ReviewVerdict(
                check_name="explanation_completeness",
                verdict="FAIL",
                reason=(
                    f"{len(missing)} trigger(s) missing non-blank "
                    f"rationale/narrative_role: {missing}."
                ),
                metrics={"missing_trigger_ids": missing},
            )
        return ReviewVerdict(
            check_name="explanation_completeness",
            verdict="PASS",
            reason="all triggers have non-blank rationale + narrative_role.",
            metrics={"missing_trigger_ids": []},
        )

    def check_sparsity(self, plan: SfxLayoutPlan) -> ReviewVerdict:
        times = sorted(t.planned_time_sec for t in plan.triggers)
        n = len(times)
        if n < 2:
            return ReviewVerdict(
                check_name="sparsity",
                verdict="PASS",
                reason=f"only {n} trigger(s); sparsity trivially holds.",
                metrics={
                    "avg_gap_s": 0.0,
                    "max_per_window": n,
                    "n_triggers": n,
                },
            )
        gaps = [times[i + 1] - times[i] for i in range(n - 1)]
        avg_gap = sum(gaps) / len(gaps)
        max_count = 0
        for i in range(n):
            window_end = times[i] + SPARSITY_WINDOW_S
            count = sum(1 for t in times if times[i] <= t <= window_end)
            max_count = max(max_count, count)
        metrics: dict[str, Any] = {
            "avg_gap_s": avg_gap,
            "max_per_window": max_count,
            "n_triggers": n,
        }
        if avg_gap < SPARSITY_AVG_GAP_MIN_S or max_count > SPARSITY_MAX_PER_WINDOW:
            return ReviewVerdict(
                check_name="sparsity",
                verdict="FAIL",
                reason=(
                    f"sparsity FAIL: avg_gap={avg_gap:.2f}s (min "
                    f"{SPARSITY_AVG_GAP_MIN_S}s) / max_per_30s_window="
                    f"{max_count} (max {SPARSITY_MAX_PER_WINDOW})."
                ),
                metrics=metrics,
            )
        return ReviewVerdict(
            check_name="sparsity",
            verdict="PASS",
            reason=(f"sparsity OK: avg_gap={avg_gap:.2f}s, max_per_30s_window={max_count}."),
            metrics=metrics,
        )

    def review(
        self,
        *,
        plan: SfxLayoutPlan,
        script_nodes: Sequence[Mapping[str, Any]] | None = None,
        script_text: str = "",
    ) -> ReviewReport:
        checks: list[ReviewVerdict] = [
            self.check_script_coverage(plan, script_nodes or []),
            self.check_keyword_anchor(plan, script_text),
            self.check_explanation_completeness(plan),
            self.check_sparsity(plan),
        ]
        overall: Verdict = "FAIL" if any(c.verdict == "FAIL" for c in checks) else "PASS"
        return ReviewReport(verdict=overall, checks=checks)


__all__ = [
    "KEYWORD_ANCHOR_OVERLAP_MIN",
    "SCRIPT_COVERAGE_MIN",
    "SPARSITY_AVG_GAP_MIN_S",
    "SPARSITY_MAX_PER_WINDOW",
    "SPARSITY_WINDOW_S",
    "SfxLayoutReviewer",
]
