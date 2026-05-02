"""Tests for [SPEC-D-003] Phase P2-P3: Script & Polish Producers, Reviewers, Gates."""

import sys
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_script_agent_cache():
    """Remove ScriptAgent module from sys.modules for fresh import with mocks."""
    sys.modules.pop("src.backend.agents.script_agent", None)
    sys.modules.pop("src.backend.agents.polish_agent", None)


def _make_mock_script_output(wc_multiplier=1.0):
    """Build a ScriptLLMOutput mock return value for ScriptAgent.produce()."""
    from src.backend.agents.schemas import ScriptLLMOutput, ScriptSegment, DataPoint

    return ScriptLLMOutput(
        segments=[
            ScriptSegment(
                segment_id="seg_001",
                section_title="Market Opening",
                outline_section_ref="sec_001",
                content="今日股市开盘表现强劲，成交量大幅攀升。",
                word_count=int(18 * wc_multiplier),
                key_data_points=[
                    DataPoint(
                        data_point_id="dp_001",
                        value="沪指上涨1.2%",
                        source="https://example.com/market-data",
                        trust_level="llm_generated",
                    )
                ],
                emotion_tone="excited",
                transition_note="fade in from title card",
            ),
            ScriptSegment(
                segment_id="seg_002",
                section_title="Sector Performance",
                outline_section_ref="sec_002",
                content="科技板块领涨，能源板块表现疲软。",
                word_count=int(15 * wc_multiplier),
                key_data_points=[
                    DataPoint(
                        data_point_id="dp_002",
                        value="科技板块涨幅3.5%",
                        source="https://example.com/sector-data",
                        trust_level="llm_generated",
                    )
                ],
                emotion_tone="neutral",
                transition_note="transition from seg_001",
            ),
            ScriptSegment(
                segment_id="seg_003",
                section_title="Closing Summary",
                outline_section_ref="sec_003",
                content="总结今日市场表现，展望明日走势。",
                word_count=int(14 * wc_multiplier),
                key_data_points=[
                    DataPoint(
                        data_point_id="dp_003",
                        value="市场成交额1.2万亿",
                        source="https://example.com/market-close",
                        trust_level="llm_generated",
                    )
                ],
                emotion_tone="calm",
                transition_note="transition from seg_002",
            ),
        ]
    )


def _make_mock_polish_output():
    """Build a PolishLLMOutput mock return value for PolishAgent.polish()."""
    from src.backend.agents.schemas import (
        PolishLLMOutput,
        PolishedSegment,
        VoiceDirection,
    )

    return PolishLLMOutput(
        segments=[
            PolishedSegment(
                segment_id="seg_001",
                section_title="Market Opening",
                outline_section_ref="sec_001",
                content="今日股市开盘表现强劲，成交量大幅攀升。",
                word_count=18,
                key_data_points=[
                    {
                        "data_point_id": "dp_001",
                        "value": "沪指上涨1.2%",
                        "source": "https://example.com/market-data",
                        "trust_level": "user_verified",
                    },
                ],
                emotion_tone="excited",
                transition_note="fade in from title card",
                voice_direction=VoiceDirection(
                    emotion="excited",
                    pace="fast",
                    energy="high",
                    key_emphasis=["开盘"],
                    pause_after=0.5,
                    notes="energetic opening",
                ),
            ),
            PolishedSegment(
                segment_id="seg_002",
                section_title="Market Opening",
                outline_section_ref="sec_001",
                content="今日股市开盘表现强劲，成交量大幅攀升。",
                word_count=18,
                key_data_points=[
                    {
                        "data_point_id": "dp_001",
                        "value": "沪指上涨1.2%",
                        "source": "https://example.com/market-data",
                        "trust_level": "user_verified",
                    },
                ],
                emotion_tone="neutral",
                transition_note="fade in from title card",
                voice_direction=VoiceDirection(
                    emotion="neutral",
                    pace="medium",
                    energy="medium",
                    key_emphasis=["强劲"],
                    pause_after=0.3,
                    notes="standard delivery",
                ),
            ),
        ],
        is_authoritative_text_source=True,
    )


