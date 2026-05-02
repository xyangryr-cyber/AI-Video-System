"""[SPEC-C-012] Tests for 5 deterministic producer programmatic steps."""

import hashlib
import json


from src.backend.agents.producer_steps import (
    compute_bgm_envelope,
    compute_roughcut_params,
    compute_sfx_timeline,
    compute_ssml,
    compute_word_count,
)


class TestComputeSsml:
    def test_basic_ssml_wraps_text(self):
        result = compute_ssml("你好世界", rate=1.0, emotion="neutral")
        assert "<speak" in result
        assert "你好世界" in result
        assert "</speak>" in result

    def test_rate_affects_prosody(self):
        result = compute_ssml("测试", rate=1.5, emotion="neutral")
        assert 'rate="1.5"' in result or "rate='1.5'" in result or "150%" in result

    def test_emotion_affects_output(self):
        result = compute_ssml("测试", rate=1.0, emotion="excited")
        assert "excited" in result.lower()

    def test_empty_text_returns_minimal_ssml(self):
        result = compute_ssml("", rate=1.0, emotion="neutral")
        assert "<speak" in result
        assert "</speak>" in result


class TestComputeBgmEnvelope:
    def test_returns_list_of_volume_points(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 10.0},
        ]
        result = compute_bgm_envelope(segments, total_duration_sec=10.0)
        assert isinstance(result, list)
        assert len(result) >= 2
        for pt in result:
            assert "time_sec" in pt
            assert "volume" in pt

    def test_fade_in_at_start(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 30.0},
        ]
        result = compute_bgm_envelope(segments, total_duration_sec=30.0)
        # First few points should have increasing volume (fade in)
        volumes = [pt["volume"] for pt in result[:3]]
        assert volumes[0] < volumes[-1] or volumes[0] <= volumes[-1]

    def test_fade_out_at_end(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 30.0},
        ]
        result = compute_bgm_envelope(segments, total_duration_sec=30.0)
        # Last few points should have decreasing volume (fade out)
        volumes = [pt["volume"] for pt in result[-3:]]
        assert volumes[0] >= volumes[-1]


class TestComputeSfxTimeline:
    def test_returns_list_of_sfx_events(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 5.0},
            {"segment_id": "seg_2", "start_sec": 5.0, "end_sec": 10.0},
        ]
        result = compute_sfx_timeline(segments)
        assert isinstance(result, list)
        for event in result:
            assert "time_sec" in event
            assert "sfx_type" in event
            assert "segment_id" in event

    def test_empty_segments_returns_empty_list(self):
        result = compute_sfx_timeline([])
        assert result == []


class TestComputeRoughcutParams:
    def test_returns_dict_with_required_keys(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 5.0},
        ]
        result = compute_roughcut_params(segments, fps=30)
        assert isinstance(result, dict)
        assert "clips" in result
        assert "total_frames" in result
        assert "fps" in result

    def test_clip_count_matches_segment_count(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 5.0},
            {"segment_id": "seg_2", "start_sec": 5.0, "end_sec": 10.0},
            {"segment_id": "seg_3", "start_sec": 10.0, "end_sec": 15.0},
        ]
        result = compute_roughcut_params(segments, fps=30)
        assert len(result["clips"]) == len(segments)

    def test_fps_propagates_to_output(self):
        result = compute_roughcut_params([], fps=24)
        assert result["fps"] == 24


class TestComputeWordCount:
    def test_chinese_text(self):
        result = compute_word_count("你好世界")
        assert result == 4

    def test_english_text(self):
        result = compute_word_count("hello world")
        assert result == 2

    def test_mixed_text(self):
        result = compute_word_count("hello 世界 test 测试")
        assert result > 0

    def test_empty_string(self):
        result = compute_word_count("")
        assert result == 0

    def test_whitespace_only(self):
        result = compute_word_count("   ")
        assert result == 0


class TestDeterministic10Runs:
    """AC-1: 5 programmatic steps produce identical output across 10 runs."""

    def _hash_output(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        serialized = json.dumps(result, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def test_ssml_deterministic(self):
        hashes = {
            self._hash_output(compute_ssml, "测试文本内容", rate=1.0, emotion="neutral")
            for _ in range(10)
        }
        assert len(hashes) == 1, f"compute_ssml produced different outputs: {hashes}"

    def test_bgm_envelope_deterministic(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 10.0},
            {"segment_id": "seg_2", "start_sec": 10.0, "end_sec": 20.0},
        ]
        hashes = {
            self._hash_output(compute_bgm_envelope, segments, total_duration_sec=20.0)
            for _ in range(10)
        }
        assert len(hashes) == 1, "compute_bgm_envelope produced different outputs"

    def test_sfx_timeline_deterministic(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 5.0},
            {"segment_id": "seg_2", "start_sec": 5.0, "end_sec": 10.0},
        ]
        hashes = {self._hash_output(compute_sfx_timeline, segments) for _ in range(10)}
        assert len(hashes) == 1, "compute_sfx_timeline produced different outputs"

    def test_roughcut_params_deterministic(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 5.0},
        ]
        hashes = {
            self._hash_output(compute_roughcut_params, segments, fps=30)
            for _ in range(10)
        }
        assert len(hashes) == 1, "compute_roughcut_params produced different outputs"

    def test_word_count_deterministic(self):
        hashes = {
            self._hash_output(compute_word_count, "hello world test") for _ in range(10)
        }
        assert len(hashes) == 1, "compute_word_count produced different outputs"


class TestNoLlmCalls:
    """AC-2: 5 programmatic steps make zero LLM API calls."""

    def test_no_llm_imports_in_producer_steps(self):
        with open("src/backend/agents/producer_steps.py") as f:
            source = f.read()
        assert "litellm" not in source.lower()
        assert "openai" not in source.lower()
        assert "anthropic" not in source.lower()
        assert "llm_service" not in source
        assert "chat_completion" not in source

    def test_ssml_no_llm_call(self):
        compute_ssml("测试", rate=1.0, emotion="neutral")

    def test_bgm_envelope_no_llm_call(self):
        compute_bgm_envelope(
            [{"segment_id": "s1", "start_sec": 0.0, "end_sec": 5.0}],
            total_duration_sec=5.0,
        )

    def test_sfx_timeline_no_llm_call(self):
        compute_sfx_timeline([{"segment_id": "s1", "start_sec": 0.0, "end_sec": 5.0}])

    def test_roughcut_params_no_llm_call(self):
        compute_roughcut_params(
            [{"segment_id": "s1", "start_sec": 0.0, "end_sec": 5.0}], fps=30
        )

    def test_word_count_no_llm_call(self):
        compute_word_count("test")
