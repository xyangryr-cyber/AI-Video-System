"""Tests for [SPEC-D-002] Phase P0-P1: Requirements & Outline Producers, Reviewers, Gates."""

import pytest


REQUIRED_FIELDS = (
    "project_id",
    "title",
    "topic",
    "duration_class",
    "target_duration_seconds",
    "target_word_count",
    "platform",
    "category",
    "narrative_template",
    "voice_preferences",
    "target_platform",
    "subtitle_preferences",
)


class TestAC1RequirementsAgentOutputFields:
    """AC-1: RequirementsAgent outputs all SPEC-9.0.1 fields."""

    def test_output_has_all_required_fields(self):
        from src.backend.agents.requirements_agent import RequirementsAgent

        agent = RequirementsAgent()
        result = agent.produce(
            project_id="proj_test",
            title="Test Video",
            topic="AI in Finance",
            duration_class="medium",
            platform="web",
            category_level1="finance",
            category_level2="stock_market",
            narrative_template="chronological",
            target_duration_seconds=600,
            target_word_count_min=1700,
            target_word_count_max=1900,
        )
        for field in REQUIRED_FIELDS:
            assert field in result, f"Missing field '{field}' in output"
        assert result["project_id"] == "proj_test"
        assert result["duration_class"] == "medium"


class TestAC2WordCountDurationConsistency:
    """AC-2: target_word_count and target_duration x speech_rate_baseline error <= 10%"""

    def test_word_count_duration_consistency(self):
        from src.backend.agents.requirements_agent import RequirementsAgent

        agent = RequirementsAgent()
        result = agent.produce(
            project_id="p",
            title="t",
            topic="AI",
            duration_class="short",
            platform="web",
            category_level1="tech",
            category_level2="ai_ml",
            narrative_template="chronological",
            target_duration_seconds=600,
            target_word_count_min=1600,
            target_word_count_max=2000,
        )
        # speech_rate_baseline = 3 chars/sec (Chinese)
        # 600s * 3 chars/s = 1800 chars expected center
        # target: 1600-2000 -> center 1800, error = 0% -> within 10%
        assert result["target_word_count"]["min"] == 1600
        assert result["target_word_count"]["max"] == 2000

    def test_word_count_duration_inconsistency_raises(self):
        from src.backend.agents.requirements_agent import RequirementsAgent

        agent = RequirementsAgent()
        # 60s * 3 chars/s = 180 chars, but asking for 5000-8000 words
        # error = (8000-180)/180 >> 10%
        with pytest.raises(ValueError, match="word_count"):
            agent.produce(
                project_id="p",
                title="t",
                topic="AI",
                duration_class="short",
                platform="web",
                category_level1="tech",
                category_level2="ai_ml",
                narrative_template="chronological",
                target_duration_seconds=60,
                target_word_count_min=5000,
                target_word_count_max=8000,
            )


class TestAC3CompletenessReviewerFailConditions:
    """AC-3: CompletenessReviewer enforces all 7 FAIL conditions."""

    def test_topic_too_short_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["topic"] = "ab"
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"

    def test_invalid_duration_class_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["duration_class"] = "epic"
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"

    def test_word_count_max_exceeds_limit_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["target_word_count"]["max"] = 200000
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"

    def test_no_valid_platform_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["platform"] = ""
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"

    def test_empty_resolution_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["resolution"] = ""
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"

    def test_invalid_category_level1_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["category"]["level1"] = "invalid_cat"
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"

    def test_invalid_narrative_template_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["narrative_template"] = "bad_template"
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"


def _valid_requirements():
    return {
        "project_id": "proj_1",
        "title": "Test Video Title",
        "topic": "AI in Financial Markets",
        "duration_class": "medium",
        "target_duration_seconds": 600,
        "target_word_count": {"min": 800, "max": 1200},
        "platform": "web",
        "category": {"level1": "finance", "level2": "stock_market"},
        "narrative_template": "chronological",
        "resolution": "1920x1080",
        "bitrate": "5M",
        "format": "mp4",
        "voice_preferences": {},
        "target_platform": "web",
        "subtitle_preferences": {},
        "preferences_confirmed_at": "2026-04-01T00:00:00Z",
    }


