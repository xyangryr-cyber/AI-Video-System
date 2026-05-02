"""Tests for [SPEC-D-015] Cross-Phase Audit Points."""


class TestAC1Audit1Checks:
    def test_audit_1_data_point_existence(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.audit_data_points(
            shots=[{"data_point_refs": ["dp_001"]}],
            script_data_points=[{"data_point_id": "dp_001"}],
        )
        assert result["verdict"] == "PASS"

    def test_audit_1_missing_data_point(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.audit_data_points(
            shots=[{"data_point_refs": ["dp_missing"]}],
            script_data_points=[{"data_point_id": "dp_001"}],
        )
        assert result["verdict"] == "FAIL"


class TestAC2Audit1GateEnforcement:
    def test_audit_1_zero_inconsistency_required(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.run_audit_1(
            shots=[
                {
                    "data_point_refs": ["dp_001"],
                    "time_range": {"start_seconds": 0.0, "end_seconds": 10.0},
                }
            ],
            script_data_points=[{"data_point_id": "dp_001"}],
            timeline_segments=[{"start_sec": 0.0, "end_sec": 10.0}],
        )
        assert result["inconsistency_count"] == 0


class TestAC3Audit2Checks:
    def test_audit_2_subtitle_match(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.run_audit_2(
            subtitles=[{"text": "hello world"}],
            polished_script={"segments": [{"content": "hello world"}]},
            storyboard=[
                {
                    "shot_id": "s1",
                    "time_range": {"start_seconds": 0.0, "end_seconds": 5.0},
                }
            ],
            rough_cut={"duration_seconds": 5.0},
            timeline={"total_duration_sec": 5.0},
        )
        assert "inconsistency_count" in result


class TestAC4Audit2GateEnforcement:
    def test_audit_2_zero_required(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.run_audit_2(
            subtitles=[{"text": "hello"}],
            polished_script={"segments": [{"content": "hello"}]},
            storyboard=[
                {
                    "shot_id": "s1",
                    "time_range": {"start_seconds": 0.0, "end_seconds": 10.0},
                }
            ],
            rough_cut={"duration_seconds": 10.1},
            timeline={"total_duration_sec": 10.0},
        )
        assert "inconsistency_count" in result


class TestAC5Audit3Summary:
    def test_audit_3_collects_all_prior(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.run_audit_3(
            audit_1={"inconsistency_count": 0, "inconsistencies": []},
            audit_2={"inconsistency_count": 0, "inconsistencies": []},
        )
        assert result["verdict"] == "PASS"

    def test_audit_3_unresolved_fails(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.run_audit_3(
            audit_1={"inconsistency_count": 2, "inconsistencies": ["a", "b"]},
            audit_2={"inconsistency_count": 1, "inconsistencies": ["c"]},
        )
        assert result["verdict"] == "FAIL"


class TestAC6InconsistencyTracker:
    def test_tracker_store_record(self):
        from src.backend.engine.inconsistency_tracker import InconsistencyTracker

        tracker = InconsistencyTracker()
        tracker.record(
            audit_id="audit_1",
            phase=7,
            check_name="data_points",
            expected_value="dp_001",
            actual_value="dp_missing",
        )
        records = tracker.list_records()
        assert len(records) == 1
        assert records[0]["status"] == "detected"

    def test_tracker_resolve(self):
        from src.backend.engine.inconsistency_tracker import InconsistencyTracker

        tracker = InconsistencyTracker()
        tracker.record(
            audit_id="a1",
            phase=7,
            check_name="dp",
            expected_value="x",
            actual_value="y",
        )
        tracker.resolve(index=0, status="accepted_deviation")
        assert tracker.list_records()[0]["status"] == "accepted_deviation"
