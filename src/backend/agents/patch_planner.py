"""[SPEC-C-104] PatchPlanner (SPEC-6.Z).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-5 SPEC-6.Z.

Produces 1..3 `(after_segment_id, score, reason)` candidates for where to
insert a new section, wraps them into a `PatchPlan` with an `expected_diff_scope`
(default `max_unrelated_change_ratio = 0.05`), and provides `apply_insert` that
produces a brand-new `segment_id` while leaving every existing segment
untouched (the semantic that distinguishes `insert_section` from
`regenerate_section`).

Recommendation algorithm (SPEC §C-BDD-5, deterministic v1):
  score = 0.3 * narrative_pacing + 0.4 * topic_adjacency + 0.3 * duration_balance

Determinism: pure function of `(outline, polished_script, content_intent)`;
no randomness, no clock.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "PositionCandidate",
    "PatchPlan",
    "PatchPlanner",
]


_DEFAULT_MAX_UNRELATED_CHANGE_RATIO = 0.05


@dataclass(frozen=True)
class PositionCandidate:
    after_segment_id: str
    score: float
    reason: str


@dataclass
class PatchPlan:
    patch_plan_id: str
    source_artifact: str
    source_version: int
    insertions: list[dict[str, object]] = field(default_factory=list)
    expected_diff_scope: dict[str, object] = field(default_factory=dict)


class PatchPlanner:
    """Stateless planner. No external I/O; safe to instantiate per call."""

    def __init__(self, *, max_candidates: int = 3) -> None:
        if not 1 <= max_candidates <= 3:
            raise ValueError("max_candidates must be in [1, 3]")
        self._max_candidates = max_candidates

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend_positions(
        self,
        *,
        outline: dict[str, Any],
        polished_script: dict[str, Any],
        content_intent: str,
    ) -> list[PositionCandidate]:
        segments = list(polished_script.get("segments") or [])
        if not segments:
            raise ValueError("polished_script must have at least one segment")

        intent_tokens = _tokens(content_intent)
        sections_by_id = {
            s.get("section_id"): s for s in (outline.get("sections") or []) if s.get("section_id")
        }
        avg_duration = _avg_section_duration(outline)

        scored: list[PositionCandidate] = []
        for idx, seg in enumerate(segments):
            seg_id = seg.get("segment_id")
            if not seg_id:
                continue
            topic = sections_by_id.get(seg.get("outline_section"), {}).get("topic", "")
            seg_tokens = _tokens(f"{seg.get('text', '')} {topic}")

            topic_adjacency = _jaccard(intent_tokens, seg_tokens)
            narrative_pacing = _pacing_weight(idx, len(segments))
            duration_balance = _duration_balance(
                section=sections_by_id.get(seg.get("outline_section"), {}),
                avg_duration=avg_duration,
            )
            score = 0.3 * narrative_pacing + 0.4 * topic_adjacency + 0.3 * duration_balance
            # Clamp to [0, 1] so the caller contract is simple to assert.
            score = max(0.0, min(1.0, score))

            reason_parts = [
                f"topic_adjacency={topic_adjacency:.2f}",
                f"narrative_pacing={narrative_pacing:.2f}",
                f"duration_balance={duration_balance:.2f}",
            ]
            scored.append(
                PositionCandidate(
                    after_segment_id=seg_id,
                    score=round(score, 4),
                    reason=" | ".join(reason_parts),
                )
            )

        # Deterministic tie-break: higher score first, then earlier segment index
        # (already implicit via the enumeration order we appended in).
        scored.sort(key=lambda c: (-c.score, _segment_index(c.after_segment_id, segments)))
        return scored[: self._max_candidates]

    def plan_insert(
        self,
        *,
        outline: dict[str, Any],
        polished_script: dict[str, Any],
        content_intent: str,
        source_artifact: str = "polished_script.json",
        source_version: int = 1,
    ) -> PatchPlan:
        candidates = self.recommend_positions(
            outline=outline,
            polished_script=polished_script,
            content_intent=content_intent,
        )
        insertions: list[dict[str, object]] = [
            {
                "after_segment_id": cand.after_segment_id,
                "content_intent": content_intent,
                "proposed_position_reason": cand.reason,
                "expected_segment_count": 1,
            }
            for cand in candidates
        ]
        expected_diff_scope: dict[str, object] = {
            # insert_section is a pure addition: no existing segment may change.
            # regenerate_section would put the target id here instead.
            "allowed_modify_segments": [],
            "max_unrelated_change_ratio": _DEFAULT_MAX_UNRELATED_CHANGE_RATIO,
        }
        plan_seed = (
            f"{source_artifact}|{source_version}|{content_intent}|"
            f"{','.join(c.after_segment_id for c in candidates)}"
        )
        patch_plan_id = "patch_" + hashlib.sha256(plan_seed.encode("utf-8")).hexdigest()[:16]
        return PatchPlan(
            patch_plan_id=patch_plan_id,
            source_artifact=source_artifact,
            source_version=source_version,
            insertions=insertions,
            expected_diff_scope=expected_diff_scope,
        )

    def apply_insert(
        self,
        *,
        polished_script: dict[str, Any],
        patch_plan: PatchPlan,
        new_text: str,
        outline_section: str | None = None,
    ) -> dict[str, Any]:
        if not patch_plan.insertions:
            raise ValueError("patch_plan has no insertions to apply")
        # Apply the top-ranked insertion (head of the list).
        target = patch_plan.insertions[0]
        after_id = target["after_segment_id"]

        existing_ids = {s["segment_id"] for s in polished_script.get("segments") or []}
        new_segment_id = _mint_segment_id(
            plan_id=patch_plan.patch_plan_id,
            after_id=str(after_id),
            existing=existing_ids,
        )
        resolved_section = outline_section
        if resolved_section is None:
            for seg in polished_script.get("segments") or []:
                if seg.get("segment_id") == after_id:
                    resolved_section = seg.get("outline_section")
                    break

        out_segments: list[dict[str, Any]] = []
        for seg in polished_script.get("segments") or []:
            # Copy-through preserves every existing segment byte-for-byte.
            out_segments.append(dict(seg))
            if seg.get("segment_id") == after_id:
                out_segments.append(
                    {
                        "segment_id": new_segment_id,
                        "outline_section": resolved_section,
                        "text": new_text,
                    }
                )
        return {**polished_script, "segments": out_segments}


# ---------------------------------------------------------------------------
# Helpers (private)
# ---------------------------------------------------------------------------


def _tokens(text: str) -> set[str]:
    if not text:
        return set()
    # Split on whitespace + common Chinese punctuation; lowercase ASCII.
    import re

    raw = re.split(r"[\s,;:。，、;:·!?!?\-　]+", text.lower())
    return {t for t in raw if t}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _pacing_weight(idx: int, total: int) -> float:
    # Middle of the script is the strongest narrative-pacing fit for an
    # inserted comparison. Triangular peak at the midpoint in [0, 1].
    if total <= 1:
        return 1.0
    pos = idx / (total - 1)
    return 1.0 - abs(pos - 0.5) * 2.0


def _avg_section_duration(outline: dict[str, Any]) -> float:
    secs = outline.get("sections") or []
    if not secs:
        return 0.0
    total = sum(float(s.get("est_duration_sec", 0) or 0) for s in secs)
    return total / len(secs) if secs else 0.0


def _duration_balance(*, section: dict[str, Any], avg_duration: float) -> float:
    d = float(section.get("est_duration_sec", 0) or 0)
    if avg_duration <= 0:
        return 0.5
    # Closer to average -> higher balance score, clamped to [0, 1].
    deviation = abs(d - avg_duration) / avg_duration
    return max(0.0, 1.0 - deviation)


def _segment_index(segment_id: str, segments: list[dict[str, Any]]) -> int:
    for i, s in enumerate(segments):
        if s.get("segment_id") == segment_id:
            return i
    return 10**6


def _mint_segment_id(*, plan_id: str, after_id: str, existing: set[str]) -> str:
    base = hashlib.sha256(f"{plan_id}|{after_id}".encode()).hexdigest()[:12]
    candidate = f"seg_ins_{base}"
    # Collision guard (SHA-256 12-hex is already unique in practice, but be safe).
    suffix = 0
    while candidate in existing:
        suffix += 1
        candidate = f"seg_ins_{base}_{suffix}"
    return candidate
