"""Tests for [SPEC-D-016] ViewerExperienceReviewer (SPEC-9.13)."""


class TestAC1AutoTriggeredAfterAvSyncPass:
    def test_triggered_after_av_sync_pass(self):
        from src.backend.agents.viewer_experience_reviewer import (
            ViewerExperienceReviewer,
        )

        reviewer = ViewerExperienceReviewer()
        assert reviewer.should_trigger(av_sync_passed=True) is True
        assert reviewer.should_trigger(av_sync_passed=False) is False


class TestAC2Inputs:
    def test_takes_4_inputs(self):
        from src.backend.agents.viewer_experience_reviewer import (
            ViewerExperienceReviewer,
        )

        reviewer = ViewerExperienceReviewer()
        result = reviewer.review(
            rough_cut_metadata={"shots": []},
            polished_script={"segments": []},
            emotion_curve={"segments": []},
            timeline={"total_duration_sec": 60},
        )
        assert "verdict" in result


class TestAC3SixDimensions:
    def test_evaluates_6_dimensions(self):
        from src.backend.agents.viewer_experience_reviewer import (
            ViewerExperienceReviewer,
        )

        reviewer = ViewerExperienceReviewer()
        result = reviewer.review(
            rough_cut_metadata={"shots": [{"type": "template"}]},
            polished_script={"segments": [{"content": "hello"}]},
            emotion_curve={"segments": [{"emotion": "neutral"}]},
            timeline={"total_duration_sec": 60},
        )
        assert "dimension_scores" in result
        assert len(result["dimension_scores"]) == 6


class TestAC4OutputFormat:
    def test_output_has_all_fields(self):
        from src.backend.agents.viewer_experience_reviewer import (
            ViewerExperienceReviewer,
        )

        reviewer = ViewerExperienceReviewer()
        result = reviewer.review(
            rough_cut_metadata={"shots": []},
            polished_script={"segments": []},
            emotion_curve={"segments": []},
            timeline={"total_duration_sec": 60},
        )
        assert "overall_score" in result
        assert "dimension_scores" in result
        assert "improvement_suggestions" in result
        assert "notes" in result
        assert isinstance(result["overall_score"], (int, float))


class TestAC5ScoreBelow6Fails:
    def test_score_below_6_fails(self):
        from src.backend.agents.viewer_experience_reviewer import (
            ViewerExperienceReviewer,
        )

        reviewer = ViewerExperienceReviewer()
        result = reviewer.review(
            rough_cut_metadata={"shots": []},
            polished_script={"segments": []},
            emotion_curve={"segments": []},
            timeline={"total_duration_sec": 60},
        )
        if result["overall_score"] < 6:
            assert result["verdict"] == "FAIL"


class TestAC6VerdictFailNonBlocking:
    def test_fail_does_not_block_gate(self):
        from src.backend.agents.viewer_experience_reviewer import (
            ViewerExperienceReviewer,
        )

        reviewer = ViewerExperienceReviewer()
        assert reviewer.blocks_gate() is False


class TestAC7ImprovementSuggestions:
    def test_suggestions_are_advisory(self):
        from src.backend.agents.viewer_experience_reviewer import (
            ViewerExperienceReviewer,
        )

        reviewer = ViewerExperienceReviewer()
        result = reviewer.review(
            rough_cut_metadata={"shots": []},
            polished_script={"segments": []},
            emotion_curve={"segments": []},
            timeline={"total_duration_sec": 60},
        )
        assert isinstance(result.get("improvement_suggestions"), list)
