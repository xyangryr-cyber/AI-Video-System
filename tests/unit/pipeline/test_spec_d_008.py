"""Tests for [SPEC-D-008] Phase P10: RoughCut Producer, AVSyncReviewer, Gate."""


class TestAC1AudioMixing:
    def test_mix_narration_bgm_sfx(self):
        from src.backend.services.audio_mixer import AudioMixer

        mixer = AudioMixer()
        result = mixer.mix(
            narration_path="phase_4/narration.wav",
            bgm_path="phase_5/bgm.mp3",
            sfx_paths=["phase_6/sfx_001.wav"],
            bgm_volume_db=-18,
        )
        assert "output_path" in result
        assert "duration_seconds" in result


class TestAC2SubtitleGeneration:
    def test_subtitle_generator_output(self):
        from src.backend.services.subtitle_generator import SubtitleGenerator

        gen = SubtitleGenerator()
        result = gen.generate(
            audio_path="phase_4/seg_audio.mp3",
            text="今日股市开盘表现强劲",
        )
        assert "subtitles" in result
        for sub in result["subtitles"]:
            assert "start_sec" in sub
            assert "end_sec" in sub
            assert "text" in sub


class TestAC3KeywordHighlighting:
    def test_keyword_highlighted_in_subtitle(self):
        from src.backend.services.keyword_highlighter import KeywordHighlighter

        hl = KeywordHighlighter()
        result = hl.highlight(
            subtitles=[{"start_sec": 0.0, "end_sec": 1.0, "text": "沪指上涨1.2%"}],
            keywords=["1.2%", "沪指"],
        )
        for sub in result:
            assert "highlighted" in sub or "text" in sub


class TestAC4RoughCutComposition:
    def test_rough_cut_agent_composes(self):
        from src.backend.agents.rough_cut_agent import RoughCutAgent

        agent = RoughCutAgent()
        result = agent.compose(
            storyboard=[
                {
                    "shot_id": "shot_0",
                    "type": "template",
                    "time_range": {"start_seconds": 0.0, "end_seconds": 10.0},
                }
            ],
            timeline={
                "segments": [
                    {"segment_id": "seg_001", "start_sec": 0.0, "end_sec": 10.0}
                ]
            },
            keyframe_renders=[
                {"shot_id": "shot_0", "render_path": "phase_8/shot_0.png"}
            ],
        )
        assert "rough_cut_path" in result
        assert "duration_seconds" in result


class TestAC5TransitionEffects:
    def test_crossfade_intra_segment(self):
        from src.backend.agents.rough_cut_agent import RoughCutAgent

        agent = RoughCutAgent()
        result = agent.apply_transitions(
            [
                {"type": "crossfade", "duration_seconds": 0.5},
            ]
        )
        assert isinstance(result, list)


class TestAC6CrossPhaseAudit2:
    def test_audit_2_av_sync(self):
        from src.backend.agents.rough_cut_agent import RoughCutAgent

        agent = RoughCutAgent()
        result = agent.run_audit_2(
            rough_cut={"duration_seconds": 40.0},
            timeline={"total_duration_sec": 40.0},
        )
        assert "inconsistency_count" in result
        assert result["inconsistency_count"] == 0


class TestAC7PlatformEncoding:
    def test_encode_for_platform(self):
        from src.backend.agents.rough_cut_agent import RoughCutAgent

        agent = RoughCutAgent()
        result = agent.encode_for_platform(
            rough_cut_path="phase_10/rough_cut.mp4",
            platform="web",
        )
        assert "output_path" in result
        assert result.get("codec") in ("h264", "H.264")


class TestAC8AVSyncReviewer:
    def test_av_sync_reviewer_l1(self):
        from src.backend.agents.av_sync_reviewer import AVSyncReviewer

        reviewer = AVSyncReviewer()
        result = reviewer.review(
            rough_cut={"av_offset_ms": 50},
            max_offset_ms=100,
        )
        assert "verdict" in result

    def test_av_sync_exceeds_tolerance(self):
        from src.backend.agents.av_sync_reviewer import AVSyncReviewer

        reviewer = AVSyncReviewer()
        result = reviewer.review(
            rough_cut={"av_offset_ms": 200},
            max_offset_ms=100,
        )
        assert result["verdict"] == "FAIL"


class TestAC9GateP10:
    def test_gate_p10_pass(self):
        from src.backend.gates.gate_p10 import GateP10

        gate = GateP10()
        result = gate.check(
            rough_cut_exists=True,
            reviewer_passed=True,
            audit_clean=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p10_fail_audit(self):
        from src.backend.gates.gate_p10 import GateP10

        gate = GateP10()
        result = gate.check(
            rough_cut_exists=True,
            reviewer_passed=True,
            audit_clean=False,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False