class TestAC4CategoryLevel1Level2EnumMapping:
    """AC-4: CompletenessReviewer validates category.level1->level2 enum mapping."""

    def test_category_level2_mismatch_fails(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["category"] = {"level1": "finance", "level2": "ai_ml"}
        verdict = r.review(req)
        assert verdict["verdict"] == "FAIL"

    def test_valid_category_mapping_passes(self):
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        r = CompletenessReviewer()
        req = _valid_requirements()
        req["category"] = {"level1": "tech", "level2": "ai_ml"}
        verdict = r.review(req)
        assert verdict["verdict"] == "PASS"


class TestAC5GateP0Checks:
    """AC-5: Gate-P0 checks: requirements.json exists + schema valid, CompletenessReviewer PASS, preferences_confirmed_at non-null"""

    def test_gate_p0_pass(self):
        from src.backend.gates.gate_p0 import GateP0

        req = _valid_requirements()
        result = GateP0.check(req)
        assert result["passed"] is True

    def test_gate_p0_fail_missing_requirements(self):
        from src.backend.gates.gate_p0 import GateP0

        result = GateP0.check({})
        assert result["passed"] is False

    def test_gate_p0_fail_preferences_not_confirmed(self):
        from src.backend.gates.gate_p0 import GateP0

        req = _valid_requirements()
        req["preferences_confirmed_at"] = None
        result = GateP0.check(req)
        assert result["passed"] is False


BEAT_TYPES = ("hook", "context", "argument", "climax", "conclusion")


class TestAC6OutlineAgentVersionsAndBeats:
    """AC-6: OutlineAgent produces 2-3 versions with narrative beats."""

    def test_produces_2_to_3_versions(self):
        from src.backend.agents.outline_agent import OutlineAgent

        agent = OutlineAgent()
        result = agent.produce(
            requirements=_valid_requirements(),
            topic="AI in Finance",
            duration_seconds=600,
        )
        versions = result["versions"]
        assert 2 <= len(versions) <= 3

    def test_narrative_beats_non_overlapping(self):
        from src.backend.agents.outline_agent import OutlineAgent

        agent = OutlineAgent()
        result = agent.produce(
            requirements=_valid_requirements(),
            topic="AI in Finance",
            duration_seconds=600,
        )
        for v in result["versions"]:
            beats = v["narrative_beats"]
            assert len(beats) == 5
            beat_names = [b["type"] for b in beats]
            assert beat_names == list(BEAT_TYPES)
            # Non-overlapping time intervals
            for i in range(len(beats) - 1):
                assert beats[i]["end_seconds"] <= beats[i + 1]["start_seconds"]

    def test_supporting_data_per_viewpoint(self):
        from src.backend.agents.outline_agent import OutlineAgent

        agent = OutlineAgent()
        result = agent.produce(
            requirements=_valid_requirements(),
            topic="AI in Finance",
            duration_seconds=600,
        )
        for v in result["versions"]:
            for beat in v["narrative_beats"]:
                assert "supporting_data" in beat
                assert "viewpoint" in beat


class TestAC7StructureReviewerValidation:
    """AC-7: StructureReviewer validates structure, duration ratio, diversity."""

    def test_valid_structure_passes(self):
        from src.backend.agents.structure_reviewer import StructureReviewer

        r = StructureReviewer()
        outlines = _valid_outlines()
        verdict = r.review(outlines, selected_version_id="vA")
        assert verdict["verdict"] == "PASS"

    def test_duration_ratio_sum_out_of_range_fails(self):
        from src.backend.agents.structure_reviewer import StructureReviewer

        r = StructureReviewer()
        outlines = _valid_outlines()
        # Corrupt the duration ratio
        for b in outlines[0]["narrative_beats"]:
            b["end_seconds"] = b["start_seconds"] + 1
        verdict = r.review(outlines, selected_version_id="vA")
        assert verdict["verdict"] == "FAIL"

    def test_inter_version_diversity(self):
        from src.backend.agents.structure_reviewer import StructureReviewer

        r = StructureReviewer()
        outlines = _valid_outlines()
        verdict = r.review(outlines, selected_version_id="vA")
        # vA and vB with different viewpoints should pass diversity
        assert (
            "diversity" in str(verdict["notes"]).lower() or verdict["verdict"] == "PASS"
        )


class TestAC8GateP1Checks:
    """AC-8: Gate-P1 checks: selected outline + reviewer PASS."""

    def test_gate_p1_pass(self):
        from src.backend.gates.gate_p1 import GateP1

        outlines = _valid_outlines()
        result = GateP1.check(outlines, selected_version_id="vA")
        assert result["passed"] is True


class TestAC9GateP1FailCases:
    """AC-9: Gate-P1 FAIL when outline not selected or reviewer FAIL."""

    def test_gate_p1_fail_no_selection(self):
        from src.backend.gates.gate_p1 import GateP1

        outlines = _valid_outlines()
        result = GateP1.check(outlines, selected_version_id=None)
        assert result["passed"] is False

    def test_gate_p1_fail_reviewer_fail(self):
        from src.backend.gates.gate_p1 import GateP1

        outlines = _valid_outlines()
        # Corrupt the outline to fail review
        for b in outlines[0]["narrative_beats"]:
            b["transition_to_next"] = ""
        result = GateP1.check(outlines, selected_version_id="vA")
        assert result["passed"] is False


def _valid_outlines():
    return [
        {
            "version_id": "vA",
            "viewpoint": "chronological",
            "narrative_beats": [
                {
                    "type": "hook",
                    "title": "H",
                    "viewpoint": "vA",
                    "start_seconds": 0,
                    "end_seconds": 120,
                    "transition_to_next": "to context",
                    "supporting_data": ["d1"],
                    "key_points": ["k1"],
                },
                {
                    "type": "context",
                    "title": "C",
                    "viewpoint": "vA",
                    "start_seconds": 120,
                    "end_seconds": 240,
                    "transition_to_next": "to argument",
                    "supporting_data": ["d2"],
                    "key_points": ["k2"],
                },
                {
                    "type": "argument",
                    "title": "A1",
                    "viewpoint": "vA",
                    "start_seconds": 240,
                    "end_seconds": 360,
                    "transition_to_next": "to argument 2",
                    "supporting_data": ["d3"],
                    "key_points": ["k3"],
                },
                {
                    "type": "climax",
                    "title": "Cl",
                    "viewpoint": "vA",
                    "start_seconds": 360,
                    "end_seconds": 480,
                    "transition_to_next": "to conclusion",
                    "supporting_data": ["d4"],
                    "key_points": ["k4"],
                },
                {
                    "type": "conclusion",
                    "title": "Co",
                    "viewpoint": "vA",
                    "start_seconds": 480,
                    "end_seconds": 600,
                    "transition_to_next": "",
                    "supporting_data": ["d5"],
                    "key_points": ["k5"],
                },
            ],
        },
        {
            "version_id": "vB",
            "viewpoint": "progressive",
            "narrative_beats": [
                {
                    "type": "hook",
                    "title": "H",
                    "viewpoint": "vB",
                    "start_seconds": 0,
                    "end_seconds": 150,
                    "transition_to_next": "to context",
                    "supporting_data": ["x1"],
                    "key_points": ["y1"],
                },
                {
                    "type": "context",
                    "title": "C",
                    "viewpoint": "vB",
                    "start_seconds": 150,
                    "end_seconds": 270,
                    "transition_to_next": "to argument",
                    "supporting_data": ["x2"],
                    "key_points": ["y2"],
                },
                {
                    "type": "argument",
                    "title": "A2",
                    "viewpoint": "vB",
                    "start_seconds": 270,
                    "end_seconds": 390,
                    "transition_to_next": "to climax",
                    "supporting_data": ["x3"],
                    "key_points": ["y3"],
                },
                {
                    "type": "climax",
                    "title": "Cl",
                    "viewpoint": "vB",
                    "start_seconds": 390,
                    "end_seconds": 510,
                    "transition_to_next": "to conclusion",
                    "supporting_data": ["x4"],
                    "key_points": ["y4"],
                },
                {
                    "type": "conclusion",
                    "title": "Co",
                    "viewpoint": "vB",
                    "start_seconds": 510,
                    "end_seconds": 600,
                    "transition_to_next": "",
                    "supporting_data": ["x5"],
                    "key_points": ["y5"],
                },
            ],
        },
    ]
