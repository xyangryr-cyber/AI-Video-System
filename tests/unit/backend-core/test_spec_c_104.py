"""Tests for [SPEC-C-104] PatchPlanner + DiffAuditor.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-5 SPEC-6.Z / SPEC-6.W.

Test matrix (AC mapping lives in the task card):
  AC-1 position recommendation returns 1..3 candidates, stable across runs.
  AC-2 DiffAuditor verdict boundary (5% PASS, 5.01% FAIL) + commit gate.
  AC-3 insert_section produces a brand-new segment_id (distinct from regenerate).
  AC-4 malicious LLM rewrites unrelated segments -> DiffAuditor FAIL.
"""

from __future__ import annotations

import pytest

from src.backend.agents.patch_planner import (
    PatchPlan,
    PatchPlanner,
    PositionCandidate,
)
from src.backend.services.diff_auditor import DiffAuditor, DiffResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _outline_three_sections() -> dict:
    return {
        "sections": [
            {
                "section_id": "intro",
                "topic": "AI 视频制作平台简介",
                "est_duration_sec": 30,
            },
            {
                "section_id": "compare",
                "topic": "传统流程 vs AI 流程",
                "est_duration_sec": 45,
            },
            {"section_id": "outlook", "topic": "未来展望", "est_duration_sec": 20},
        ]
    }


def _polished_script_six_segments() -> dict:
    return {
        "version": 1,
        "segments": [
            {
                "segment_id": "seg_001",
                "outline_section": "intro",
                "text": "开场:介绍 AI 视频制作平台。",
            },
            {
                "segment_id": "seg_002",
                "outline_section": "intro",
                "text": "平台的定位与目标用户。",
            },
            {
                "segment_id": "seg_003",
                "outline_section": "compare",
                "text": "传统流程需要 3 天。",
            },
            {
                "segment_id": "seg_004",
                "outline_section": "compare",
                "text": "AI 流程可以压缩到 30 分钟。",
            },
            {
                "segment_id": "seg_005",
                "outline_section": "outlook",
                "text": "未来一年的路线图。",
            },
            {
                "segment_id": "seg_006",
                "outline_section": "outlook",
                "text": "总结与结束。",
            },
        ],
    }


# ---------------------------------------------------------------------------
# AC-1
# ---------------------------------------------------------------------------


class TestAC1:
    """AC-1: 位置推荐 1-3 候选 `(after_segment_id, score, reason)`"""

    def test_position_recommends_one_to_three_candidates(self):
        planner = PatchPlanner()
        candidates = planner.recommend_positions(
            outline=_outline_three_sections(),
            polished_script=_polished_script_six_segments(),
            content_intent="补充一个新的对比环节:AI 渲染成本 vs 人工渲染成本",
        )

        assert isinstance(candidates, list)
        assert 1 <= len(candidates) <= 3

        for cand in candidates:
            assert isinstance(cand, PositionCandidate)
            assert isinstance(cand.after_segment_id, str) and cand.after_segment_id
            assert 0.0 <= cand.score <= 1.0
            assert isinstance(cand.reason, str) and cand.reason

        scores = [c.score for c in candidates]
        assert scores == sorted(scores, reverse=True), (
            "candidates must be sorted by score desc"
        )

        # Stability: same input -> identical candidates (SPEC AC §C-BDD-5).
        again = planner.recommend_positions(
            outline=_outline_three_sections(),
            polished_script=_polished_script_six_segments(),
            content_intent="补充一个新的对比环节:AI 渲染成本 vs 人工渲染成本",
        )
        assert [c.after_segment_id for c in again] == [
            c.after_segment_id for c in candidates
        ]
        assert [c.score for c in again] == [c.score for c in candidates]


# ---------------------------------------------------------------------------
# AC-2
# ---------------------------------------------------------------------------


class TestAC2:
    """AC-2: DiffAuditor unrelated_change_ratio > 5% 时 FAIL + 阻断 commit"""

    def test_unrelated_change_ratio_over_5pct_blocks_commit(self):
        auditor = DiffAuditor()

        # 20 segments baseline. Allowed modify: none (pure insert elsewhere).
        old = {
            "segments": [
                {"segment_id": f"seg_{i:03d}", "text": f"段落 {i}."} for i in range(20)
            ]
        }

        # Case A: exactly 1 unrelated change out of 20 = 5.0% -> PASS (boundary).
        new_pass = {
            "segments": [
                {
                    "segment_id": f"seg_{i:03d}",
                    "text": (f"段落 {i}." if i != 7 else "段落 7 改写了."),
                }
                for i in range(20)
            ]
        }
        scope = {"allowed_modify_segments": [], "max_unrelated_change_ratio": 0.05}
        result_pass = auditor.audit(
            old_artifact=old, new_artifact=new_pass, expected_diff_scope=scope
        )

        assert isinstance(result_pass, DiffResult)
        assert result_pass.verdict == "PASS"
        assert result_pass.unrelated_change_ratio == pytest.approx(0.05, abs=1e-9)
        assert result_pass.can_commit is True

        # Case B: 2 unrelated changes out of 20 = 10% -> FAIL.
        new_fail = {
            "segments": [
                {
                    "segment_id": f"seg_{i:03d}",
                    "text": (f"段落 {i}." if i not in (7, 13) else f"段落 {i} 改写了."),
                }
                for i in range(20)
            ]
        }
        result_fail = auditor.audit(
            old_artifact=old, new_artifact=new_fail, expected_diff_scope=scope
        )
        assert result_fail.verdict == "FAIL"
        assert result_fail.unrelated_change_ratio > 0.05
        assert result_fail.can_commit is False
        assert any(v.segment_id == "seg_007" for v in result_fail.violations)
        assert any(v.segment_id == "seg_013" for v in result_fail.violations)

        # Case C: fine-grained boundary — 5.1% must FAIL.
        old_big = {
            "segments": [
                {"segment_id": f"seg_{i:04d}", "text": f"段落 {i}."}
                for i in range(1000)
            ]
        }
        changed_ids = {f"seg_{i:04d}" for i in range(51)}  # 51/1000 = 5.1% > 5%
        new_over = {
            "segments": [
                {
                    "segment_id": sid,
                    "text": (
                        "改写了."
                        if sid in changed_ids
                        else f"段落 {int(sid.split('_')[1])}."
                    ),
                }
                for sid in (f"seg_{i:04d}" for i in range(1000))
            ]
        }
        result_over = auditor.audit(
            old_artifact=old_big, new_artifact=new_over, expected_diff_scope=scope
        )
        assert result_over.verdict == "FAIL"
        assert result_over.unrelated_change_ratio > 0.05
        assert result_over.can_commit is False


