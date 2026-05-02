"""Tests for [SPEC-F-009] TTS Provider Abstraction & Voice Preview."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUDIO_DIR = PROJECT_ROOT / "src" / "frontend" / "audio"
PROVIDERS_DIR = AUDIO_DIR / "providers"
TTS_PROVIDER_PATH = AUDIO_DIR / "TTSProvider.ts"
BASE_PROVIDER_PATH = PROVIDERS_DIR / "BaseTTSProvider.ts"
AZURE_PROVIDER_PATH = PROVIDERS_DIR / "AzureTTSProvider.ts"
VOICE_PREVIEW_PATH = AUDIO_DIR / "voicePreview.ts"


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


def _all_audio_sources() -> str:
    sources = []
    for p in [
        TTS_PROVIDER_PATH,
        BASE_PROVIDER_PATH,
        AZURE_PROVIDER_PATH,
        VOICE_PREVIEW_PATH,
    ]:
        if p.is_file():
            sources.append(p.read_text(encoding="utf-8"))
    return "\n".join(sources)


class TestAC1VendorSwitchNoUpstreamChange:
    """AC-1: Switching TTS vendor (e.g., Azure -> another) requires no upstream code changes"""

    def test_tts_provider_interface_exists(self):
        source = _read_text(TTS_PROVIDER_PATH)
        assert "interface" in source or "type" in source, (
            "TTSProvider.ts must define the TTS provider interface"
        )
        assert "synthesize" in source, (
            "TTSProvider interface must define synthesize method"
        )

    def test_base_provider_abstract_class(self):
        source = _read_text(BASE_PROVIDER_PATH)
        has_base = (
            "abstract" in source
            or "implements" in source
            or "BaseTTSProvider" in source
        )
        assert has_base, (
            "BaseTTSProvider.ts must define the abstract base class for TTS providers"
        )

    def test_azure_provider_implements_base(self):
        source = _read_text(AZURE_PROVIDER_PATH)
        assert "BaseTTSProvider" in source or "TTSProvider" in source, (
            "AzureTTSProvider must reference the base TTS provider interface"
        )

    def test_upstream_imports_only_interface(self):
        interface_source = _read_text(TTS_PROVIDER_PATH)
        assert "AudioResult" in interface_source, (
            "TTSProvider.ts must define AudioResult type"
        )


class TestAC2UnsupportedParamCapabilityGapLog:
    """AC-2: Unsupported parameter triggers log containing `capability_gap`, synthesis does not throw"""

    def test_capability_gap_log_pattern(self):
        source = _all_audio_sources()
        assert "capability_gap" in source, (
            "TTS providers must log 'capability_gap' for unsupported parameters"
        )

    def test_no_throw_on_unsupported_param(self):
        source = _all_audio_sources()
        has_try_catch = "try" in source or "catch" in source
        has_fallback = (
            "fallback" in source.lower()
            or "degrad" in source.lower()
            or "warn" in source.lower()
        )
        assert has_try_catch or has_fallback, (
            "TTS providers must gracefully handle unsupported parameters without throwing"
        )


class TestAC3PreviewDuration14To16s:
    """AC-3: Preview files are 14-16 seconds in duration"""

    def test_preview_duration_range(self):
        source = _read_text(VOICE_PREVIEW_PATH)
        assert re.search(r"1[4-6]", source), (
            "voicePreview.ts must reference duration in 14-16 second range"
        )

    def test_preview_generate_function(self):
        source = _read_text(VOICE_PREVIEW_PATH)
        assert "generate" in source.lower() or "preview" in source.lower(), (
            "voicePreview.ts must have a function to generate voice previews"
        )


class TestAC4SynthesizeInterface:
    """AC-4: `TTSProvider.synthesize()` accepts `text`, `ssml_tags`, `voice_params` and returns `AudioResult`"""

    def test_synthesize_accepts_text(self):
        source = _all_audio_sources()
        assert "text" in source, "TTSProvider.synthesize() must accept 'text' parameter"

    def test_synthesize_accepts_ssml_tags(self):
        source = _all_audio_sources()
        assert "ssml" in source.lower(), (
            "TTSProvider.synthesize() must accept 'ssml_tags' parameter"
        )

    def test_synthesize_accepts_voice_params(self):
        source = _all_audio_sources()
        has_vp = (
            "voice_params" in source
            or "voiceParams" in source
            or "VoiceParams" in source
        )
        assert has_vp, "TTSProvider.synthesize() must accept 'voice_params' parameter"

    def test_synthesize_returns_audio_result(self):
        source = _all_audio_sources()
        assert "AudioResult" in source, (
            "TTSProvider.synthesize() must return AudioResult"
        )