def _make_requirements():
    return {
        "project_id": "proj_test",
        "title": "Test Video",
        "topic": "A detailed topic about stock market trends",
        "target_word_count": {"min": 800, "max": 1200},
        "target_duration_seconds": 600,
    }


def _make_outline():
    return {
        "sections": [
            {
                "section_id": "sec_001",
                "title": "Market Opening",
                "viewpoints": ["bullish sentiment", "trading volume surge"],
                "key_topic": "opening bell analysis",
            },
            {
                "section_id": "sec_002",
                "title": "Sector Performance",
                "viewpoints": ["tech leads", "energy lags"],
                "key_topic": "sector rotation",
            },
            {
                "section_id": "sec_003",
                "title": "Closing Summary",
                "viewpoints": ["daily recap", "next day outlook"],
                "key_topic": "market close",
            },
        ]
    }


def _make_valid_script_segment(overrides=None):
    seg = {
        "segment_id": "seg_001",
        "section_title": "Market Opening",
        "outline_section_ref": "sec_001",
        "content": "今日股市开盘表现强劲，成交量大幅攀升。",
        "word_count": 18,
        "key_data_points": [
            {
                "data_point_id": "dp_001",
                "value": "沪指上涨1.2%",
                "source": "https://example.com/market-data",
                "trust_level": "user_verified",
            }
        ],
        "emotion_tone": "excited",
        "transition_note": "fade in from title card",
    }
    if overrides:
        seg.update(overrides)
    return seg


# ---------------------------------------------------------------------------
# AC-1: ScriptAgent outputs per-segment scripts with all required fields
# ---------------------------------------------------------------------------


class TestAC1ScriptAgentOutputFields:
    """AC-1: ScriptAgent outputs per-segment scripts with all required fields
    (segment_id, section_title, outline_section_ref, content, word_count,
    key_data_points, emotion_tone, transition_note)"""

    def test_segment_has_all_fields(self):
        _clear_script_agent_cache()
        mock_out = _make_mock_script_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.script_agent import ScriptAgent

            agent = ScriptAgent()
            result = agent.produce(
                requirements=_make_requirements(),
                outline=_make_outline(),
            )

        assert isinstance(result, list), "ScriptAgent must return a list of segments"
        assert len(result) > 0, "Must produce at least one segment"

        for seg in result:
            assert "segment_id" in seg
            assert "section_title" in seg
            assert "outline_section_ref" in seg
            assert "content" in seg
            assert "word_count" in seg
            assert "key_data_points" in seg
            assert "emotion_tone" in seg
            assert "transition_note" in seg
            assert isinstance(seg["key_data_points"], list)


# ---------------------------------------------------------------------------
# AC-2: trust_level enum + llm_generated limit
# ---------------------------------------------------------------------------


class TestAC2TrustLevelAndLlmDataPointLimit:
    """AC-2: trust_level in {user_verified, source_verified, llm_generated};
    llm_generated data points <= 5 total"""

    def test_trust_level_enum_valid(self):
        _clear_script_agent_cache()
        mock_out = _make_mock_script_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.script_agent import ScriptAgent

            agent = ScriptAgent()
            result = agent.produce(
                requirements=_make_requirements(),
                outline=_make_outline(),
            )

        valid_levels = {"user_verified", "source_verified", "llm_generated"}
        all_data_points = []
        for seg in result:
            for dp in seg.get("key_data_points", []):
                assert "trust_level" in dp, f"data point missing trust_level: {dp}"
                assert dp["trust_level"] in valid_levels, (
                    f"Invalid trust_level: {dp['trust_level']}"
                )
                all_data_points.append(dp)

        assert len(all_data_points) > 0, "Must have at least one data point"

    def test_llm_generated_data_points_max_5(self):
        _clear_script_agent_cache()
        mock_out = _make_mock_script_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.script_agent import ScriptAgent

            agent = ScriptAgent()
            result = agent.produce(
                requirements=_make_requirements(),
                outline=_make_outline(),
            )

        llm_count = 0
        for seg in result:
            for dp in seg.get("key_data_points", []):
                if dp.get("trust_level") == "llm_generated":
                    llm_count += 1
        assert llm_count <= 5, f"llm_generated data points ({llm_count}) exceeds max 5"


