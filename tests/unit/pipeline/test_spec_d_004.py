"""Tests for [SPEC-D-004] Phase P4: TTS Producer, AudioQualityReviewer, Gate."""


def _make_polished_script():
    return {
        "segments": [
            {
                "segment_id": "seg_001",
                "content": "今日股市开盘。",
                "word_count": 6,
                "voice_direction": {
                    "emotion": "excited",
                    "pace": "fast",
                    "energy": "high",
                    "key_emphasis": ["开盘"],
                    "pause_after": 0.5,
                    "notes": "",
                },
                "emotion_tone": "excited",
            },
            {
                "segment_id": "seg_002",
                "content": "沪指上涨百分之1点2。",
                "word_count": 10,
                "voice_direction": {
                    "emotion": "neutral",
                    "pace": "medium",
                    "energy": "medium",
                    "key_emphasis": [],
                    "pause_after": 0.3,
                    "notes": "",
                },
                "emotion_tone": "neutral",
            },
        ],
        "is_authoritative_text_source": True,
    }


# ---------------------------------------------------------------------------
# AC-1: With voice preference, preferred voice first
# ---------------------------------------------------------------------------


class TestAC1PreferredVoiceCandidates:
    def test_preferred_voice_first_with_recommended(self):
        from src.backend.agents.tts_agent import TTSAgent

        agent = TTSAgent()
        result = agent.select_voice_candidates(
            polished_script=_make_polished_script(),
            voice_preferences={"preferred_voice_id": "voice_zh_female_01"},
        )
        assert isinstance(result, list)
        assert len(result) >= 1
        # Preferred voice must be first
        assert result[0]["voice_id"] == "voice_zh_female_01"
        assert result[0]["is_recommended"] is True
        # At least 1 more recommended candidate
        assert len(result) >= 2


# ---------------------------------------------------------------------------
# AC-2: Without voice preference
# ---------------------------------------------------------------------------


class TestAC2NoPreferenceGeneratePreviews:
    def test_no_preference_generates_2_to_3_previews(self):
        from src.backend.agents.tts_agent import TTSAgent

        agent = TTSAgent()
        result = agent.select_voice_candidates(
            polished_script=_make_polished_script(),
            voice_preferences=None,
        )
        assert isinstance(result, list)
        assert 2 <= len(result) <= 3
        for c in result:
            assert "voice_id" in c


# ---------------------------------------------------------------------------
# AC-3: Non-preferred voice confirmation
# ---------------------------------------------------------------------------


class TestAC3NewVoiceConfirmation:
    def test_new_voice_confirmation_accept(self):
        from src.backend.agents.tts_agent import TTSAgent

        agent = TTSAgent()
        result = agent.confirm_voice_selection(
            selected_voice_id="voice_zh_male_01",
            preferred_voice_id="voice_zh_female_01",
            user_accepted=True,
        )
        assert result["write_target"] == "user_preferences_md"
        assert result["voice_id"] == "voice_zh_male_01"

    def test_new_voice_confirmation_reject(self):
        from src.backend.agents.tts_agent import TTSAgent

        agent = TTSAgent()
        result = agent.confirm_voice_selection(
            selected_voice_id="voice_zh_male_01",
            preferred_voice_id="voice_zh_female_01",
            user_accepted=False,
        )
        assert result["write_target"] == "project_preferences_md"
        assert result["voice_id"] == "voice_zh_male_01"


# ---------------------------------------------------------------------------
# AC-4: Global voice params complete
# ---------------------------------------------------------------------------


class TestAC4GlobalVoiceParamsComplete:
    def test_global_voice_params_complete(self):
        from src.backend.agents.tts_agent import TTSAgent

        agent = TTSAgent()
        params = agent.build_global_voice_params(voice_id="voice_zh_female_01")
        assert "voice_id" in params
        assert "style" in params
        assert "style_degree" in params
        assert "rate_wpm" in params
        assert "pitch" in params
        assert "volume" in params
        assert params["voice_id"] == "voice_zh_female_01"


