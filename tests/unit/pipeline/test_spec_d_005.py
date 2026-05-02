"""Tests for [SPEC-D-005] Phase P5-P6: BGM & SFX Producers, Reviewers, Gates."""


# ---------------------------------------------------------------------------
# AC-1: BGMAgent emotion_curve.json
# ---------------------------------------------------------------------------


class TestAC1BgmEmotionCurve:
    def test_emotion_curve_per_segment(self):
        from src.backend.agents.bgm_agent import BGMAgent

        agent = BGMAgent()
        timeline = {
            "segments": [
                {
                    "segment_id": "seg_001",
                    "start_sec": 0.0,
                    "end_sec": 10.0,
                    "emotion_tone": "excited",
                },
                {
                    "segment_id": "seg_002",
                    "start_sec": 10.0,
                    "end_sec": 25.0,
                    "emotion_tone": "neutral",
                },
                {
                    "segment_id": "seg_003",
                    "start_sec": 25.0,
                    "end_sec": 35.0,
                    "emotion_tone": "calm",
                },
            ],
            "total_duration_sec": 35.0,
        }
        result = agent.produce_emotion_curve(timeline=timeline)
        assert "segments" in result
        for entry in result["segments"]:
            assert "segment_id" in entry
            assert "emotion" in entry
            assert "energy" in entry
            assert 1 <= entry["energy"] <= 10
        assert len(result["segments"]) == 3


# ---------------------------------------------------------------------------
# AC-2: BGM candidates correlated with emotion
# ---------------------------------------------------------------------------


class TestAC2BgmCandidatesCorrelated:
    def test_candidates_correlated_with_emotion(self):
        from src.backend.agents.bgm_agent import BGMAgent

        agent = BGMAgent()
        emotion_curve = {
            "segments": [
                {"segment_id": "seg_001", "emotion": "excited", "energy": 8},
                {"segment_id": "seg_002", "emotion": "calm", "energy": 3},
            ],
        }
        result = agent.select_bgm_candidates(emotion_curve=emotion_curve, count=3)
        assert isinstance(result, list)
        assert len(result) == 3
        for c in result:
            assert "track_id" in c
            assert "energy_score" in c


# ---------------------------------------------------------------------------
# AC-3: BGM volume envelope
# ---------------------------------------------------------------------------


class TestAC3BgmVolumeEnvelope:
    def test_volume_envelope_per_segment_type(self):
        from src.backend.agents.bgm_agent import BGMAgent

        agent = BGMAgent()
        envelope = agent.design_volume_envelope(
            segments=[
                {"type": "hook", "start_sec": 0.0},
                {"type": "body", "start_sec": 5.0},
                {"type": "transition", "start_sec": 20.0},
            ]
        )
        assert isinstance(envelope, list)
        for entry in envelope:
            assert "volume_db" in entry
            assert entry["volume_db"] <= -12


# ---------------------------------------------------------------------------
# AC-4: BGM 2-level fallback
# ---------------------------------------------------------------------------


class TestAC4BgmFallback:
    def test_fallback_mubert_to_local(self):
        from src.backend.agents.bgm_agent import BGMAgent

        agent = BGMAgent()
        result = agent.fetch_bgm_track(
            source="mubert_api",
            emotion="excited",
            energy=8,
        )
        assert "track_id" in result or "fallback_used" in result


# ---------------------------------------------------------------------------
# AC-5: BGM copyright
# ---------------------------------------------------------------------------


class TestAC5CopyrightMarking:
    def test_copyright_marking(self):
        from src.backend.agents.bgm_agent import BGMAgent

        agent = BGMAgent()
        candidates = [
            {"track_id": "track_001", "source": "mubert"},
            {"track_id": "track_002", "source": "local_library"},
        ]
        result = agent.mark_copyright(candidates)
        for c in result:
            assert "copyright" in c
            assert c["copyright"] in ("CC0", "CC-BY", "proprietary")


# ---------------------------------------------------------------------------
# AC-6: MusicFitReviewer L1 + L2
# ---------------------------------------------------------------------------