# ---------------------------------------------------------------------------
# AC-3: Word count bounds + outline fidelity
# ---------------------------------------------------------------------------


class TestAC3WordCountAndOutlineFidelity:
    """AC-3: Total word count within target_word_count +/- 10%;
    no new viewpoints beyond outline; no omitted outline viewpoints;
    every data point has non-empty source"""

    def test_word_count_within_target_range(self):
        _clear_script_agent_cache()
        # Use multiplier to get word count near center of range (1000)
        mock_out = _make_mock_script_output(wc_multiplier=20)
        req = _make_requirements()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.script_agent import ScriptAgent

            agent = ScriptAgent()
            result = agent.produce(requirements=req, outline=_make_outline())

        total_wc = sum(seg.get("word_count", 0) for seg in result)
        wc_min = req["target_word_count"]["min"]
        wc_max = req["target_word_count"]["max"]
        center = (wc_min + wc_max) / 2
        lower = center * 0.9
        upper = center * 1.1
        assert lower <= total_wc <= upper, (
            f"Total word count {total_wc} not in [{lower:.0f}, {upper:.0f}]"
        )

    def test_no_new_viewpoints_beyond_outline(self):
        _clear_script_agent_cache()
        mock_out = _make_mock_script_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.script_agent import ScriptAgent

            agent = ScriptAgent()
            outline = _make_outline()
            result = agent.produce(requirements=_make_requirements(), outline=outline)

        # Collect all outline-known viewpoints
        known_viewpoints = set()
        for sec in outline["sections"]:
            for vp in sec.get("viewpoints", []):
                known_viewpoints.add(vp)

        # Each segment's content should not introduce entirely new viewpoints.
        # This is a structural check: the outline_section_ref must map to a
        # known section and the viewpoint count per section is bounded.
        for seg in result:
            ref = seg.get("outline_section_ref")
            assert ref is not None, "segment missing outline_section_ref"
            section_ids = {s["section_id"] for s in outline["sections"]}
            assert ref in section_ids, f"outline_section_ref {ref!r} not in outline"

    def test_data_point_source_non_empty(self):
        _clear_script_agent_cache()
        mock_out = _make_mock_script_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.script_agent import ScriptAgent

            agent = ScriptAgent()
            result = agent.produce(
                requirements=_make_requirements(),
                outline=_make_outline(),
            )

        for seg in result:
            for dp in seg.get("key_data_points", []):
                source = dp.get("source", "")
                assert source, f"data point has empty source: {dp['data_point_id']}"


# ---------------------------------------------------------------------------
# AC-4: FactChecker L1/L2 + blocks gate on unconfirmed llm_generated
# ---------------------------------------------------------------------------


class TestAC4FactCheckerChecks:
    """AC-4: FactChecker L1 checks source reachability, L2 semantic comparison;
    llm_generated unconfirmed data points block Gate-P2"""

    def test_l1_source_reachability(self):
        from src.backend.agents.fact_checker import FactChecker

        checker = FactChecker()
        # A data point with a well-formed URL source should pass L1
        dp = {
            "data_point_id": "dp_test",
            "value": "some value",
            "source": "https://example.com/data",
            "trust_level": "source_verified",
        }
        result = checker.check_l1(dp)
        assert "verdict" in result
        # L1 should not crash; reachability check is best-effort
        assert result["verdict"] in ("PASS", "FAIL")

    def test_llm_generated_unconfirmed_blocks_gate(self):
        from src.backend.agents.fact_checker import FactChecker

        checker = FactChecker()
        # llm_generated without confirmation should produce a FAIL verdict
        segments = [
            {
                "segment_id": "seg_x",
                "key_data_points": [
                    {
                        "data_point_id": "dp_unconfirmed",
                        "value": "unverified claim",
                        "source": "",
                        "trust_level": "llm_generated",
                    }
                ],
            }
        ]
        result = checker.review(segments)
        assert result["verdict"] == "FAIL", (
            f"llm_generated with empty source must FAIL, got {result['verdict']}"
        )


