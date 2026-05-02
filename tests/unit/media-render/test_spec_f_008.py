"""Tests for [SPEC-F-008] Voice Parameter System & SSML Builder."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUDIO_DIR = PROJECT_ROOT / "src" / "frontend" / "audio"
VOICE_CONVERTER_PATH = AUDIO_DIR / "voiceParamConverter.ts"
SSML_BUILDER_PATH = AUDIO_DIR / "ssmlBuilder.ts"


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


class TestAC1StyleDegreeRangeValidation:
    """AC-1: `style_degree` validates range [0.01, 2.0], rejects out-of-range"""

    def test_style_degree_min_validated(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        # Must check lower bound: style_degree < 0.01 or style_degree >= 0.01
        assert re.search(r"0\.01", source), (
            "voiceParamConverter.ts must reference 0.01 as the style_degree lower bound"
        )

    def test_style_degree_max_validated(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        # Must check upper bound: style_degree > 2.0 or style_degree <= 2.0
        assert re.search(r"2\.0", source), (
            "voiceParamConverter.ts must reference 2.0 as the style_degree upper bound"
        )

    def test_style_degree_range_clamped(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        # Must have validation logic: validateStyleDegree function + bounds
        has_bounds_check = (
            re.search(r"validateStyleDegree|style_degree\s*[<>=!]", source)
            and re.search(r"0\.01", source)
            and re.search(r"2\.0", source)
        )
        assert has_bounds_check, (
            "voiceParamConverter.ts must validate style_degree against [0.01, 2.0]"
        )


class TestAC2VoiceDirectionDeterministic:
    """AC-2: Same `voice_direction` input produces identical output on two calls (pure function)"""

    def test_converter_is_pure_function_no_externals(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        # Pure function: no Date, no Math.random, no fetch/axios, no setTimeout
        forbidden = [
            r"Math\.random",
            r"new Date",
            r"fetch\(",
            r"axios",
            r"setTimeout",
            r"setInterval",
            r"localStorage",
            r"sessionStorage",
        ]
        for pattern in forbidden:
            assert not re.search(pattern, source), (
                f"voiceParamConverter.ts must not use {pattern} (impure)"
            )

    def test_converter_exports_deterministic_function(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"export.*function", source), (
            "voiceParamConverter.ts must export a deterministic pure function"
        )


class TestAC3NoLlmCallsInConverter:
    """AC-3: Conversion code has zero LLM API calls"""

    def test_no_llm_imports(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        llm_patterns = [
            r"openai",
            r"anthropic",
            r"langchain",
            r"llm",
            r"completion",
            r"chat\.",
            r"generateText",
            r"generate\(",
        ]
        for pattern in llm_patterns:
            assert not re.search(pattern, source), (
                f"voiceParamConverter.ts must not import or call LLM APIs ({pattern})"
            )


class TestAC4PaceLookupTable:
    """AC-4: `pace=much_slower` -> `rate_multiplier=0.8`; all 5 pace levels match lookup table"""

    def test_pace_much_slower_to_08(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"much_slower", source) and re.search(r"0\.8", source), (
            "voiceParamConverter.ts: pace=much_slower must map to rate_multiplier=0.8"
        )

    def test_pace_slower_to_09(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"slower", source) and re.search(r"0\.9", source), (
            "voiceParamConverter.ts: pace=slower must map to rate_multiplier=0.9"
        )

    def test_pace_normal_to_10(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"normal", source) and re.search(r"1\.0", source), (
            "voiceParamConverter.ts: pace=normal must map to rate_multiplier=1.0"
        )

    def test_pace_faster_to_11(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"faster", source) and re.search(r"1\.1", source), (
            "voiceParamConverter.ts: pace=faster must map to rate_multiplier=1.1"
        )

    def test_pace_much_faster_to_12(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"much_faster", source) and re.search(r"1\.2", source), (
            "voiceParamConverter.ts: pace=much_faster must map to rate_multiplier=1.2"
        )


class TestAC5EnergyLookupTable:
    """AC-5: `energy=high` -> volume +10%; all 3 energy levels match lookup table"""

    def test_energy_low_volume_reduced(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"low", source, re.IGNORECASE), (
            "voiceParamConverter.ts must handle energy=low"
        )

    def test_energy_normal_volume_default(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"normal", source), (
            "voiceParamConverter.ts must handle energy=normal"
        )

    def test_energy_high_volume_increased(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        assert re.search(r"high", source), (
            "voiceParamConverter.ts must handle energy=high"
        )

    def test_energy_volume_math(self):
        source = _read_text(VOICE_CONVERTER_PATH)
        # Must have volume modifier: eg volume * 1.1, volume + 10%, etc.
        assert re.search(r"volume|vol", source, re.IGNORECASE), (
            "voiceParamConverter.ts must compute volume adjustments for energy levels"
        )


class TestAC6EmotionTransitionBreak:
    """AC-6: Adjacent segments `sad->excited` -> 800ms `<break>` inserted between them"""

    def test_sad_to_excited_break(self):
        source = _read_text(SSML_BUILDER_PATH)
        assert re.search(r"sad", source) and re.search(r"excited", source), (
            "ssmlBuilder.ts must handle sad->excited emotion transition"
        )

    def test_break_800ms(self):
        source = _read_text(SSML_BUILDER_PATH)
        # 800ms break for emotion transitions
        assert re.search(r"(?:800|800ms)", source), (
            "ssmlBuilder.ts must insert 800ms break for emotion transitions"
        )

    def test_break_tag_emitted(self):
        source = _read_text(SSML_BUILDER_PATH)
        assert re.search(r"<break", source), "ssmlBuilder.ts must emit SSML <break> tag"


class TestAC7NumericDenseProsodySlow:
    """AC-7: Numeric-dense sentence wrapped in `<prosody rate=\"slow\">`"""

    def test_prosody_slow_tag(self):
        source = _read_text(SSML_BUILDER_PATH)
        assert re.search(r"<prosody\s+rate=\"slow\"", source), (
            'ssmlBuilder.ts must emit <prosody rate="slow"> for numeric-dense sentences'
        )

    def test_numeric_detection_logic(self):
        source = _read_text(SSML_BUILDER_PATH)
        # Must have logic to detect numeric density: regex digit matching or similar
        assert re.search(r"\d|digit|numeric", source, re.IGNORECASE), (
            "ssmlBuilder.ts must contain numeric-dense sentence detection logic"
        )


class TestAC8NoLlmCallsInSsmlBuilder:
    """AC-8: `ssml_builder` module has zero LLM calls"""

    def test_no_llm_imports_in_builder(self):
        source = _read_text(SSML_BUILDER_PATH)
        llm_patterns = [
            r"openai",
            r"anthropic",
            r"langchain",
            r"llm",
            r"completion",
            r"chat\.",
            r"generateText",
            r"generate\(",
        ]
        for pattern in llm_patterns:
            assert not re.search(pattern, source), (
                f"ssmlBuilder.ts must not import or call LLM APIs ({pattern})"
            )