class TestAC6MusicFitReviewerL1L2:
    def test_l1_duration_insufficient_fail(self):
        from src.backend.agents.music_fit_reviewer import MusicFitReviewer

        reviewer = MusicFitReviewer()
        result = reviewer.review_l1(
            bgm_duration=5.0,
            video_duration=60.0,
            volume_db=-18,
            copyright_tag="CC0",
        )
        assert result["verdict"] == "FAIL"

    def test_l1_volume_too_high_fail(self):
        from src.backend.agents.music_fit_reviewer import MusicFitReviewer

        reviewer = MusicFitReviewer()
        result = reviewer.review_l1(
            bgm_duration=60.0,
            video_duration=60.0,
            volume_db=-10,
            copyright_tag="CC0",
        )
        assert result["verdict"] == "FAIL"

    def test_l1_pass_triggers_l2(self):
        from src.backend.agents.music_fit_reviewer import MusicFitReviewer

        reviewer = MusicFitReviewer()
        l1_result = reviewer.review_l1(
            bgm_duration=65.0,
            video_duration=60.0,
            volume_db=-20,
            copyright_tag="CC0",
        )
        assert l1_result["verdict"] == "PASS"

    def test_l1_fail_skips_l2_zero_tokens(self):
        from src.backend.agents.music_fit_reviewer import MusicFitReviewer

        reviewer = MusicFitReviewer()
        full = reviewer.review(
            bgm_duration=5.0,
            video_duration=60.0,
            volume_db=-10,
            copyright_tag="INVALID",
            emotion_curve={"segments": []},
        )
        assert full["l2_called"] is False


# ---------------------------------------------------------------------------
# AC-7: Gate-P5
# ---------------------------------------------------------------------------