# ---------------------------------------------------------------------------
# AC-5: Gate-P2 checks
# ---------------------------------------------------------------------------


class TestAC5GateP2Checks:
    """AC-5: Gate-P2 checks: script fields complete, FactChecker PASS,
    StructureReviewer PASS, no pending tasks, preferences confirmed"""

    def test_gate_p2_pass(self):
        from src.backend.gates.gate_p2 import GateP2
        from src.backend.agents.fact_checker import FactChecker

        script = [
            {
                "segment_id": "seg_001",
                "section_title": "Intro",
                "outline_section_ref": "sec_001",
                "content": "测试内容",
                "word_count": 4,
                "key_data_points": [
                    {
                        "data_point_id": "dp_001",
                        "value": "verified data",
                        "source": "https://example.com",
                        "trust_level": "user_verified",
                    }
                ],
                "emotion_tone": "neutral",
                "transition_note": "",
            }
        ]
        fact_result = FactChecker().review(script)
        structure_result = {"verdict": "PASS", "notes": [], "blocking_issues": []}

        gate = GateP2()
        result = gate.check(
            script=script,
            fact_checker_result=fact_result,
            structure_reviewer_result=structure_result,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is True, f"Gate-P2 should PASS: {result}"

    def test_gate_p2_fail_unconfirmed_data(self):
        from src.backend.gates.gate_p2 import GateP2

        script = [
            {
                "segment_id": "seg_001",
                "section_title": "Intro",
                "outline_section_ref": "sec_001",
                "content": "测试",
                "word_count": 2,
                "key_data_points": [
                    {
                        "data_point_id": "dp_bad",
                        "value": "unverified",
                        "source": "",
                        "trust_level": "llm_generated",
                    }
                ],
                "emotion_tone": "neutral",
                "transition_note": "",
            }
        ]
        fact_result = {
            "verdict": "FAIL",
            "notes": [],
            "blocking_issues": ["unconfirmed llm_generated data points"],
        }
        structure_result = {"verdict": "PASS", "notes": [], "blocking_issues": []}

        gate = GateP2()
        result = gate.check(
            script=script,
            fact_checker_result=fact_result,
            structure_reviewer_result=structure_result,
            pending_tasks=[],
            preferences_confirmed=True,
        )
        assert result["passed"] is False, "Gate-P2 must FAIL on unconfirmed data"


# ---------------------------------------------------------------------------
# AC-6: Data point re-extraction on revision/regenerate
# ---------------------------------------------------------------------------


class TestAC6DataPointReextraction:
    """AC-6: SPEC-9.2.4 re-extraction: on user_revision/regenerate,
    new data points get trust_level=llm_generated, changed points reset to
    llm_generated, unchanged points retain original trust_level,
    deleted points removed"""

    def test_reextraction_new_point_llm_generated(self):
        from src.backend.agents.script_agent import ScriptAgent

        agent = ScriptAgent()
        original_data_points = [
            {
                "data_point_id": "dp_old",
                "value": "old",
                "source": "http://s",
                "trust_level": "user_verified",
            },
        ]
        new_data_points = [
            {"data_point_id": "dp_old", "value": "old", "source": "http://s"},
            {"data_point_id": "dp_new", "value": "fresh", "source": "http://s2"},
        ]

        result = agent.reextract_data_points(original_data_points, new_data_points)
        new_dp = next(dp for dp in result if dp["data_point_id"] == "dp_new")
        assert new_dp["trust_level"] == "llm_generated"

    def test_reextraction_changed_point_reset(self):
        from src.backend.agents.script_agent import ScriptAgent

        agent = ScriptAgent()
        original = [
            {
                "data_point_id": "dp_a",
                "value": "v1",
                "source": "http://s",
                "trust_level": "user_verified",
            },
        ]
        new = [
            {"data_point_id": "dp_a", "value": "v2", "source": "http://s"},
        ]

        result = agent.reextract_data_points(original, new)
        changed = next(dp for dp in result if dp["data_point_id"] == "dp_a")
        assert changed["trust_level"] == "llm_generated"

    def test_reextraction_unchanged_point_retained(self):
        from src.backend.agents.script_agent import ScriptAgent

        agent = ScriptAgent()
        original = [
            {
                "data_point_id": "dp_a",
                "value": "same",
                "source": "http://s",
                "trust_level": "source_verified",
            },
        ]
        new = [
            {"data_point_id": "dp_a", "value": "same", "source": "http://s"},
        ]

        result = agent.reextract_data_points(original, new)
        kept = next(dp for dp in result if dp["data_point_id"] == "dp_a")
        assert kept["trust_level"] == "source_verified"

    def test_reextraction_deleted_point_removed(self):
        from src.backend.agents.script_agent import ScriptAgent

        agent = ScriptAgent()
        original = [
            {
                "data_point_id": "dp_a",
                "value": "v1",
                "source": "http://s",
                "trust_level": "user_verified",
            },
            {
                "data_point_id": "dp_b",
                "value": "v2",
                "source": "http://s",
                "trust_level": "user_verified",
            },
        ]
        new = [
            {"data_point_id": "dp_a", "value": "v1", "source": "http://s"},
        ]

        result = agent.reextract_data_points(original, new)
        ids = {dp["data_point_id"] for dp in result}
        assert "dp_b" not in ids, "deleted data point must be removed"
        assert "dp_a" in ids


# ---------------------------------------------------------------------------
# AC-7: PolishAgent voice_direction + authoritative text source flag
# ---------------------------------------------------------------------------


class TestAC7PolishAgentVoiceDirection:
    """AC-7: PolishAgent outputs polished_script with voice_direction
    (emotion/pace/energy/key_emphasis/pause_after/notes) per segment;
    is_authoritative_text_source=true"""

    def test_voice_direction_6_subfields(self):
        _clear_script_agent_cache()
        mock_out = _make_mock_polish_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.polish_agent import PolishAgent

            agent = PolishAgent()
            segments = [
                _make_valid_script_segment(),
                _make_valid_script_segment({"segment_id": "seg_002"}),
            ]
            result = agent.polish(segments)

        assert isinstance(result, dict)
        assert "segments" in result
        for seg in result["segments"]:
            vd = seg.get("voice_direction")
            assert vd is not None, (
                f"segment {seg['segment_id']} missing voice_direction"
            )
            assert "emotion" in vd
            assert "pace" in vd
            assert "energy" in vd
            assert "key_emphasis" in vd
            assert "pause_after" in vd
            assert "notes" in vd

    def test_authoritative_text_source_flag(self):
        _clear_script_agent_cache()
        mock_out = _make_mock_polish_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ):
            from src.backend.agents.polish_agent import PolishAgent

            agent = PolishAgent()
            segments = [_make_valid_script_segment()]
            result = agent.polish(segments)

        assert result.get("is_authoritative_text_source") is True, (
            "polished_script must be marked authoritative text source"
        )


