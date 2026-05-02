"""Tests for [SPEC-D-012] Unified Gate Checking Framework."""


class TestAC1BaseGateAbstractClassAndGateResult:
    def test_gate_result_structure(self):
        from src.backend.gates.base_gate import GateResult

        result = GateResult(passed=True, failed_checks=[], passed_checks=["check1"])
        assert result.passed is True
        assert "check1" in result.passed_checks

    def test_gate_result_fail(self):
        from src.backend.gates.base_gate import GateResult

        result = GateResult(passed=False, failed_checks=["bad"], passed_checks=["ok"])
        assert result.passed is False


class TestAC2CheckRegistration:
    def test_register_checks(self):
        from src.backend.gates.base_gate import BaseGate

        class TestGate(BaseGate):
            def check_a(self):
                return True, "ok"

        gate = TestGate()
        gate.register_checks(["check_a"])
        assert len(gate._checks) == 1


class TestAC3SequentialExecution:
    def test_sequential_execution_with_aggregation(self):
        from src.backend.gates.base_gate import BaseGate

        class TestGate(BaseGate):
            def check_a(self):
                return True, "a ok"

            def check_b(self):
                return False, "b bad"

        gate = TestGate()
        gate.register_checks(["check_a", "check_b"])
        result = gate.run()
        assert result.passed is False
        assert "a ok" in result.passed_checks
        assert any("b bad" in f for f in result.failed_checks)


class TestAC4EVID2001OnFailure:
    def test_error_code_on_failure(self):
        from src.backend.gates.base_gate import BaseGate

        class FailingGate(BaseGate):
            def check_x(self):
                return False, "blocked"

        gate = FailingGate()
        gate.register_checks(["check_x"])
        result = gate.run()
        assert result.passed is False
        # Error response structure
        error = gate.error_response(result)
        assert "EVID_2001" in error.get("error_code", "")


class TestAC5SkipBranchHandling:
    def test_skip_branch_handling(self):
        from src.backend.gates.base_gate import BaseGate

        class SkippableGate(BaseGate):
            def check_a(self):
                return False, "would fail"

        gate = SkippableGate()
        gate.register_checks(["check_a"])
        # Skip mode: treat as always-pass
        skip_result = gate.run_skip()
        assert skip_result.passed is True


class TestAC6AsyncTaskCompletion:
    def test_async_task_check(self):
        from src.backend.gates.base_gate import BaseGate

        class AsyncGate(BaseGate):
            def check_async(self):
                return True, "done"

        gate = AsyncGate()
        assert gate.check_async_completion(async_tasks_complete=True) is True
        assert gate.check_async_completion(async_tasks_complete=False) is False


class TestAC7ArtifactStatusValidation:
    def test_artifact_status_check(self):
        from src.backend.gates.base_gate import BaseGate

        gate = BaseGate()
        assert gate.validate_artifact_status(status="complete") is True
        assert gate.validate_artifact_status(status="damaged") is False
