"""[SPEC-D-018] Gate-P4 failure-recovery paths (SPEC-9.4.4 v3.17 addendum).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §D-AUDP7A-1 AC-4.

Two recovery paths triggered by Gate-P4 FAIL:

* :func:`reassemble_on_concat_failure` -- concat-integrity FAIL routes
  to :class:`NarrationMasterAssembler` for a pure re-concat (no TTS
  rerun). The recovery path accepts any assembler with an
  ``assemble(project_id, project_root)`` method so tests can substitute
  a fake without pulling ffmpeg into the unit suite.

* :func:`retry_master_audio_ref_write` -- flaky ``projects.master_audio_ref``
  UPDATEs retry up to ``max_retries`` times (default 3). On the final
  failure the underlying ``sqlite3.Error`` is re-raised so the caller
  knows the write was not persisted.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Mapping, Protocol


logger = logging.getLogger(__name__)


__all__ = [
    "Assembler",
    "MasterAudioRefRepo",
    "reassemble_on_concat_failure",
    "retry_master_audio_ref_write",
]


class Assembler(Protocol):
    """Minimal protocol satisfied by NarrationMasterAssembler (SPEC-C-016)."""

    def assemble(
        self, project_id: str, project_root: Path
    ) -> Any: ...  # pragma: no cover


class MasterAudioRefRepo(Protocol):
    """Minimal protocol satisfied by ProjectStateRepository (SPEC-C-016)."""

    def set_master_audio_ref(
        self, project_id: str, ref: Mapping[str, Any]
    ) -> None: ...  # pragma: no cover


def reassemble_on_concat_failure(
    assembler: Assembler,
    project_id: str,
    project_root: Path,
) -> Any:
    """Re-run the P4 master assembler (no TTS) after concat FAIL.

    The caller is expected to have failed Gate-P4 on ``concat_integrity``.
    This path deliberately DOES NOT invoke TTSProvider -- v3.17 AC-4 says
    "(不重 TTS)".
    """
    logger.info(
        "gate_p4.recovery.reassemble project_id=%s root=%s",
        project_id,
        str(project_root),
    )
    return assembler.assemble(project_id, Path(project_root))


def retry_master_audio_ref_write(
    repo: MasterAudioRefRepo,
    project_id: str,
    ref: Mapping[str, Any],
    *,
    max_retries: int = 3,
    sleep_seconds: float = 0.0,
) -> bool:
    """UPDATE ``projects.master_audio_ref`` with up to ``max_retries`` attempts.

    Returns ``True`` on success. Re-raises the final ``sqlite3.Error`` if
    all ``max_retries`` attempts fail so the caller can surface the
    error (and trigger the outer recovery path, e.g. Gate FAIL).
    """
    if max_retries < 1:
        raise ValueError(f"max_retries must be >= 1, got {max_retries}")
    last_exc: sqlite3.Error | None = None
    for attempt in range(1, max_retries + 1):
        try:
            repo.set_master_audio_ref(project_id, ref)
            return True
        except sqlite3.Error as exc:
            last_exc = exc
            logger.warning(
                "gate_p4.recovery.db_retry attempt=%d/%d err=%s",
                attempt,
                max_retries,
                exc,
            )
            if attempt == max_retries:
                break
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
    assert last_exc is not None
    raise last_exc
