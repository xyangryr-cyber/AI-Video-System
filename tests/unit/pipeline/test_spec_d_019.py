"""Tests for [SPEC-D-019] Gate-P5 升级."""


class TestAC1GateP5MixPreviewCheck:
    def test_gate_p5_mix_preview_exists(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check_v317(
            bgm_mix_preview_exists=True,
            user_selected=True,
            master_file_ready=True,
            master_playable=True,
            source_ref_valid=True,
            master_audio_ref_switched=True,
            reviewer_passed=True,
            no_bgm=False,
        )
        assert result["passed"] is True

    def test_no_bgm_path_skips_checks(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check_v317(
            no_bgm=True,
            reviewer_passed=False,  # reviewer irrelevant in no_bgm
        )
        assert result["passed"] is True


class TestAC2V317Checks:
    def test_missing_mix_preview_fails(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check_v317(
            bgm_mix_preview_exists=False,
            no_bgm=False,
        )
        assert result["passed"] is False

    def test_missing_master_file_fails(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check_v317(
            master_file_ready=False,
            no_bgm=False,
        )
        assert result["passed"] is False


class TestAC3MusicFitReviewerV317:
    def test_music_fit_v317_joint_pass(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check_v317(
            bgm_mix_preview_exists=True,
            user_selected=True,
            master_file_ready=True,
            master_playable=True,
            source_ref_valid=True,
            master_audio_ref_switched=True,
            reviewer_passed=True,
            no_bgm=False,
        )
        assert result["passed"] is True
