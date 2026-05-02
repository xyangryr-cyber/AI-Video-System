"""Unit tests for [SPEC-C-104] PatchPlanner (SPEC-6.Z).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-5.

Scope: PatchPlanner position recommendation + plan_insert + apply_insert.
AC-1 / AC-3 coverage (auditor-focused AC-2 / AC-4 live in the integration file).
"""

from __future__ import annotations

from src.backend.agents.patch_planner import (
    PatchPlan,
    PatchPlanner,
    PositionCandidate,
)


def _outline() -> dict:
    return {
        "sections": [
            {"section_id": "intro", "topic": "简介", "est_duration_sec": 20},
            {"section_id": "compare", "topic": "对比", "est_duration_sec": 40},
            {"section_id": "wrapup", "topic": "收尾", "est_duration_sec": 15},
        ]
    }


def _script() -> dict:
    return {
        "version": 1,
        "segments": [
            {"segment_id": "seg_a", "outline_section": "intro", "text": "开场。"},
            {
                "segment_id": "seg_b",
                "outline_section": "compare",
                "text": "旧流程很慢。",
            },
            {
                "segment_id": "seg_c",
                "outline_section": "compare",
                "text": "新流程很快。",
            },
            {"segment_id": "seg_d", "outline_section": "wrapup", "text": "总结。"},
        ],
    }


def test_recommend_positions_returns_one_to_three():
    cands = PatchPlanner().recommend_positions(
        outline=_outline(),
        polished_script=_script(),
        content_intent="补充成本对比",
    )
    assert 1 <= len(cands) <= 3
    assert all(isinstance(c, PositionCandidate) for c in cands)
    # after_segment_id must reference an existing segment.
    existing = {s["segment_id"] for s in _script()["segments"]}
    assert all(c.after_segment_id in existing for c in cands)
    # Sorted by score desc.
    assert [c.score for c in cands] == sorted((c.score for c in cands), reverse=True)


def test_recommend_positions_is_deterministic():
    a = PatchPlanner().recommend_positions(
        outline=_outline(), polished_script=_script(), content_intent="补充成本对比"
    )
    b = PatchPlanner().recommend_positions(
        outline=_outline(), polished_script=_script(), content_intent="补充成本对比"
    )
    assert [(c.after_segment_id, c.score) for c in a] == [
        (c.after_segment_id, c.score) for c in b
    ]


def test_plan_insert_emits_patch_plan_with_scope():
    plan = PatchPlanner().plan_insert(
        outline=_outline(),
        polished_script=_script(),
        content_intent="补充成本对比",
        source_artifact="polished_script.json",
        source_version=2,
    )
    assert isinstance(plan, PatchPlan)
    assert plan.source_version == 2
    assert 1 <= len(plan.insertions) <= 3
    assert plan.expected_diff_scope["max_unrelated_change_ratio"] == 0.05
    assert plan.expected_diff_scope["allowed_modify_segments"] == []


def test_apply_insert_creates_new_segment_id_only():
    script = _script()
    existing = {s["segment_id"] for s in script["segments"]}
    plan = PatchPlanner().plan_insert(
        outline=_outline(),
        polished_script=script,
        content_intent="补充成本对比",
        source_artifact="polished_script.json",
        source_version=1,
    )
    updated = PatchPlanner().apply_insert(
        polished_script=script, patch_plan=plan, new_text="新段落。"
    )
    new_ids = {s["segment_id"] for s in updated["segments"]}
    added = new_ids - existing
    assert len(added) == 1
    # Distinct from regenerate_section — old segments still present with same id + text.
    for old in script["segments"]:
        same = next(
            s for s in updated["segments"] if s["segment_id"] == old["segment_id"]
        )
        assert same["text"] == old["text"]
