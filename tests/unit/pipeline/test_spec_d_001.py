"""Tests for [SPEC-D-001] Artifact Authority Map & Reviewer/Gate Verdict Binding."""

import pytest

REQUIRED_ARTIFACTS = (
    "requirements.json",
    "outline",
    "polished_script",
    "timeline.json",
    "style_lock.json",
    "keyframe_renders",
    "rough_cut",
    "final_cut",
    "emotion_curve.json",
)


class TestAC1RegistryCoversAllNineArtifacts:
    """AC-1: Artifact authority registry covers all 9 artifacts."""

    def test_registry_covers_all_9_artifacts(self):
        from src.backend.engine.artifact_authority import ARTIFACT_AUTHORITY

        assert len(ARTIFACT_AUTHORITY) == 9, (
            f"Expected 9 artifacts, got {len(ARTIFACT_AUTHORITY)}"
        )
        for name in REQUIRED_ARTIFACTS:
            assert name in ARTIFACT_AUTHORITY, (
                f"Missing artifact '{name}' in authority registry"
            )


REQUIRED_FIELDS = (
    "producer_phase",
    "producer_agent",
    "consumer_phases",
    "consumer_agents",
    "schema_ref",
    "acceptance_reviewer",
)


class TestAC2RegistryEntryHasAllFields:
    """AC-2: Each registry entry maps all 6 required fields."""

    def test_registry_entry_has_all_fields(self):
        from src.backend.engine.artifact_authority import ARTIFACT_AUTHORITY

        for name, entry in ARTIFACT_AUTHORITY.items():
            for field in REQUIRED_FIELDS:
                assert field in entry, (
                    f"Artifact '{name}' missing required field '{field}'"
                )
                value = entry[field]
                if isinstance(value, str):
                    assert value, f"Artifact '{name}' field '{field}' is empty string"
                elif isinstance(value, list):
                    pass  # empty lists are valid (e.g. final_cut has no consumers)
                elif isinstance(value, dict):
                    assert value, f"Artifact '{name}' field '{field}' is empty dict"


class TestAC3LookupByArtifactName:
    """AC-3: Lookup by artifact name returns correct authority record."""

    def test_lookup_by_artifact_name(self):
        from src.backend.engine.artifact_authority import lookup_artifact

        record = lookup_artifact("requirements.json")
        assert record["producer_phase"] == "P0"
        assert record["producer_agent"] == "RequirementsAgent"
        assert record["acceptance_reviewer"] == "CompletenessReviewer"

    def test_lookup_missing_artifact_raises_key_error(self):
        from src.backend.engine.artifact_authority import lookup_artifact

        with pytest.raises(KeyError):
            lookup_artifact("nonexistent.json")


class TestAC4ReviewerVerdictFormat:
    """AC-4: Reviewer verdict type enforces `{verdict: PASS|FAIL, notes: str[], blocking_issues: str[]}`"""

    def test_verdict_format_pass(self):
        from src.shared.types.verdict import Verdict

        v = Verdict(verdict="PASS", notes=["All checks ok"], blocking_issues=[])
        assert v.verdict == "PASS"
        assert v.notes == ["All checks ok"]
        assert v.blocking_issues == []

    def test_verdict_format_fail_with_blocking_issues(self):
        from src.shared.types.verdict import Verdict

        v = Verdict(
            verdict="FAIL",
            notes=["Audio quality low"],
            blocking_issues=["AudioQualityReviewer returned FAIL"],
        )
        assert v.verdict == "FAIL"
        assert len(v.blocking_issues) == 1

    def test_verdict_rejects_invalid_value(self):
        from pydantic import ValidationError
        from src.shared.types.verdict import Verdict

        with pytest.raises(ValidationError):
            Verdict(verdict="INVALID", notes=[], blocking_issues=[])

    def test_verdict_notes_defaults_to_empty_list(self):
        from src.shared.types.verdict import Verdict

        v = Verdict(verdict="PASS")  # notes and blocking_issues default to []
        assert v.notes == []
        assert v.blocking_issues == []

    def test_notes_items_must_be_strings(self):
        from pydantic import ValidationError
        from src.shared.types.verdict import Verdict

        with pytest.raises(ValidationError):
            Verdict(verdict="PASS", notes=[123], blocking_issues=[])


class TestAC5GateFailureResponseEvid2001:
    """AC-5: Gate failure response includes EVID_2001 with {failed_checks[], passed_checks[]}"""

    def test_gate_failure_response_evid_2001(self):
        from src.backend.engine.verdict_binding import build_gate_failure_response

        resp = build_gate_failure_response(
            failed_checks=["master_audio_ref missing"],
            passed_checks=["checksum_consistent", "concat_integrity"],
        )
        assert resp["error_code"] == "EVID_2001"
        assert "failed_checks" in resp
        assert "passed_checks" in resp
        assert "master_audio_ref missing" in resp["failed_checks"]
        assert "checksum_consistent" in resp["passed_checks"]

    def test_gate_failure_response_http_status_422(self):
        from src.backend.engine.verdict_binding import build_gate_failure_response

        resp = build_gate_failure_response(
            failed_checks=["check_1"],
            passed_checks=[],
        )
        assert resp["http_status"] == 422


class TestAC6ReviewStatusComputedFromTaskLedger:
    """AC-6: review_status computed from task_ledger as pure function (not DB field)."""

    def test_all_reviews_passed_returns_passed(self):
        from src.backend.engine.verdict_binding import compute_review_status

        ledger = [
            {"task_type": "review", "verdict": "PASS", "phase": "P0"},
            {"task_type": "review", "verdict": "PASS", "phase": "P1"},
        ]
        assert compute_review_status(ledger) == "passed"

    def test_any_review_failed_returns_failed(self):
        from src.backend.engine.verdict_binding import compute_review_status

        ledger = [
            {"task_type": "review", "verdict": "PASS", "phase": "P0"},
            {"task_type": "review", "verdict": "FAIL", "phase": "P1"},
        ]
        assert compute_review_status(ledger) == "failed"

    def test_empty_ledger_returns_pending(self):
        from src.backend.engine.verdict_binding import compute_review_status

        assert compute_review_status([]) == "pending"

    def test_no_review_tasks_returns_pending(self):
        from src.backend.engine.verdict_binding import compute_review_status

        ledger = [
            {"task_type": "producer", "phase": "P1"},
            {"task_type": "user_action", "phase": "P3"},
        ]
        assert compute_review_status(ledger) == "pending"

    def test_in_progress_review_returns_in_progress(self):
        from src.backend.engine.verdict_binding import compute_review_status

        ledger = [
            {"task_type": "review", "status": "running", "phase": "P0"},
        ]
        assert compute_review_status(ledger) == "in_progress"

    def test_pure_function_no_side_effects(self):
        from src.backend.engine.verdict_binding import compute_review_status

        ledger = [{"task_type": "review", "verdict": "PASS"}]
        before = [dict(e) for e in ledger]
        compute_review_status(ledger)
        assert ledger == before  # input unchanged
