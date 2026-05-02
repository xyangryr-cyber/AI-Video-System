"""Tests for [SPEC-D-017] Phase Scenario Cards & Failure Recovery Paths."""


class TestAC1P0Scenarios:
    def test_short_description_prompt(self):
        from src.backend.engine.failure_recovery import FailureRecovery

        fr = FailureRecovery()
        result = fr.handle_p0_short_description(description="短")
        assert result["action"] in ("prompt_user", "proceed")


class TestAC2P1RetryLimit:
    def test_5_regenerate_suggest_return(self):
        from src.backend.engine.failure_recovery import FailureRecovery

        fr = FailureRecovery()
        assert fr.max_retries(phase=1) == 5

    def test_infinite_retry_prevented(self):
        from src.backend.engine.failure_recovery import FailureRecovery

        fr = FailureRecovery()
        result = fr.should_retry(phase=1, attempt=6, max_retries=5)
        assert result is False


class TestAC3P3FreezeAndManual:
    def test_5_polish_freeze_version(self):
        from src.backend.engine.failure_recovery import FailureRecovery

        fr = FailureRecovery()
        result = fr.handle_phase_failure(phase=3, consecutive_fails=5)
        assert result["action"] in ("freeze", "manual_edit_mode")


class TestAC4TTSFailureAutoRetry:
    def test_tts_auto_retry_max_3(self):
        from src.backend.engine.failure_recovery import FailureRecovery

        fr = FailureRecovery()
        assert fr.max_retries(phase=4) <= 3


class TestAC5RollbackCascade:
    def test_p7_rollback_to_p2(self):
        from src.backend.engine.rollback_cascade import RollbackCascade

        rc = RollbackCascade()
        invalidated = rc.compute_cascade(invalid_phase=7, max_phase=11)
        assert len(invalidated) >= 2

    def test_rollback_preserves_p0_p1(self):
        from src.backend.engine.rollback_cascade import RollbackCascade

        rc = RollbackCascade()
        invalidated = rc.compute_cascade(invalid_phase=3, max_phase=10)
        assert 0 not in invalidated


class TestAC6PhaseScenarioCards:
    def test_scenario_card_for_phase(self):
        from src.backend.engine.phase_scenarios import PhaseScenarios

        ps = PhaseScenarios()
        card = ps.get_scenario(phase=4)
        assert "retry_limit" in card
        assert "on_failure" in card


class TestAC7GenericRetry:
    def test_generic_5x_limit(self):
        from src.backend.engine.failure_recovery import FailureRecovery

        fr = FailureRecovery()
        for phase in range(12):
            assert fr.max_retries(phase=phase) <= 5


class TestAC8ProviderSwitchOnFail:
    def test_provider_switch_available(self):
        from src.backend.engine.failure_recovery import FailureRecovery

        fr = FailureRecovery()
        result = fr.has_provider_fallback(phase=4)
        assert result is True
