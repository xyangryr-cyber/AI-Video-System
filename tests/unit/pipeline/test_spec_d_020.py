"""Tests for [SPEC-D-020] Gate-P6 升级."""


class TestAC1GateP6V317:
    def test_gate_p6_final_audio_master_checks(self):
        from src.backend.gates.gate_p6 import GateP6

        gate = GateP6()
        result = gate.check_v317(
            final_audio_master_exists=True,
            master_playable=True,
            checksum_consistent=True,
            source_ref_valid=True,
            reviewer_passed=True,
        )
        assert result["passed"] is True

    def test_missing_final_master_fails(self):
        from src.backend.gates.gate_p6 import GateP6

        gate = GateP6()
        result = gate.check_v317(
            final_audio_master_exists=False,
        )
        assert result["passed"] is False

    def test_segment_mix_checks(self):
        from src.backend.gates.gate_p6 import GateP6

        gate = GateP6()
        result = gate.check_v317(
            final_audio_master_exists=True,
            master_playable=True,
            checksum_consistent=True,
            source_ref_valid=True,
            reviewer_passed=True,
            segment_mix_complete=True,
        )
        assert result["passed"] is True
