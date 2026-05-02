"""[FEAT-TTS] ByteDanceTTSProvider — real HTTP TTS provider tests.

5 acceptance criteria:
- AC-1: synthesize() returns an audio_path pointing to a real file on disk.
- AC-2: HTTP request includes the correct Authorization header
        (`Bearer;{access_token}` per ByteDance OpenSpeech docs).
- AC-3: Missing env vars degrade gracefully — synthesize() returns stub-style
        result without raising, and logs a capability_gap.
- AC-4: HTTP/API errors degrade gracefully — synthesize() returns stub-style
        result without raising.
- AC-5: Chinese text is correctly UTF-8 encoded in the JSON request body.
"""

from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def env_with_creds(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("BYTEDANCE_TTS_APP_ID", "9061824843")
    monkeypatch.setenv(
        "BYTEDANCE_TTS_ACCESS_TOKEN", "JDkdzY8awzQ_65UlrTzglP-ndxQ7Y9AH"
    )
    monkeypatch.setenv("BYTEDANCE_TTS_SECRET_KEY", "eiUEr9CdvWmTw0-vS0A_tJZNMWRgleVB")
    monkeypatch.setenv("AVS_AUDIO_DIR", str(tmp_path))
    return tmp_path


def _fake_response(payload: dict[str, object]) -> io.BytesIO:
    return io.BytesIO(json.dumps(payload).encode("utf-8"))


class TestAC1RealAudioFileWritten:
    def test_synthesize_writes_audio_bytes_to_disk(
        self, env_with_creds: Path
    ) -> None:
        from src.backend.services.bytedance_tts_provider import (
            ByteDanceTTSProvider,
        )

        audio_bytes = b"\xff\xfb\x90\x00synthesized-mp3-bytes"
        payload = {
            "code": 3000,
            "data": base64.b64encode(audio_bytes).decode("ascii"),
            "duration": 1500,
        }

        with patch.object(urllib.request, "urlopen") as mocked:
            mocked.return_value.__enter__.return_value = _fake_response(payload)
            provider = ByteDanceTTSProvider()
            result = provider.synthesize(
                text="hello",
                voice_params={"voice_id": "BV001_streaming"},
            )

        audio_path = Path(result["audio_path"])
        assert audio_path.exists(), audio_path
        assert audio_path.read_bytes() == audio_bytes
        assert result["duration_seconds"] > 0
        assert result["sample_rate"] == 24000


class TestAC2AuthorizationHeader:
    def test_request_uses_bearer_semicolon_access_token(
        self, env_with_creds: Path
    ) -> None:
        from src.backend.services.bytedance_tts_provider import (
            ByteDanceTTSProvider,
        )

        payload = {
            "code": 3000,
            "data": base64.b64encode(b"x").decode("ascii"),
            "duration": 1000,
        }
        captured: dict[str, urllib.request.Request] = {}

        def fake_urlopen(req, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            captured["req"] = req
            return _ContextStub(_fake_response(payload))

        with patch.object(urllib.request, "urlopen", new=fake_urlopen):
            ByteDanceTTSProvider().synthesize(
                text="hi", voice_params={"voice_id": "v"}
            )

        req = captured["req"]
        assert (
            req.get_header("Authorization")
            == "Bearer;JDkdzY8awzQ_65UlrTzglP-ndxQ7Y9AH"
        )
        assert req.get_header("Content-type") == "application/json"
        body = json.loads(req.data.decode("utf-8"))
        assert body["app"]["appid"] == "9061824843"
        assert body["app"]["token"] == "JDkdzY8awzQ_65UlrTzglP-ndxQ7Y9AH"
        assert body["request"]["operation"] == "query"


class TestAC3GracefulFallbackOnMissingEnv:
    def test_missing_env_vars_returns_stub_without_raising(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        for var in (
            "BYTEDANCE_TTS_APP_ID",
            "BYTEDANCE_TTS_ACCESS_TOKEN",
            "BYTEDANCE_TTS_SECRET_KEY",
        ):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("AVS_AUDIO_DIR", str(tmp_path))

        from src.backend.services.bytedance_tts_provider import (
            ByteDanceTTSProvider,
        )

        with patch.object(urllib.request, "urlopen") as mocked:
            result = ByteDanceTTSProvider().synthesize(
                text="hi", voice_params={"voice_id": "v"}
            )
            assert mocked.call_count == 0, "should not call API when creds missing"

        assert "audio_path" in result
        assert result["duration_seconds"] >= 1.0
        assert result.get("fallback") is True


class TestAC4GracefulFallbackOnApiError:
    def test_api_error_returns_stub_without_raising(
        self, env_with_creds: Path
    ) -> None:
        from src.backend.services.bytedance_tts_provider import (
            ByteDanceTTSProvider,
        )

        def boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise urllib.error.URLError("connection refused")

        with patch.object(urllib.request, "urlopen", new=boom):
            result = ByteDanceTTSProvider().synthesize(
                text="hi", voice_params={"voice_id": "v"}
            )

        assert "audio_path" in result
        assert result.get("fallback") is True

    def test_non_success_response_code_returns_stub(
        self, env_with_creds: Path
    ) -> None:
        from src.backend.services.bytedance_tts_provider import (
            ByteDanceTTSProvider,
        )

        payload = {"code": 3001, "message": "resource not granted"}

        with patch.object(urllib.request, "urlopen") as mocked:
            mocked.return_value.__enter__.return_value = _fake_response(payload)
            result = ByteDanceTTSProvider().synthesize(
                text="hi", voice_params={"voice_id": "v"}
            )

        assert "audio_path" in result
        assert result.get("fallback") is True


class TestAC5ChineseTextEncoding:
    def test_chinese_text_serialised_as_utf8_unicode(
        self, env_with_creds: Path
    ) -> None:
        from src.backend.services.bytedance_tts_provider import (
            ByteDanceTTSProvider,
        )

        payload = {
            "code": 3000,
            "data": base64.b64encode(b"x").decode("ascii"),
            "duration": 1000,
        }
        captured: dict[str, urllib.request.Request] = {}

        def fake_urlopen(req, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            captured["req"] = req
            return _ContextStub(_fake_response(payload))

        with patch.object(urllib.request, "urlopen", new=fake_urlopen):
            ByteDanceTTSProvider().synthesize(
                text="欢迎使用AI视频制作系统",
                voice_params={"voice_id": "BV001_streaming"},
            )

        body = json.loads(captured["req"].data.decode("utf-8"))
        assert body["request"]["text"] == "欢迎使用AI视频制作系统"
        assert body["app"]["appid"] == "9061824843"


class _ContextStub:
    """Minimal context-manager wrapper around a body stream."""

    def __init__(self, stream: io.BytesIO) -> None:
        self._stream = stream

    def __enter__(self) -> io.BytesIO:
        return self._stream

    def __exit__(self, *args: object) -> None:
        return None