class TestAC7GateP5:
    def test_gate_p5_pass(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check(
            skipped=False,
            bgm_exists=True,
            reviewer_passed=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p5_skipped_pass(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check(
            skipped=True,
            bgm_exists=False,
            reviewer_passed=False,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p5_fail_unplayable_bgm(self):
        from src.backend.gates.gate_p5 import GateP5

        gate = GateP5()
        result = gate.check(
            skipped=False,
            bgm_exists=False,
            reviewer_passed=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False


# ---------------------------------------------------------------------------
# AC-8: SFX Agent output
# ---------------------------------------------------------------------------


class TestAC8SfxOutputAllFields:
    def test_sfx_output_all_fields(self):
        from src.backend.agents.sfx_agent import SFXAgent

        agent = SFXAgent()
        timeline = {
            "segments": [
                {
                    "segment_id": "seg_001",
                    "start_sec": 0.0,
                    "end_sec": 10.0,
                    "content": "今日股市开盘",
                },
                {
                    "segment_id": "seg_002",
                    "start_sec": 10.0,
                    "end_sec": 25.0,
                    "content": "沪指上涨",
                },
            ],
        }
        result = agent.produce_sfx(timeline=timeline)
        assert isinstance(result, list)
        for sfx in result:
            assert "sfx_id" in sfx
            assert "type" in sfx
            assert "semantic_type" in sfx
            assert "timestamp_seconds" in sfx
            assert "trigger_text" in sfx
            assert "reason" in sfx
            assert "volume_db" in sfx

    def test_type_semantic_type_mapping(self):
        from src.backend.agents.sfx_agent import SFXAgent

        agent = SFXAgent()
        mapping = agent.get_type_mapping()
        assert "boom" in mapping or len(mapping) > 0
        for ftype, stype in mapping.items():
            assert isinstance(ftype, str)
            assert isinstance(stype, str)


# ---------------------------------------------------------------------------
# AC-9: SFX constraints
# ---------------------------------------------------------------------------


class TestAC9SfxConstraints:
    def test_interval_constraint(self):
        from src.backend.agents.sfx_agent import SFXAgent

        agent = SFXAgent()
        sfx_list = [
            {"timestamp_seconds": 0.0},
            {"timestamp_seconds": 5.0},
            {"timestamp_seconds": 20.0},
        ]
        result = agent.check_sparsity(sfx_list, min_interval=15.0)
        assert "verdict" in result

    def test_type_diversity_constraint(self):
        from src.backend.agents.sfx_agent import SFXAgent

        agent = SFXAgent()
        sfx_list = [
            {"type": "boom"},
            {"type": "boom"},
        ]
        result = agent.check_type_diversity(sfx_list, min_types=3)
        assert result["verdict"] == "FAIL"

    def test_no_bgm_transition_overlap(self):
        from src.backend.agents.sfx_agent import SFXAgent

        agent = SFXAgent()
        sfx_list = [{"timestamp_seconds": 9.5}]
        bgm_transitions = [10.0, 20.0]
        result = agent.check_bgm_overlap(
            sfx_list=sfx_list,
            bgm_transition_timestamps=bgm_transitions,
            tolerance=2.0,
        )
        assert "verdict" in result


# ---------------------------------------------------------------------------
# AC-10: SFX 3-level fallback
# ---------------------------------------------------------------------------


class TestAC10SfxFallback:
    def test_fallback_builtin_to_freesound(self):
        from src.backend.agents.sfx_agent import SFXAgent

        agent = SFXAgent()
        result = agent.fetch_sfx(source="builtin", sfx_type="boom")
        assert "file_path" in result or "fallback_used" in result


# ---------------------------------------------------------------------------
# AC-11: SFXReviewer pure L1
# ---------------------------------------------------------------------------


class TestAC11SfxReviewer:
    def test_sfx_reviewer_pure_l1_no_llm(self):
        from src.backend.agents.sfx_reviewer import SFXReviewer

        reviewer = SFXReviewer()
        sfx_list = [
            {
                "sfx_id": "sfx_001",
                "type": "boom",
                "timestamp_seconds": 8.0,
                "volume_db": -18,
            },
            {
                "sfx_id": "sfx_002",
                "type": "whoosh",
                "timestamp_seconds": 25.0,
                "volume_db": -20,
            },
            {
                "sfx_id": "sfx_003",
                "type": "ding",
                "timestamp_seconds": 42.0,
                "volume_db": -17,
            },
        ]
        result = reviewer.review(sfx_list=sfx_list, narration_volume_db=-12)
        assert "verdict" in result
        assert "checks" in result
        assert len(result["checks"]) >= 4

    def test_density_too_high_fail(self):
        from src.backend.agents.sfx_reviewer import SFXReviewer

        reviewer = SFXReviewer()
        sfx_list = [
            {
                "sfx_id": f"sfx_{i}",
                "type": "boom",
                "timestamp_seconds": float(i * 3),
                "volume_db": -18,
            }
            for i in range(20)
        ]
        result = reviewer.review(sfx_list=sfx_list, narration_volume_db=-12)
        density_check = next(
            (c for c in result["checks"] if c["rule"] == "density"), None
        )
        assert density_check is not None
        assert density_check["verdict"] == "FAIL"

    def test_voice_masking_fail(self):
        from src.backend.agents.sfx_reviewer import SFXReviewer

        reviewer = SFXReviewer()
        sfx_list = [
            {
                "sfx_id": "sfx_001",
                "type": "boom",
                "timestamp_seconds": 5.0,
                "volume_db": -5,
            }
        ]
        result = reviewer.review(sfx_list=sfx_list, narration_volume_db=-12)
        masking_check = next(
            (c for c in result["checks"] if c["rule"] == "voice_masking"), None
        )
        assert masking_check is not None
        assert masking_check["verdict"] == "FAIL"


# ---------------------------------------------------------------------------
# AC-12: Gate-P6
# ---------------------------------------------------------------------------


class TestAC12GateP6:
    def test_gate_p6_pass(self):
        from src.backend.gates.gate_p6 import GateP6

        gate = GateP6()
        result = gate.check(
            skipped=False,
            sfx_exists=True,
            reviewer_passed=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p6_skipped_pass(self):
        from src.backend.gates.gate_p6 import GateP6

        gate = GateP6()
        result = gate.check(
            skipped=True,
            sfx_exists=False,
            reviewer_passed=False,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True


# ---------------------------------------------------------------------------
# AC-13: Consecutive SFX fail -> suggest skip
# ---------------------------------------------------------------------------


class TestAC13ConsecutiveSfxFail:
    def test_3_consecutive_fails_suggest_skip(self):
        from src.backend.agents.sfx_reviewer import SFXReviewer

        reviewer = SFXReviewer()
        assert reviewer.should_suggest_skip(consecutive_fails=3) is True
        assert reviewer.should_suggest_skip(consecutive_fails=2) is False
        assert reviewer.should_suggest_skip(consecutive_fails=0) is False
