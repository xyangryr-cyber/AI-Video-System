"""Tests for [SPEC-D-103] shot 拆分语义对齐 + anchor 校验 + 预览态/生产态切换."""

from src.backend.services.shot_anchor_validator import ShotAnchorValidator


class TestAC1:
    """AC-1: L1-A4 anchor_text 是 polished_script substring（hash 比对）"""

    def test_l1_a4_anchor_text_is_substring_of_polished_script(self):
        validator = ShotAnchorValidator()
        polished_script = "The economy grew 5.2% in 2024 driven by strong exports and domestic consumption."
        anchor_text = "economy grew 5.2%"

        result = validator.check_l1_a4_anchor_substring(
            polished_script=polished_script,
            anchor_text=anchor_text,
        )
        assert result["passed"] is True
        assert result["rule"] == "L1-A4"

    def test_l1_a4_anchor_text_not_substring_fails(self):
        validator = ShotAnchorValidator()
        polished_script = "The economy grew 5.2% in 2024."
        anchor_text = "GDP surged 8.0%"  # Not in polished_script

        result = validator.check_l1_a4_anchor_substring(
            polished_script=polished_script,
            anchor_text=anchor_text,
        )
        assert result["passed"] is False


class TestAC2:
    """AC-2: L1-A5 子 shot 字符区间不重叠不遗漏"""

    def test_l1_a5_child_shot_intervals_no_overlap_no_gap(self):
        validator = ShotAnchorValidator()
        parent_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 26 chars
        child_shots = [
            {"shot_id": "s0", "char_start": 0, "char_end": 8},
            {"shot_id": "s1", "char_start": 8, "char_end": 17},
            {"shot_id": "s2", "char_start": 17, "char_end": 26},
        ]
        result = validator.check_l1_a5_intervals(
            parent_text_len=len(parent_text),
            child_shots=child_shots,
        )
        assert result["passed"] is True

    def test_l1_a5_overlap_fails(self):
        validator = ShotAnchorValidator()
        child_shots = [
            {"shot_id": "s0", "char_start": 0, "char_end": 10},
            {"shot_id": "s1", "char_start": 5, "char_end": 20},  # Overlaps s0
        ]
        result = validator.check_l1_a5_intervals(
            parent_text_len=20,
            child_shots=child_shots,
        )
        assert result["passed"] is False

    def test_l1_a5_gap_fails(self):
        validator = ShotAnchorValidator()
        child_shots = [
            {"shot_id": "s0", "char_start": 0, "char_end": 5},
            {"shot_id": "s1", "char_start": 8, "char_end": 20},  # Gap 5-8
        ]
        result = validator.check_l1_a5_intervals(
            parent_text_len=20,
            child_shots=child_shots,
        )
        assert result["passed"] is False


class TestAC3:
    """AC-3: L1-A6 子 shot 时长之和 = 父 shot 时长 ± 100ms"""

    def test_l1_a6_child_shot_durations_sum_equals_parent_within_100ms(self):
        validator = ShotAnchorValidator()
        parent_duration = 10.0
        child_durations = [3.5, 4.0, 2.5]  # sum = 10.0

        result = validator.check_l1_a6_duration_sum(
            parent_duration=parent_duration,
            child_durations=child_durations,
        )
        assert result["passed"] is True
        assert abs(result["sum_difference"]) <= 0.1

    def test_l1_a6_exceeds_tolerance_fails(self):
        validator = ShotAnchorValidator()
        parent_duration = 10.0
        child_durations = [3.0, 3.0, 3.5]  # sum = 9.5, diff = 0.5 > 0.1

        result = validator.check_l1_a6_duration_sum(
            parent_duration=parent_duration,
            child_durations=child_durations,
        )
        assert result["passed"] is False


class TestAC4:
    """AC-4: L1-A7 downstream_bindings 引用合法性（P8/P9/P10）"""

    def test_l1_a7_downstream_bindings_reference_validity(self):
        validator = ShotAnchorValidator()
        downstream_bindings = [
            {"phase": "P8", "shot_id": "shot_001"},
            {"phase": "P9", "material_id": "mat_xyz"},
            {"phase": "P10", "rough_cut_segment": "seg_abc"},
        ]
        result = validator.check_l1_a7_bindings(
            downstream_bindings=downstream_bindings,
        )
        assert result["passed"] is True

    def test_l1_a7_invalid_phase_fails(self):
        validator = ShotAnchorValidator()
        downstream_bindings = [
            {"phase": "P8", "shot_id": "shot_001"},
            {"phase": "P5", "something": "invalid"},  # P5 is not allowed
        ]
        result = validator.check_l1_a7_bindings(
            downstream_bindings=downstream_bindings,
        )
        assert result["passed"] is False
