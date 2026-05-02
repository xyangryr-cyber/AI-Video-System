"""Integration tests for [SPEC-C-104] DiffAuditor 5% boundary + malicious rewrite.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-5 SPEC-6.W.

Scope:
  - 5% boundary: exactly 5% PASS, 5.01% FAIL (SPEC AC assertion).
  - Malicious LLM rewrite of unrelated segments must FAIL + block commit.
"""

from __future__ import annotations

import pytest

from src.backend.agents.patch_planner import PatchPlanner
from src.backend.services.diff_auditor import DiffAuditor, DiffResult


def _old_20() -> dict:
    return {
        "segments": [
            {"segment_id": f"seg_{i:03d}", "text": f"段落 {i}."} for i in range(20)
        ]
    }


def test_boundary_exact_5pct_is_pass():
    scope = {"allowed_modify_segments": [], "max_unrelated_change_ratio": 0.05}
    new = {
        "segments": [
            {
                "segment_id": f"seg_{i:03d}",
                "text": (f"段落 {i}." if i != 3 else "改写了"),
            }
            for i in range(20)
        ]
    }
    result = DiffAuditor().audit(
        old_artifact=_old_20(), new_artifact=new, expected_diff_scope=scope
    )
    assert isinstance(result, DiffResult)
    assert result.verdict == "PASS"
    assert result.unrelated_change_ratio == pytest.approx(0.05, abs=1e-9)
    assert result.can_commit is True


def test_boundary_just_over_5pct_is_fail():
    # 1000 baseline segments; 51 unrelated changes -> 5.1% > 5% -> FAIL.
    scope = {"allowed_modify_segments": [], "max_unrelated_change_ratio": 0.05}
    old = {
        "segments": [
            {"segment_id": f"seg_{i:04d}", "text": f"段落 {i}."} for i in range(1000)
        ]
    }
    changed = {f"seg_{i:04d}" for i in range(51)}
    new = {
        "segments": [
            {
                "segment_id": sid,
                "text": (
                    "改写了" if sid in changed else f"段落 {int(sid.split('_')[1])}."
                ),
            }
            for sid in (f"seg_{i:04d}" for i in range(1000))
        ]
    }
    result = DiffAuditor().audit(
        old_artifact=old, new_artifact=new, expected_diff_scope=scope
    )
    assert result.verdict == "FAIL"
    assert result.unrelated_change_ratio > 0.05
    assert result.can_commit is False


def test_malicious_llm_unrelated_rewrite_fails_end_to_end():
    # Plan a legitimate insert, then simulate a malicious LLM that also
    # rewrote unrelated existing segments. Auditor must catch it.
    old_script = {
        "version": 1,
        "segments": [
            {"segment_id": "seg_001", "outline_section": "intro", "text": "开场。"},
            {"segment_id": "seg_002", "outline_section": "intro", "text": "平台定位。"},
            {
                "segment_id": "seg_003",
                "outline_section": "compare",
                "text": "旧流程慢。",
            },
            {
                "segment_id": "seg_004",
                "outline_section": "compare",
                "text": "新流程快。",
            },
            {"segment_id": "seg_005", "outline_section": "outlook", "text": "未来。"},
            {"segment_id": "seg_006", "outline_section": "outlook", "text": "总结。"},
        ],
    }
    outline = {
        "sections": [
            {"section_id": "intro", "topic": "简介", "est_duration_sec": 20},
            {"section_id": "compare", "topic": "对比", "est_duration_sec": 40},
            {"section_id": "outlook", "topic": "展望", "est_duration_sec": 20},
        ]
    }

    plan = PatchPlanner().plan_insert(
        outline=outline,
        polished_script=old_script,
        content_intent="补充成本对比",
        source_artifact="polished_script.json",
        source_version=1,
    )

    rewrote = {"seg_001", "seg_005", "seg_006"}
    tampered = []
    for seg in old_script["segments"]:
        if seg["segment_id"] in rewrote:
            tampered.append({**seg, "text": seg["text"] + "【恶意注入】"})
        else:
            tampered.append(dict(seg))
    tampered.append(
        {"segment_id": "seg_999", "outline_section": "compare", "text": "新插入。"}
    )
    tampered_new = {"version": 2, "segments": tampered}

    result = DiffAuditor().audit(
        old_artifact=old_script,
        new_artifact=tampered_new,
        expected_diff_scope=plan.expected_diff_scope,
    )
    assert result.verdict == "FAIL"
    assert result.can_commit is False
    violated = {v.segment_id for v in result.violations}
    assert rewrote.issubset(violated), f"missing: {rewrote - violated}"