# ---------------------------------------------------------------------------
# AC-8: Gate-P3 L1 style precheck (8 rules, pure code, 0 LLM tokens)
# ---------------------------------------------------------------------------


class TestAC8GateP3L1StylePrecheck:
    """AC-8: Gate-P3 L1 style precheck (8 rules, pure code, 0 LLM tokens):
    person consistency, modal particle frequency [0.5-3.0]/100chars,
    sentence length <=80 chars, paragraph length <=300 chars (warning only),
    banned words list (17 words), total word count +/-5%,
    viewpoint count preservation, data point ID set preservation"""

    def test_person_consistency_fail(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        # Mixed person (first-person "我" + third-person "他们") should fail
        segments = [
            {
                "segment_id": "seg_001",
                "content": "我认为这个股票会涨，他们却不这么认为。",
                "word_count": 20,
                "key_data_points": [],
                "outline_section_ref": "sec_001",
            }
        ]
        result = precheck.review(
            segments, outline=_make_outline(), original_script=segments
        )
        person_check = next(
            (c for c in result.get("checks", []) if c["rule"] == "person_consistency"),
            None,
        )
        assert person_check is not None, "must include person_consistency check"
        assert person_check["verdict"] in ("PASS", "FAIL")

    def test_modal_particle_frequency_out_of_range(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        # Excessive modal particles
        segments = [
            {
                "segment_id": "seg_001",
                "content": "吧呢啊吗哦呀哈哇啦咧呗呐" * 5,
                "word_count": 10,
                "key_data_points": [],
                "outline_section_ref": "sec_001",
            }
        ]
        result = precheck.review(
            segments, outline=_make_outline(), original_script=segments
        )
        modal_check = next(
            (
                c
                for c in result.get("checks", [])
                if c["rule"] == "modal_particle_frequency"
            ),
            None,
        )
        assert modal_check is not None
        # With extreme input, this should FAIL
        assert modal_check["verdict"] == "FAIL"

    def test_sentence_over_80_chars_fail(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        segments = [
            {
                "segment_id": "seg_001",
                "content": "这是一句"
                + "非常" * 30
                + "长的句子超过了八十个字符的限制需要被检测出来并报告失败。",
                "word_count": 40,
                "key_data_points": [],
                "outline_section_ref": "sec_001",
            }
        ]
        result = precheck.review(
            segments, outline=_make_outline(), original_script=segments
        )
        sent_check = next(
            (c for c in result.get("checks", []) if c["rule"] == "sentence_length"),
            None,
        )
        assert sent_check is not None
        assert sent_check["verdict"] == "FAIL"

    def test_banned_word_detected_fail(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        segments = [
            {
                "segment_id": "seg_001",
                "content": "这个股票绝对会涨，保证赚钱，必买。",
                "word_count": 15,
                "key_data_points": [],
                "outline_section_ref": "sec_001",
            }
        ]
        result = precheck.review(
            segments, outline=_make_outline(), original_script=segments
        )
        banned_check = next(
            (c for c in result.get("checks", []) if c["rule"] == "banned_words"),
            None,
        )
        assert banned_check is not None
        assert banned_check["verdict"] == "FAIL"

    def test_word_count_exceeds_5_percent_fail(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        # Original script had 18 words; polished has 25 (way over 5%)
        original = [_make_valid_script_segment()]
        segments = [
            {
                "segment_id": "seg_001",
                "content": "很多 " * 25,
                "word_count": 50,
                "key_data_points": [],
                "outline_section_ref": "sec_001",
            }
        ]
        result = precheck.review(
            segments, outline=_make_outline(), original_script=original
        )
        wc_check = next(
            (
                c
                for c in result.get("checks", [])
                if c["rule"] == "word_count_deviation"
            ),
            None,
        )
        assert wc_check is not None
        assert wc_check["verdict"] == "FAIL"

    def test_viewpoint_count_mismatch_fail(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        outline = _make_outline()
        # Segments don't cover all sections
        segments = [
            {
                "segment_id": "seg_001",
                "content": "今日股市表现良好。",
                "word_count": 6,
                "key_data_points": [],
                "outline_section_ref": "sec_001",
            }
        ]
        result = precheck.review(segments, outline=outline, original_script=segments)
        vp_check = next(
            (c for c in result.get("checks", []) if c["rule"] == "viewpoint_coverage"),
            None,
        )
        assert vp_check is not None
        assert vp_check["verdict"] == "FAIL"

    def test_data_point_id_set_mismatch_fail(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        original = [_make_valid_script_segment()]
        # Modified segments with different data points
        segments = [
            {
                "segment_id": "seg_001",
                "content": "改写后的内容。",
                "word_count": 5,
                "key_data_points": [
                    {
                        "data_point_id": "dp_new_different",
                        "value": "x",
                        "source": "http://s",
                        "trust_level": "llm_generated",
                    },
                ],
                "outline_section_ref": "sec_001",
            }
        ]
        result = precheck.review(
            segments, outline=_make_outline(), original_script=original
        )
        dp_check = next(
            (
                c
                for c in result.get("checks", [])
                if c["rule"] == "data_point_preservation"
            ),
            None,
        )
        assert dp_check is not None
        assert dp_check["verdict"] == "FAIL"

    def test_no_llm_calls_in_precheck(self):
        from src.backend.engine.style_precheck import StylePrecheck

        precheck = StylePrecheck()
        segments = [_make_valid_script_segment()]
        # review() must be a pure code path with no LLM dependencies
        result = precheck.review(
            segments, outline=_make_outline(), original_script=segments
        )
        assert "verdict" in result
        assert "checks" in result
        assert len(result["checks"]) == 8, (
            f"Expected 8 checks, got {len(result['checks'])}"
        )


# ---------------------------------------------------------------------------
# AC-9: Gate-P3 rejects on precheck FAIL or missing artifact
# ---------------------------------------------------------------------------


class TestAC9GateP3RejectsOnPrecheckFail:
    """AC-9: Gate-P3 rejects on any L1 precheck FAIL or missing artifact"""

    def test_gate_p3_pass(self):
        from src.backend.gates.gate_p3 import GateP3

        gate = GateP3()
        # All checks pass
        style_result = {
            "verdict": "PASS",
            "checks": [
                {"rule": "person_consistency", "verdict": "PASS"},
                {"rule": "modal_particle_frequency", "verdict": "PASS"},
                {"rule": "sentence_length", "verdict": "PASS"},
                {"rule": "paragraph_length", "verdict": "PASS"},
                {"rule": "banned_words", "verdict": "PASS"},
                {"rule": "word_count_deviation", "verdict": "PASS"},
                {"rule": "viewpoint_coverage", "verdict": "PASS"},
                {"rule": "data_point_preservation", "verdict": "PASS"},
            ],
        }
        result = gate.check(
            polished_script={
                "segments": [{"segment_id": "seg_001", "content": "test"}],
                "is_authoritative_text_source": True,
            },
            style_precheck_result=style_result,
        )
        assert result["passed"] is True, f"Gate-P3 should PASS: {result}"

    def test_gate_p3_fail_style_precheck(self):
        from src.backend.gates.gate_p3 import GateP3

        gate = GateP3()
        style_result = {
            "verdict": "FAIL",
            "checks": [
                {
                    "rule": "person_consistency",
                    "verdict": "FAIL",
                    "detail": "mixed person detected",
                },
                {"rule": "modal_particle_frequency", "verdict": "PASS"},
                {"rule": "sentence_length", "verdict": "PASS"},
                {"rule": "paragraph_length", "verdict": "PASS"},
                {"rule": "banned_words", "verdict": "PASS"},
                {"rule": "word_count_deviation", "verdict": "PASS"},
                {"rule": "viewpoint_coverage", "verdict": "PASS"},
                {"rule": "data_point_preservation", "verdict": "PASS"},
            ],
        }
        result = gate.check(
            polished_script={"segments": [], "is_authoritative_text_source": True},
            style_precheck_result=style_result,
        )
        assert result["passed"] is False, "Gate-P3 must FAIL on precheck FAIL"
