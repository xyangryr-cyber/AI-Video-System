"""Tests for [SPEC-D-102] 局部插入 Scenario Cards + Gate-P2/P3 DiffAuditor 断言."""

from src.backend.engine.scenario_cards.insert_section_p2_card import (
    InsertSectionP2Card,
)
from src.backend.engine.scenario_cards.insert_section_p3_card import (
    InsertSectionP3Card,
)


class TestAC1:
    """AC-1: P2 insert_section 后 DiffAuditor.verdict=PASS 才进 Gate-P2"""

    def test_p2_insert_section_passes_with_diff_auditor_pass(self):
        card = InsertSectionP2Card()
        # Setup: old artifact with 20 segments, insert into segment_03 area
        old_segments = [
            {"segment_id": f"seg_{i:02d}", "text": f"original text {i}"}
            for i in range(20)
        ]
        result = card.handle_insert(
            old_segments=old_segments,
            after_segment_id="seg_02",
            content_intent="new inserted section about market trends",
        )
        assert result["diff_verdict"] == "PASS"
        # After diff pass, the gate should pass
        assert result["gate_passed"] is True
        # Only 1 segment added, ratio 1/20 = 5% <= threshold
        assert result["unrelated_change_ratio"] <= 0.05


class TestAC2:
    """AC-2: P3 同 P2"""

    def test_p3_insert_section_passes_with_diff_auditor_pass(self):
        card = InsertSectionP3Card()
        old_segments = [
            {"segment_id": f"seg_{i:02d}", "text": f"polished text {i}"}
            for i in range(20)
        ]
        result = card.handle_insert(
            old_segments=old_segments,
            after_segment_id="seg_05",
            content_intent="add summary section",
        )
        assert result["diff_verdict"] == "PASS"
        assert result["gate_passed"] is True


class TestAC3:
    """AC-3: 与 regenerate_section 测试区分：新 segment_id 必产生"""

    def test_insert_section_generates_new_segment_id(self):
        card = InsertSectionP2Card()
        old_segments = [
            {"segment_id": "seg_00", "text": "intro"},
            {"segment_id": "seg_01", "text": "body"},
            {"segment_id": "seg_02", "text": "conclusion"},
        ]
        result = card.handle_insert(
            old_segments=old_segments,
            after_segment_id="seg_01",
            content_intent="inserted content",
        )
        new_seg = result["new_segment"]
        assert "segment_id" in new_seg
        assert new_seg["segment_id"] not in {"seg_00", "seg_01", "seg_02"}
        # Must be a NEW id, not reusing existing
        assert (
            new_seg["segment_id"].startswith("seg_") or "new" in new_seg["segment_id"]
        )
        assert result["is_new_segment"] is True


class TestAC4:
    """AC-4: 5% 阈值恶意超出反例 FAIL"""

    def test_insert_section_fails_when_exceeds_5pct_threshold(self):
        card = InsertSectionP2Card()
        # 10 segments, attempt to modify a segment NOT in allowed scope
        old_segments = [
            {"segment_id": f"seg_{i:02d}", "text": f"original text {i}"}
            for i in range(10)
        ]
        # Malicious: modify 2 unrelated segments (ratio 2/10 = 20% > 5%)
        result = card._run_diff_audit(
            old_segments=old_segments,
            new_segments=[
                {"segment_id": "seg_00", "text": "MODIFIED unrelated"},
                {"segment_id": "seg_01", "text": "ANOTHER unrelated change"},
                *[
                    {"segment_id": f"seg_{i:02d}", "text": f"original text {i}"}
                    for i in range(2, 10)
                ],
            ],
            allowed_modify_segments=["seg_new"],
        )
        assert result["verdict"] == "FAIL"
        assert result["unrelated_change_ratio"] > 0.05