# ---------------------------------------------------------------------------
# AC-3
# ---------------------------------------------------------------------------


class TestAC3:
    """AC-3: 与 regenerate_section 路径区分:insert_section 产生新 segment_id"""

    def test_insert_section_creates_new_segment_id(self):
        planner = PatchPlanner()
        old_script = _polished_script_six_segments()
        existing_ids = {s["segment_id"] for s in old_script["segments"]}

        plan = planner.plan_insert(
            outline=_outline_three_sections(),
            polished_script=old_script,
            content_intent="补充 AI 渲染成本对比",
            source_artifact="polished_script.json",
            source_version=1,
        )
        assert isinstance(plan, PatchPlan)
        assert plan.source_artifact == "polished_script.json"
        assert plan.source_version == 1
        assert 1 <= len(plan.insertions) <= 3
        for ins in plan.insertions:
            assert ins["after_segment_id"] in existing_ids
            assert ins["content_intent"] == "补充 AI 渲染成本对比"
        assert plan.expected_diff_scope["max_unrelated_change_ratio"] == 0.05
        # Pure insert: allowed_modify_segments is empty (no existing segment may change).
        assert plan.expected_diff_scope["allowed_modify_segments"] == []

        # apply_insert creates a BRAND-NEW segment_id, leaves all old segments intact.
        new_script = planner.apply_insert(
            polished_script=old_script,
            patch_plan=plan,
            new_text="AI 渲染成本不到人工渲染的十分之一。",
        )
        new_ids = [s["segment_id"] for s in new_script["segments"]]
        added = set(new_ids) - existing_ids
        assert len(added) == 1, (
            "insert_section must produce exactly one brand-new segment_id"
        )
        new_id = next(iter(added))
        assert new_id not in existing_ids
        for old_seg in old_script["segments"]:
            match = next(
                s
                for s in new_script["segments"]
                if s["segment_id"] == old_seg["segment_id"]
            )
            assert match["text"] == old_seg["text"]

        # Legitimate insert artifact PASSES the auditor.
        auditor = DiffAuditor()
        result = auditor.audit(
            old_artifact=old_script,
            new_artifact=new_script,
            expected_diff_scope=plan.expected_diff_scope,
        )
        assert result.verdict == "PASS", (
            f"insert-only diff must pass auditor; got {result.verdict} "
            f"ratio={result.unrelated_change_ratio}"
        )


# ---------------------------------------------------------------------------
# AC-4
# ---------------------------------------------------------------------------


class TestAC4:
    """AC-4: 集成测试:恶意 LLM 输出改写无关段落 → FAIL"""

    def test_malicious_llm_unrelated_rewrite_fails(self):
        planner = PatchPlanner()
        old_script = _polished_script_six_segments()

        plan = planner.plan_insert(
            outline=_outline_three_sections(),
            polished_script=old_script,
            content_intent="补充 AI 渲染成本对比",
            source_artifact="polished_script.json",
            source_version=1,
        )

        # Simulate a malicious LLM that, in addition to inserting the new
        # segment, silently rewrote 3 unrelated existing segments (3/6 = 50%).
        tampered_segments = []
        rewrote_ids = {"seg_001", "seg_005", "seg_006"}
        for seg in old_script["segments"]:
            if seg["segment_id"] in rewrote_ids:
                tampered_segments.append({**seg, "text": seg["text"] + "【恶意注入】"})
            else:
                tampered_segments.append(dict(seg))
        # Still append a new segment so the shape matches insert_section.
        tampered_segments.append(
            {
                "segment_id": "seg_999",
                "outline_section": "compare",
                "text": "AI 成本更低。",
            }
        )
        tampered_new = {"version": 2, "segments": tampered_segments}

        auditor = DiffAuditor()
        result = auditor.audit(
            old_artifact=old_script,
            new_artifact=tampered_new,
            expected_diff_scope=plan.expected_diff_scope,
        )
        assert result.verdict == "FAIL"
        assert result.can_commit is False
        assert result.unrelated_change_ratio > 0.05
        violated = {v.segment_id for v in result.violations}
        assert rewrote_ids.issubset(violated), (
            f"every tampered segment must appear in violations; missing: "
            f"{rewrote_ids - violated}"
        )