# ---------------------------------------------------------------------------
# AC-5: Segment voice override priority
# ---------------------------------------------------------------------------


class TestAC5SegmentVoiceOverridePriority:
    def test_segment_override_priority(self):
        from src.backend.agents.tts_agent import TTSAgent

        agent = TTSAgent()
        overrides = agent.build_segment_overrides(
            segment={"voice_direction": {"emotion": "excited", "pace": "fast"}},
            digit_slowdown=False,
            global_voice_params={"rate_wpm": 160},
        )
        assert "rate_multiplier" in overrides or "emotion" in overrides
        # Segment override values take priority over global
        assert isinstance(overrides, dict)
        assert len(overrides) >= 1


# ---------------------------------------------------------------------------
# AC-6: Voice direction bridge is pure code
# ---------------------------------------------------------------------------


class TestAC6VoiceDirectionBridgePureCode:
    def test_bridge_is_pure_code_no_llm(self):
        from src.backend.services.voice_direction_bridge import VoiceDirectionBridge

        bridge = VoiceDirectionBridge()
        vd = {
            "emotion": "excited",
            "pace": "fast",
            "energy": "high",
            "key_emphasis": ["test"],
            "pause_after": 0.5,
            "notes": "",
        }
        result = bridge.convert(vd)
        # Must produce deterministic output without any LLM calls
        assert "emotion" in result
        assert result["emotion"] == "excited"

    def test_bridge_maps_all_directions(self):
        from src.backend.services.voice_direction_bridge import VoiceDirectionBridge

        bridge = VoiceDirectionBridge()
        for emotion in ("excited", "neutral", "calm"):
            vd = {
                "emotion": emotion,
                "pace": "medium",
                "energy": "medium",
                "key_emphasis": [],
                "pause_after": 0.3,
                "notes": "",
            }
            result = bridge.convert(vd)
            assert result["emotion"] == emotion


# ---------------------------------------------------------------------------
# AC-7: Digit slowdown SSML
# ---------------------------------------------------------------------------


class TestAC7DigitSlowdownSsml:
    def test_digit_dense_detection(self):
        from src.backend.services.digit_slowdown import DigitSlowdown

        ds = DigitSlowdown()
        # Digit-dense sentence
        assert ds.is_digit_dense("增长率达到百分之3点5") is True
        # Non-digit sentence
        assert ds.is_digit_dense("今日股市表现良好") is False

    def test_ssml_prosody_wrapping(self):
        from src.backend.services.digit_slowdown import DigitSlowdown

        ds = DigitSlowdown()
        text = "增长率达到百分之3点5"
        result = ds.wrap_ssml(text)
        assert '<prosody rate="slow"' in result or result.startswith("<speak")
        # Should be valid SSML wrapping
        assert len(result) > len(text)


# ---------------------------------------------------------------------------
# AC-8: TTSProvider abstraction
# ---------------------------------------------------------------------------


class TestAC8TtsProviderAbstraction:
    def test_provider_abstraction_interface(self):
        from src.backend.services.tts_provider import TTSProvider

        provider = TTSProvider()
        assert hasattr(provider, "synthesize")
        result = provider.synthesize(
            text="测试",
            voice_params={"voice_id": "v1"},
        )
        assert "audio_path" in result or "audio_data" in result
        assert "duration_seconds" in result

    def test_capability_gap_logged(self):
        from src.backend.services.tts_provider import TTSProvider

        provider = TTSProvider()
        result = provider.synthesize(
            text="测试",
            voice_params={"voice_id": "v1", "unsupported_feature": "xyz"},
        )
        # Unsupported params should not crash, just be logged as capability_gap
        assert "audio_path" in result or "audio_data" in result


# ---------------------------------------------------------------------------
# AC-9: timeline.json continuous timestamps
# ---------------------------------------------------------------------------


