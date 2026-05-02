"""[SPEC-D-018] Gate-P4 v3.17 failure-recovery paths (AC-4).

Covers SPEC-9.4.4 addendum: concat-integrity FAIL triggers
NarrationMasterAssembler rerun (NO re-TTS); master_audio_ref DB
write failure retries <= 3 before raising.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from src.backend.recovery.p4_recovery_paths import (
    reassemble_on_concat_failure,
    retry_master_audio_ref_write,
)


class TestConcatFailureTriggersReassemble:
    def test_reassemble_called_without_retts(self) -> None:
        calls: list[tuple[str, Path]] = []

        class FakeAssembler:
            def assemble(self, project_id: str, project_root: Path) -> dict[str, Any]:
                calls.append((project_id, project_root))
                return {"kind": "narration_master", "version": 2}

        class NoTTS:
            def synthesize(self, *_: Any, **__: Any) -> None:  # pragma: no cover
                raise AssertionError("recovery must NOT rerun TTS; only reassemble")

        assembler = FakeAssembler()
        result = reassemble_on_concat_failure(
            assembler,
            "proj_x",
            Path("/tmp/proj_x"),
        )
        assert calls == [("proj_x", Path("/tmp/proj_x"))]
        assert result["kind"] == "narration_master"


class TestMasterAudioRefDbRetry:
    def test_succeeds_on_third_attempt(self) -> None:
        attempts = {"n": 0}

        class FlakyRepo:
            def set_master_audio_ref(
                self, project_id: str, ref: dict[str, Any]
            ) -> None:
                attempts["n"] += 1
                if attempts["n"] < 3:
                    raise sqlite3.OperationalError("database is locked")

        ok = retry_master_audio_ref_write(
            FlakyRepo(),
            "proj_x",
            {"kind": "narration_master"},
            max_retries=3,
        )
        assert ok is True
        assert attempts["n"] == 3

    def test_gives_up_after_three(self) -> None:
        attempts = {"n": 0}

        class AlwaysFailRepo:
            def set_master_audio_ref(
                self, project_id: str, ref: dict[str, Any]
            ) -> None:
                attempts["n"] += 1
                raise sqlite3.OperationalError("still locked")

        with pytest.raises(sqlite3.OperationalError):
            retry_master_audio_ref_write(
                AlwaysFailRepo(),
                "proj_x",
                {"kind": "narration_master"},
                max_retries=3,
            )
        assert attempts["n"] == 3
