"""Tests for [SPEC-D-009] Phase P11: FinalCut Producer, FinalReviewer, Gate."""


class TestAC1FinalCutAdjustments:
    def test_final_cut_agent_adjustments(self):
        from src.backend.agents.final_cut_agent import FinalCutAgent

        agent = FinalCutAgent()
        result = agent.adjust(
            project_id="test_project",
            rough_cut_path="phase_10/rough_cut.mp4",
            adjustments={"volume_db": -2, "trim_start_seconds": 0.5},
        )
        assert "output_path" in result


class TestAC2CoverGeneration:
    def test_cover_generator_output(self):
        from src.backend.services.cover_generator import CoverGenerator

        gen = CoverGenerator()
        result = gen.generate_covers(title="Test Video", template="dark")
        assert isinstance(result, list)
        assert len(result) >= 1
        for cover in result:
            assert "path" in cover
            assert "size" in cover


class TestAC3PlatformAdaptation:
    def test_platform_profiles(self):
        from src.backend.services.platform_profiles import PlatformProfiles

        pp = PlatformProfiles()
        profile = pp.get_profile("web")
        assert "resolution" in profile
        assert "codec" in profile


class TestAC4BrandKitOverlay:
    def test_brand_kit_overlay(self):
        from src.backend.services.brand_kit_overlay import BrandKitOverlay

        bk = BrandKitOverlay()
        result = bk.apply(
            video_path="phase_11/final_cut.mp4",
            brand_kit={"logo_path": "brand/logo.png", "watermark": "Brand Name"},
        )
        assert "output_path" in result


class TestAC5FinalReviewer:
    def test_final_reviewer_l1(self):
        from src.backend.agents.final_reviewer import FinalReviewer

        reviewer = FinalReviewer()
        result = reviewer.review(
            {
                "resolution": "1920x1080",
                "has_audio": True,
                "has_subtitles": True,
                "duration_seconds": 120,
            }
        )
        assert "verdict" in result
        assert "checks" in result

    def test_final_reviewer_missing_audio_fail(self):
        from src.backend.agents.final_reviewer import FinalReviewer

        reviewer = FinalReviewer()
        result = reviewer.review(
            {
                "resolution": "1920x1080",
                "has_audio": False,
                "has_subtitles": True,
                "duration_seconds": 120,
            }
        )
        assert result["verdict"] == "FAIL"


class TestAC6CrossPhaseAudit3:
    def test_audit_3_summary(self):
        from src.backend.agents.final_cut_agent import FinalCutAgent

        agent = FinalCutAgent()
        result = agent.run_audit_3(
            audit_1={"inconsistency_count": 0},
            audit_2={"inconsistency_count": 0},
        )
        assert result["verdict"] == "PASS"

    def test_audit_3_with_prior_failures(self):
        from src.backend.agents.final_cut_agent import FinalCutAgent

        agent = FinalCutAgent()
        result = agent.run_audit_3(
            audit_1={"inconsistency_count": 2},
            audit_2={"inconsistency_count": 0},
        )
        assert result["verdict"] == "FAIL"


class TestAC7GateP11:
    def test_gate_p11_pass(self):
        from src.backend.gates.gate_p11 import GateP11

        gate = GateP11()
        result = gate.check(
            final_cut_exists=True,
            reviewer_passed=True,
            audit_clean=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True
        assert result.get("project_completed") is True

    def test_gate_p11_fail(self):
        from src.backend.gates.gate_p11 import GateP11

        gate = GateP11()
        result = gate.check(
            final_cut_exists=True,
            reviewer_passed=False,
            audit_clean=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False
