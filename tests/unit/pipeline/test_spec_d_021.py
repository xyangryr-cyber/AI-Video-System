"""Tests for [SPEC-D-021] Gate-7A + FSM edges."""


class TestAC1Gate7AChecks:
    def test_gate_7a_material_check(self):
        from src.backend.gates.gate_7a import Gate7A

        gate = Gate7A()
        result = gate.check(
            hard_materials_verified=True,
            soft_materials_ready=True,
            advanced_to_p8=False,
        )
        assert "passed" in result

    def test_hard_material_unverified_blocks(self):
        from src.backend.gates.gate_7a import Gate7A

        gate = Gate7A()
        result = gate.check(
            hard_materials_verified=False,
        )
        assert result["passed"] is False

    def test_advanced_to_p8_flag(self):
        from src.backend.gates.gate_7a import Gate7A

        gate = Gate7A()
        result = gate.check(
            hard_materials_verified=True,
            advanced_to_p8=True,
        )
        assert result["passed"] is True


class TestAC2FSMEdges:
    def test_fsm_p8_to_7a_edge(self):
        from src.backend.gates.gate_7a import Gate7A

        gate = Gate7A()
        assert gate.can_reenter_7a(from_phase=8) is True

    def test_fsm_no_reenter_from_early(self):
        from src.backend.gates.gate_7a import Gate7A

        gate = Gate7A()
        assert gate.can_reenter_7a(from_phase=3) is False
