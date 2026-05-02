"""[FEAT-TTS] ByteDanceTTSProvider — real TTS via ByteDance OpenSpeech API.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.4.7 (provider abstraction)
+ tasks/DEV-HANDOFF-TTS-AND-SPEC-G.md §3 (concrete provider implementation).

Subclasses TTSProvider so callers receive the same `{audio_path,
duration_seconds, sample_rate}` shape regardless of whether the real API
or the stub fallback handled the call. On any error path (missing creds,
network failure, non-success response code) the call degrades to a
stub-style result with ``fallback=True`` rather than raising — the P4
pipeline must not break end-to-end when TTS is misconfigured.

[SPEC-D-005] Audio defaults read from config/platform_profiles.json
bilibili.audio; voice_params override individual keys when present.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict

from src.backend.services.tts_provider import TTSProvider, _load_platform_audio_config

_API_URL = "https://openspeech.bytedance.com/api/v1/tts"
_DEFAULT_VOICE_TYPE = "BV001_streaming"
_DEFAULT_CLUSTER = "volcano_tts"
_REQUEST_TIMEOUT_SEC = 30
_SUCCESS_CODE = 3000
_DEFAULT_AUDIO_DIR = "data/audio"

_logger = logging.getLogger(__name__)


class ByteDanceTTSProvider(TTSProvider):
    """Real TTS provider backed by ByteDance OpenSpeech.

    Env contract:
      - BYTEDANCE_TTS_APP_ID
      - BYTEDANCE_TTS_ACCESS_TOKEN
      - AVS_AUDIO_DIR (optional; default "data/audio")
    """

    def synthesize(
        self,
        *,
        text: str,
        voice_params: Dict[str, Any],
        ssml_tags: str | None = None,
    ) -> Dict[str, Any]:
        # Reuse the abstract parent's capability_gap logging for unsupported keys.
        super().synthesize(text=text, voice_params=voice_params, ssml_tags=ssml_tags)

        app_id = os.environ.get("BYTEDANCE_TTS_APP_ID")
        access_token = os.environ.get("BYTEDANCE_TTS_ACCESS_TOKEN")
        if not app_id or not access_token:
            _logger.warning(
                "bytedance_tts.missing_env: degrading to stub fallback"
            )
            return self._fallback(text, reason="missing_env")

        body = self._build_body(
            app_id=app_id,
            access_token=access_token,
            text=text,
            voice_params=voice_params,
            ssml_tags=ssml_tags,
        )
        try:
            payload = self._post(access_token=access_token, body=body)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            _logger.warning("bytedance_tts.api_error: %s", exc)
            return self._fallback(text, reason="api_error")

        if not isinstance(payload, dict) or payload.get("code") != _SUCCESS_CODE:
            _logger.warning(
                "bytedance_tts.non_success_code: code=%s message=%s",
                payload.get("code") if isinstance(payload, dict) else None,
                payload.get("message") if isinstance(payload, dict) else None,
            )
            return self._fallback(text, reason="non_success_code")

        audio_b64 = payload.get("data") or payload.get("audio")
        if not isinstance(audio_b64, str):
            _logger.warning("bytedance_tts.missing_audio_payload")
            return self._fallback(text, reason="missing_audio")

        audio_bytes = base64.b64decode(audio_b64)
        audio_path = self._write_audio_file(text=text, audio_bytes=audio_bytes)

        duration_ms = payload.get("duration")
        duration_sec = (
            float(duration_ms) / 1000.0
            if isinstance(duration_ms, (int, float)) and duration_ms > 0
            else self._estimate_duration(text)
        )

        # Resolve audio params: platform defaults + voice_params overrides
        audio_defaults = _load_platform_audio_config()
        sample_rate = voice_params.get("sample_rate", audio_defaults.get("sample_rate", 44100))
        channels = voice_params.get("channels", audio_defaults.get("channels", 2))

        return {
            "audio_path": str(audio_path),
            "duration_seconds": round(duration_sec, 2),
            "sample_rate": sample_rate,
            "channels": channels,
        }

    # -- helpers ----------------------------------------------------------

    def _build_body(
        self,
        *,
        app_id: str,
        access_token: str,
        text: str,
        voice_params: Dict[str, Any],
        ssml_tags: str | None,
    ) -> bytes:
        voice_type = voice_params.get("voice_id") or _DEFAULT_VOICE_TYPE
        cluster = voice_params.get("cluster") or os.environ.get(
            "BYTEDANCE_TTS_CLUSTER", _DEFAULT_CLUSTER
        )
        rate_wpm = float(voice_params.get("rate_wpm", 160.0))
        speed_ratio = round(rate_wpm / 160.0, 3)
        volume_ratio = float(voice_params.get("volume", 1.0))
        pitch_ratio = float(voice_params.get("pitch", 1.0))
        body: Dict[str, Any] = {
            "app": {
                "appid": app_id,
                "token": access_token,
                "cluster": cluster,
            },
            "user": {"uid": "avs"},
            "audio": {
                "voice_type": voice_type,
                "encoding": "mp3",
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": ssml_tags or text,
                "operation": "query",
                "text_type": "ssml" if ssml_tags else "plain",
            },
        }
        return json.dumps(body, ensure_ascii=False).encode("utf-8")

    def _post(self, *, access_token: str, body: bytes) -> Any:
        req = urllib.request.Request(
            _API_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer;{access_token}",
            },
        )
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_SEC) as resp:
            raw = resp.read()
        return json.loads(raw)

    def _write_audio_file(self, *, text: str, audio_bytes: bytes) -> Path:
        out_dir = Path(os.environ.get("AVS_AUDIO_DIR", _DEFAULT_AUDIO_DIR))
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"seg_audio_{hash(text) & 0xFFFF:04x}.mp3"
        path = out_dir / filename
        path.write_bytes(audio_bytes)
        return path

    def _estimate_duration(self, text: str) -> float:
        return max(1.0, len(text) / 3.0)

    def _fallback(self, text: str, *, reason: str) -> Dict[str, Any]:
        return {
            "audio_path": f"phase_4/seg_audio_{hash(text) & 0xFFFF:04x}.mp3",
            "duration_seconds": round(self._estimate_duration(text), 2),
            "sample_rate": self._resolve_audio_default("sample_rate"),
            "channels": self._resolve_audio_default("channels"),
            "fallback": True,
            "fallback_reason": reason,
        }

    def _resolve_audio_default(self, key: str) -> Any:
        """Read the platform audio default for *key* from config."""
        audio_defaults = _load_platform_audio_config()
        return audio_defaults.get(key) if audio_defaults else None
