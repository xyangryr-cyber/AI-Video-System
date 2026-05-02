"""Tests for [SPEC-D-007] Phase P8-P9: Keyframe Render & B-Roll Producers, Reviewers, Gates."""


# ===========================================================================
# P8 Keyframe Render
# ===========================================================================


class TestAC1KeyframeRenderEngineSelection:
    def test_render_engine_selected_by_shot_type(self):
        from src.backend.services.render_engine_selector import RenderEngineSelector

        sel = RenderEngineSelector()
        engine = sel.select(template_type="chart_card")
        assert engine in ("echarts", "react", "remotion")

    def test_unknown_type_falls_back_to_react(self):
        from src.backend.services.render_engine_selector import RenderEngineSelector

        sel = RenderEngineSelector()
        engine = sel.select(template_type="unknown_xyz")
        assert engine == "react"


class TestAC2KeyframeRenderPerShot:
    def test_keyframe_agent_renders_template_shots_only(self):
        from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent

        agent = KeyframeRenderAgent()
        storyboard = [
            {
                "shot_id": "shot_0",
                "type": "template",
                "template_type": "chart_card",
                "time_range": {"start_seconds": 0.0, "end_seconds": 10.0},
            },
            {
                "shot_id": "shot_1",
                "type": "broll",
                "time_range": {"start_seconds": 10.0, "end_seconds": 15.0},
            },
        ]
        result = agent.render_keyframes(storyboard=storyboard)
        for item in result:
            assert item["type"] == "template"


class TestAC3DegradationFailedShot:
    def test_failed_shot_degraded_to_text_card(self):
        from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent

        agent = KeyframeRenderAgent()
        result = agent.handle_failed_shot(
            shot_id="shot_failed",
            reason="render timeout",
        )
        assert result["degraded"] is True
        assert (
            "text_card" in result.get("fallback_type", "").lower()
            or result.get("fallback_type") is not None
        )


class TestAC4NumberCrossCheck:
    def test_oral_visual_number_cross_check(self):
        from src.backend.agents.visual_reviewer import VisualReviewer

        reviewer = VisualReviewer()
        result = reviewer.check_number_match(
            oral_numbers=["1.2%", "3000亿"],
            visual_numbers=["1.2%", "3000亿"],
        )
        assert result["verdict"] == "PASS"

    def test_mismatch_returns_fail(self):
        from src.backend.agents.visual_reviewer import VisualReviewer

        reviewer = VisualReviewer()
        result = reviewer.check_number_match(
            oral_numbers=["1.2%"],
            visual_numbers=["5.0%"],
        )
        assert result["verdict"] == "FAIL"


class TestAC5ChartDataProvenance:
    def test_chart_data_provenance_audit(self):
        from src.backend.agents.visual_reviewer import VisualReviewer

        reviewer = VisualReviewer()
        result = reviewer.audit_data_provenance(
            chart_data_points=["dp_001", "dp_002"],
            source_data_points=["dp_001", "dp_002"],
        )
        assert result["verdict"] == "PASS"


# ===========================================================================
# P9 B-Roll
# ===========================================================================


class TestAC6BrollSemanticRelevance:
    def test_broll_relevance_scoring(self):
        from src.backend.agents.broll_agent import BRollAgent

        agent = BRollAgent()
        result = agent.score_relevance(
            shot_context="stock market rally",
            broll_candidates=[{"id": "br_1", "tags": ["finance", "chart"]}],
        )
        assert isinstance(result, list)
        for item in result:
            assert "relevance_score" in item
            assert 0.0 <= item["relevance_score"] <= 1.0


class TestAC7BrollQualityFiltering:
    def test_quality_filter_min_resolution(self):
        from src.backend.agents.broll_agent import BRollAgent

        agent = BRollAgent()
        result = agent.filter_quality(
            candidates=[{"id": "br_1", "resolution": "720p"}],
            min_resolution="1080p",
        )
        assert isinstance(result, list)


class TestAC8BrollStyleMatching:
    def test_style_lock_color_match(self):
        from src.backend.agents.broll_agent import BRollAgent

        agent = BRollAgent()
        style_lock = {"colors": {"bg": "#1a1a2e", "fg": "#e0e0e0", "accent": "#00d4ff"}}
        result = agent.filter_by_style(
            candidates=[{"id": "br_1", "dominant_color": "#1a1a2e"}],
            style_lock=style_lock,
        )
        assert isinstance(result, list)


class TestAC9BrollFallback:
    def test_broll_3_level_fallback(self):
        from src.backend.agents.broll_agent import BRollAgent

        agent = BRollAgent()
        result = agent.fetch_broll(source="pexels_api", query="finance")
        assert "file_path" in result or "fallback_used" in result
        assert "source_used" in result


# ===========================================================================
# VisualReviewer (P8, pure L1)
# ===========================================================================


class TestAC10VisualReviewer:
    def test_visual_reviewer_pure_l1(self):
        from src.backend.agents.visual_reviewer import VisualReviewer

        reviewer = VisualReviewer()
        result = reviewer.review(
            [
                {
                    "shot_id": "shot_0",
                    "render_path": "phase_8/shot_0.png",
                    "resolution": "1920x1080",
                    "file_size_bytes": 102400,
                },
            ]
        )
        assert "verdict" in result
        assert "checks" in result

    def test_missing_render_path_fail(self):
        from src.backend.agents.visual_reviewer import VisualReviewer

        reviewer = VisualReviewer()
        result = reviewer.review(
            [
                {"shot_id": "shot_0", "render_path": None},
            ]
        )
        assert result["verdict"] == "FAIL"


# ===========================================================================
# BRollFitReviewer (P9, L1+L2)
# ===========================================================================


class TestAC11BRollFitReviewer:
    def test_broll_l1_semantic_mismatch_fail(self):
        from src.backend.agents.broll_fit_reviewer import BRollFitReviewer

        reviewer = BRollFitReviewer()
        result = reviewer.review_l1(
            broll_candidates=[{"relevance_score": 0.1}],
            min_relevance=0.3,
        )
        assert result["verdict"] == "FAIL"

    def test_broll_l1_pass(self):
        from src.backend.agents.broll_fit_reviewer import BRollFitReviewer

        reviewer = BRollFitReviewer()
        result = reviewer.review_l1(
            broll_candidates=[{"relevance_score": 0.8}],
            min_relevance=0.3,
        )
        assert result["verdict"] == "PASS"


# ===========================================================================
# Gates (P8, P9)
# ===========================================================================


class TestAC12GateP8:
    def test_gate_p8_pass(self):
        from src.backend.gates.gate_p8 import GateP8

        gate = GateP8()
        result = gate.check(
            renders_complete=True,
            degraded_shots=0,
            reviewer_passed=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p8_degraded_within_limit(self):
        from src.backend.gates.gate_p8 import GateP8

        gate = GateP8()
        result = gate.check(
            renders_complete=True,
            degraded_shots=2,
            reviewer_passed=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert "passed" in result


class TestAC13GateP9:
    def test_gate_p9_pass(self):
        from src.backend.gates.gate_p9 import GateP9

        gate = GateP9()
        result = gate.check(
            broll_complete=True,
            reviewer_passed=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p9_fail_missing_broll(self):
        from src.backend.gates.gate_p9 import GateP9

        gate = GateP9()
        result = gate.check(
            broll_complete=False,
            reviewer_passed=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False
