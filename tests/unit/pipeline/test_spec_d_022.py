"""Tests for [SPEC-D-022] Gate-P8 升级."""


class TestAC1GateP8Readiness:
    def test_gate_p8_material_readiness_check(self):
        from src.backend.gates.gate_p8 import GateP8

        gate = GateP8()
        result = gate.check_v317(
            renders_complete=True,
            material_readiness=True,
            degraded_shots=0,
            reviewer_passed=True,
        )
        assert result["passed"] is True

    def test_material_not_ready_fails(self):
        from src.backend.gates.gate_p8 import GateP8

        gate = GateP8()
        result = gate.check_v317(
            renders_complete=True,
            material_readiness=False,
        )
        assert result["passed"] is False

    def test_degradation_bifurcation(self):
        from src.backend.gates.gate_p8 import GateP8

        gate = GateP8()
        result = gate.check_v317(
            renders_complete=True,
            material_readiness=True,
            degraded_shots=1,
            reviewer_passed=True,
        )
        assert "passed" in result
