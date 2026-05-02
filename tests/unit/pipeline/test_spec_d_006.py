"""Tests for [SPEC-D-006] Phase P7: Storyboard Producer, Reviewer, Gate."""


def _make_timeline():
    return {
        "segments": [
            {
                "segment_id": "seg_001",
                "start_sec": 0.0,
                "end_sec": 10.0,
                "content": "opening",
                "emotion_tone": "excited",
            },
            {
                "segment_id": "seg_002",
                "start_sec": 10.0,
                "end_sec": 25.0,
                "content": "middle",
                "emotion_tone": "neutral",
            },
            {
                "segment_id": "seg_003",
                "start_sec": 25.0,
                "end_sec": 40.0,
                "content": "closing",
                "emotion_tone": "calm",
            },
        ],
        "total_duration_sec": 40.0,
    }


def _make_script():
    return [
        {
            "segment_id": "seg_001",
            "key_data_points": [{"data_point_id": "dp_001", "value": "x"}],
        },
        {
            "segment_id": "seg_002",
            "key_data_points": [{"data_point_id": "dp_002", "value": "y"}],
        },
        {
            "segment_id": "seg_003",
            "key_data_points": [{"data_point_id": "dp_003", "value": "z"}],
        },
    ]


# AC-1: Shot fields
class TestAC1StoryboardAgentShotFields:
    def test_shot_has_all_fields(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        result = agent.produce_storyboard(
            timeline=_make_timeline(), script=_make_script()
        )
        assert isinstance(result, list)
        for shot in result:
            assert "shot_id" in shot
            assert "time_range" in shot
            assert shot["type"] in ("template", "broll")
            assert "narration_text" in shot
            assert "data_point_refs" in shot


# AC-2: Data viz coverage >= 80%
class TestAC2DataVisualizationCoverage:
    def test_data_visualization_coverage_80_percent(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        coverage = agent.check_data_coverage(
            shots=agent.produce_storyboard(
                timeline=_make_timeline(), script=_make_script()
            ),
            key_data_points=[{"data_point_id": "dp_001"}, {"data_point_id": "dp_002"}],
        )
        assert coverage["coverage_ratio"] >= 0.8

    def test_each_data_point_has_visual(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        shots = agent.produce_storyboard(
            timeline=_make_timeline(), script=_make_script()
        )
        coverage = agent.check_data_coverage(
            shots=shots,
            key_data_points=[{"data_point_id": "dp_001"}],
        )
        assert coverage["coverage_ratio"] >= 0.8


# AC-3: Style lock flow
class TestAC3StyleLockFlow:
    def test_style_lock_3_candidates(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        candidates = agent.generate_style_candidates(count=3)
        assert len(candidates) == 3
        for c in candidates:
            assert "scheme_id" in c
            assert "colors" in c

    def test_style_lock_user_confirm_writes_json(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        result = agent.confirm_style_lock(scheme_id="scheme_001")
        assert result["style_lock_path"] is not None
        assert result["confirmed"] is True


# AC-4: Shot timing constraints
class TestAC4ShotTimingConstraints:
    def test_shot_duration_in_range(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        shots = agent.produce_storyboard(
            timeline=_make_timeline(), script=_make_script()
        )
        for shot in shots:
            dur = (
                shot["time_range"]["end_seconds"] - shot["time_range"]["start_seconds"]
            )
            assert 3.0 <= dur <= 30.0, (
                f"shot {shot['shot_id']} duration {dur}s out of range"
            )

    def test_consecutive_same_type_max_2(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        result = agent.check_consecutive_same_type(
            [
                {"type": "template"},
                {"type": "template"},
                {"type": "template"},
            ]
        )
        assert result["verdict"] == "FAIL"

    def test_shots_continuous_no_gaps(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        shots = agent.produce_storyboard(
            timeline=_make_timeline(), script=_make_script()
        )
        # Check no gaps between consecutive shots
        for i in range(len(shots) - 1):
            end = shots[i]["time_range"]["end_seconds"]
            start = shots[i + 1]["time_range"]["start_seconds"]
            assert abs(end - start) < 0.01, f"gap between shot {i} and {i + 1}"

    def test_scene_switch_every_30s(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        result = agent.check_scene_switch(
            shots=agent.produce_storyboard(
                timeline=_make_timeline(), script=_make_script()
            ),
            window_seconds=30.0,
        )
        assert result["verdict"] == "PASS"


# AC-5: Narration text alignment
class TestAC5NarrationTextAlignment:
    def test_narration_text_timeline_alignment(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        shots = agent.produce_storyboard(
            timeline=_make_timeline(), script=_make_script()
        )
        for shot in shots:
            assert "narration_text" in shot
            assert isinstance(shot["narration_text"], str)
            assert len(shot["narration_text"]) > 0


# AC-6: Cross-phase audit #1
class TestAC6CrossPhaseAudit1:
    def test_audit_1_data_point_ids_valid(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.audit_data_points(
            shots=[{"data_point_refs": ["dp_001"]}],
            script_data_points=[{"data_point_id": "dp_001"}],
        )
        assert result["verdict"] == "PASS"

    def test_audit_1_time_alignment(self):
        from src.backend.engine.cross_phase_audit import CrossPhaseAudit

        auditor = CrossPhaseAudit()
        result = auditor.audit_time_alignment(
            shots=[{"time_range": {"start_seconds": 0.0, "end_seconds": 10.0}}],
            timeline_segments=[{"start_sec": 0.0, "end_sec": 10.0}],
        )
        assert result["verdict"] == "PASS"

    def test_audit_1_inconsistency_zero(self):
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


# AC-7: StoryboardReviewer L1 + L2
class TestAC7StoryboardReviewerL1L2:
    def test_l1_time_gap_fail(self):
        from src.backend.agents.storyboard_reviewer import StoryboardReviewer

        reviewer = StoryboardReviewer()
        result = reviewer.review_l1(
            [
                {"time_range": {"start_seconds": 0.0, "end_seconds": 10.0}},
                {"time_range": {"start_seconds": 15.0, "end_seconds": 25.0}},
            ]
        )
        assert result["verdict"] == "FAIL"

    def test_l1_3_consecutive_same_type_fail(self):
        from src.backend.agents.storyboard_reviewer import StoryboardReviewer

        reviewer = StoryboardReviewer()
        result = reviewer.review_l1(
            [
                {
                    "time_range": {"start_seconds": 0.0, "end_seconds": 10.0},
                    "type": "template",
                },
                {
                    "time_range": {"start_seconds": 10.0, "end_seconds": 20.0},
                    "type": "template",
                },
                {
                    "time_range": {"start_seconds": 20.0, "end_seconds": 30.0},
                    "type": "template",
                },
            ]
        )
        assert result["verdict"] == "FAIL"

    def test_l1_shot_duration_2s_fail(self):
        from src.backend.agents.storyboard_reviewer import StoryboardReviewer

        reviewer = StoryboardReviewer()
        result = reviewer.review_l1(
            [
                {
                    "time_range": {"start_seconds": 0.0, "end_seconds": 2.0},
                    "type": "template",
                },
            ]
        )
        assert result["verdict"] == "FAIL"

    def test_l1_uncovered_data_point_fail(self):
        from src.backend.agents.storyboard_reviewer import StoryboardReviewer

        reviewer = StoryboardReviewer()
        result = reviewer.review_l1(
            [
                {
                    "time_range": {"start_seconds": 0.0, "end_seconds": 10.0},
                    "type": "template",
                    "data_point_refs": [],
                }
            ],
            key_data_points=[{"data_point_id": "dp_missing"}],
        )
        assert result["verdict"] == "FAIL"

    def test_l1_pass_triggers_l2(self):
        from src.backend.agents.storyboard_reviewer import StoryboardReviewer

        reviewer = StoryboardReviewer()
        l1 = reviewer.review_l1(
            [
                {
                    "time_range": {"start_seconds": 0.0, "end_seconds": 10.0},
                    "type": "template",
                    "data_point_refs": ["dp_001"],
                },
                {
                    "time_range": {"start_seconds": 10.0, "end_seconds": 25.0},
                    "type": "broll",
                    "data_point_refs": ["dp_002"],
                },
            ]
        )
        assert l1["verdict"] == "PASS"

    def test_l1_fail_skips_l2_zero_tokens(self):
        from src.backend.agents.storyboard_reviewer import StoryboardReviewer

        reviewer = StoryboardReviewer()
        full = reviewer.review(
            [
                {
                    "time_range": {"start_seconds": 0.0, "end_seconds": 1.0},
                    "type": "template",
                },
            ]
        )
        assert full["l2_called"] is False


# AC-8: Gate-P7
class TestAC8GateP7:
    def test_gate_p7_pass(self):
        from src.backend.gates.gate_p7 import GateP7

        gate = GateP7()
        result = gate.check(
            storyboard_complete=True,
            style_lock_exists=True,
            reviewer_passed=True,
            audit_inconsistency=0,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p7_fail_no_style_lock(self):
        from src.backend.gates.gate_p7 import GateP7

        gate = GateP7()
        result = gate.check(
            storyboard_complete=True,
            style_lock_exists=False,
            reviewer_passed=True,
            audit_inconsistency=0,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False

    def test_gate_p7_fail_audit_inconsistency(self):
        from src.backend.gates.gate_p7 import GateP7

        gate = GateP7()
        result = gate.check(
            storyboard_complete=True,
            style_lock_exists=True,
            reviewer_passed=True,
            audit_inconsistency=3,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False


# AC-9: Visual preferences
class TestAC9VisualPreferences:
    def test_candidates_match_visual_preferences(self):
        from src.backend.agents.storyboard_agent import StoryboardAgent

        agent = StoryboardAgent()
        candidates = agent.generate_style_candidates(
            count=3,
            visual_preferences={"preferred_palette": "dark"},
        )
        assert len(candidates) == 3
        # Candidates should reflect dark palette preference
        assert any("dark" in c.get("scheme_id", "").lower() for c in candidates)
