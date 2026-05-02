"""Tests for preflight check implementations."""

from src.backend.core.preflight import (
    DEFAULT_RUNNERS,
    _check_llm,
    _check_sqlite,
    _check_tts,
    _check_media_dir,
)


def test_llm_check():
    """LLM check should verify import + config."""
    result = _check_llm()
    assert result.status in ("ok", "degraded"), f"Unexpected: {result.status}"


def test_sqlite_check():
    """SQLite check should connect and SELECT 1."""
    result = _check_sqlite()
    assert result.status == "ok", f"SQLite check failed: {result.message}"


def test_tts_check():
    """TTS check should verify importability."""
    result = _check_tts()
    assert result.status in ("ok", "degraded"), f"Unexpected: {result.status}"


def test_media_dir_check():
    """Media dir check should create directory."""
    result = _check_media_dir()
    assert result.status == "ok", f"Media dir check failed: {result.message}"


def test_all_nine_runners_registered():
    """All 9 checks must be registered in DEFAULT_RUNNERS."""
    expected = {
        "llm", "llm_review", "tts", "sqlite", "media_dir",
        "web_search", "material", "bgm", "financial_data",
    }
    assert set(DEFAULT_RUNNERS.keys()) == expected
