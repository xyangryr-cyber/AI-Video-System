"""[SPEC-D-005] Tests: TTS audio params aligned with platform standards.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.4.7
"""

from __future__ import annotations

from unittest.mock import patch

from src.backend.services.tts_provider import TTSProvider
from src.backend.services.bytedance_tts_provider import ByteDanceTTSProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _platform_defaults() -> dict:
    """Return a dict matching bilibili.audio in platform_profiles.json."""
    return {"sample_rate": 44100, "channels": 2, "bitrate": "192k"}


# ---------------------------------------------------------------------------
# TTSProvider (abstract base / stub)
# ---------------------------------------------------------------------------

class TestTTSProviderPlatformParams:
    """Verify that TTSProvider.synthesize() uses platform defaults and
    respects voice_params overrides."""

    def test_uses_platform_default_audio_params(self):
        """When voice_params has no overrides, bilibili audio defaults are used."""
        defaults = _platform_defaults()
        with patch(
            "src.backend.services.tts_provider._load_platform_audio_config",
            return_value=defaults,
        ):
            provider = TTSProvider()
            result = provider.synthesize(text="Hello world", voice_params={})
        assert result["sample_rate"] == 44100
        assert result["channels"] == 2

    def test_voice_params_override_platform_defaults(self):
        """When voice_params specifies sample_rate/channels, those take priority."""
        defaults = _platform_defaults()
        with patch(
            "src.backend.services.tts_provider._load_platform_audio_config",
            return_value=defaults,
        ):
            provider = TTSProvider()
            result = provider.synthesize(
                text="Hello world", voice_params={"sample_rate": 48000, "channels": 1}
            )
        assert result["sample_rate"] == 48000
        assert result["channels"] == 1

    def test_partial_override_falls_back_to_platform_default(self):
        """When only one param is overridden, the other falls back to platform default."""
        defaults = _platform_defaults()
        with patch(
            "src.backend.services.tts_provider._load_platform_audio_config",
            return_value=defaults,
        ):
            provider = TTSProvider()
            result = provider.synthesize(
                text="Hello world", voice_params={"sample_rate": 48000}
            )
        assert result["sample_rate"] == 48000
        assert result["channels"] == 2  # platform default


# ---------------------------------------------------------------------------
# ByteDanceTTSProvider (real provider)
# ---------------------------------------------------------------------------

class TestByteDanceTTSProviderPlatformParams:
    """Verify that ByteDanceTTSProvider also uses platform defaults and
    respects voice_params overrides."""

    def test_uses_platform_default_audio_params(self, monkeypatch):
        """When voice_params has no overrides, the response uses platform defaults."""
        defaults = _platform_defaults()
        monkeypatch.setattr(
            "src.backend.services.bytedance_tts_provider._load_platform_audio_config",
            lambda: defaults,
        )
        monkeypatch.setenv("BYTEDANCE_TTS_APP_ID", "test_app_id")
        monkeypatch.setenv("BYTEDANCE_TTS_ACCESS_TOKEN", "test_token")

        provider = ByteDanceTTSProvider()
        fake_audio_b64 = "AAAA"
        with patch.object(provider, "_post", return_value={
            "code": 3000,
            "data": fake_audio_b64,
            "duration": 2000,
        }):
            result = provider.synthesize(text="Hello world", voice_params={})

        assert result["sample_rate"] == 44100
        assert result.get("channels") == 2

    def test_voice_params_override_platform_defaults(self, monkeypatch):
        """When voice_params specifies sample_rate/channels, those take priority."""
        defaults = _platform_defaults()
        monkeypatch.setattr(
            "src.backend.services.bytedance_tts_provider._load_platform_audio_config",
            lambda: defaults,
        )
        monkeypatch.setenv("BYTEDANCE_TTS_APP_ID", "test_app_id")
        monkeypatch.setenv("BYTEDANCE_TTS_ACCESS_TOKEN", "test_token")

        provider = ByteDanceTTSProvider()
        fake_audio_b64 = "AAAA"
        with patch.object(provider, "_post", return_value={
            "code": 3000,
            "data": fake_audio_b64,
            "duration": 2000,
        }):
            result = provider.synthesize(
                text="Hello world",
                voice_params={"sample_rate": 48000, "channels": 1},
            )

        assert result["sample_rate"] == 48000
        assert result["channels"] == 1

    def test_fallback_still_returns_platform_defaults(self, monkeypatch):
        """When API call fails (missing env), fallback result still uses platform defaults."""
        defaults = _platform_defaults()
        monkeypatch.setattr(
            "src.backend.services.bytedance_tts_provider._load_platform_audio_config",
            lambda: defaults,
        )
        monkeypatch.delenv("BYTEDANCE_TTS_APP_ID", raising=False)
        monkeypatch.delenv("BYTEDANCE_TTS_ACCESS_TOKEN", raising=False)

        provider = ByteDanceTTSProvider()
        result = provider.synthesize(text="Hello world", voice_params={})

        assert result.get("fallback") is True
        assert result["sample_rate"] == 44100
        assert result.get("channels") == 2