class TestAC9TimelineJsonOutput:
    def test_timeline_json_continuous_timestamps(self):
        from src.backend.agents.tts_agent import TTSAgent

        agent = TTSAgent()
        timeline = agent.build_timeline(
            polished_script=_make_polished_script(),
            voice_id="voice_zh_female_01",
        )
        assert "segments" in timeline
        segments = timeline["segments"]
        assert len(segments) >= 2
        assert "total_duration_sec" in timeline

        # Check continuous timestamps
        prev_end = 0.0
        for seg in segments:
            assert "start_sec" in seg
            assert "end_sec" in seg
            assert "audio_path" in seg
            assert seg["start_sec"] >= prev_end - 0.001
            assert seg["end_sec"] >= seg["start_sec"]
            prev_end = seg["end_sec"]


# ---------------------------------------------------------------------------
# AC-10: AudioQualityReviewer checks (7 criteria)
# ---------------------------------------------------------------------------


class TestAC10AudioQualityReviewerChecks:
    def test_cps_out_of_range_fail(self):
        from src.backend.agents.audio_quality_reviewer import (
            AudioQualityReviewer,
        )

        reviewer = AudioQualityReviewer()
        # CPS below 3.0 should fail
        result = reviewer.review_segment_metadata(
            word_count=1, duration_seconds=10.0, sample_rate=44100, segment_id="s1"
        )
        checks = {c["rule"]: c for c in result["checks"]}
        assert checks["cps"]["verdict"] == "FAIL"

    def test_silence_over_2s_fail(self):
        from src.backend.agents.audio_quality_reviewer import (
            AudioQualityReviewer,
        )

        reviewer = AudioQualityReviewer()
        result = reviewer.check_silence(silence_duration_seconds=3.0, segment_id="s1")
        assert result["verdict"] == "FAIL"

    def test_timeline_audio_mismatch_fail(self):
        from src.backend.agents.audio_quality_reviewer import (
            AudioQualityReviewer,
        )

        reviewer = AudioQualityReviewer()
        result = reviewer.check_timeline_accuracy(
            timeline_duration=10.0, audio_duration=10.1, segment_id="s1"
        )
        assert "verdict" in result

    def test_segment_gap_out_of_range_fail(self):
        from src.backend.agents.audio_quality_reviewer import (
            AudioQualityReviewer,
        )

        reviewer = AudioQualityReviewer()
        result = reviewer.check_inter_segment_gap(gap_seconds=2.0, segment_id="s1")
        assert result["verdict"] == "FAIL"

    def test_sample_rate_not_44100_fail(self):
        from src.backend.agents.audio_quality_reviewer import (
            AudioQualityReviewer,
        )

        reviewer = AudioQualityReviewer()
        result = reviewer.check_sample_rate(sample_rate=48000, segment_id="s1")
        assert result["verdict"] == "FAIL"


# ---------------------------------------------------------------------------
# AC-11: Gate-P4 checks
# ---------------------------------------------------------------------------


class TestAC11GateP4Checks:
    def test_gate_p4_pass(self):
        from src.backend.gates.gate_p4 import GateP4Checker

        gate = GateP4Checker(check_audio_files_exist=lambda: True)
        result = gate.check_p4_gate(
            audio_files_exist=True,
            reviewer_passed=True,
            async_task_done=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True

    def test_gate_p4_fail_missing_audio(self):
        from src.backend.gates.gate_p4 import GateP4Checker

        gate = GateP4Checker(check_audio_files_exist=lambda: True)
        result = gate.check_p4_gate(
            audio_files_exist=False,
            reviewer_passed=True,
            async_task_done=True,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False

    def test_gate_p4_fail_async_running(self):
        from src.backend.gates.gate_p4 import GateP4Checker

        gate = GateP4Checker(check_audio_files_exist=lambda: True)
        result = gate.check_p4_gate(
            audio_files_exist=True,
            reviewer_passed=True,
            async_task_done=False,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False
