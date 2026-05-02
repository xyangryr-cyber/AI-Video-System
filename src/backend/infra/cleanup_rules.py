"""Archive / cleanup classification rules ([SPEC-B-014]).

Authority:
  docs/specs/SPEC-B-infra-deploy.md §1.3 backup policy, §15 cleanup task.
  docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-2 items 2+3.

Rules implemented here:

* AC-3 WHITELIST (kept on archive):
    - phase_4/narration_master.{mp3,json}
    - phase_5/bgm_mix_master.{mp3,json}
    - phase_6/final_audio_with_bgm_sfx.{mp3,json}
    - phase_7a/chart_materials/**

* AC-4 BLACKLIST (removed on archive):
    - phase_5/bgm_candidates/**
    - phase_5/bgm_mix_preview_*.mp3
    - phase_6/sfx_applied_segments/**

* AC-2 BACKUP CLASSIFICATION:
    - OSS async archive target: phase_7a/verified_materials/
    - Local-only (never uploaded): phase_5/bgm_mix_preview_*.mp3 and
      phase_6/sfx_applied_segments/

Anything not matched by blacklist defaults to KEEP, so v3.15 artifacts
(phase_0..phase_11 existing files) survive archive without per-file rules.
"""

from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# AC-3 whitelist (explicit keep). Directories end with "/"; files are literals.
ARCHIVE_WHITELIST_PATTERNS: Tuple[str, ...] = (
    "phase_4/narration_master.mp3",
    "phase_4/narration_master.json",
    "phase_5/bgm_mix_master.mp3",
    "phase_5/bgm_mix_master.json",
    "phase_6/final_audio_with_bgm_sfx.mp3",
    "phase_6/final_audio_with_bgm_sfx.json",
    "phase_7a/chart_materials/",
)

# AC-4 blacklist (explicit delete).
ARCHIVE_BLACKLIST_PATTERNS: Tuple[str, ...] = (
    "phase_5/bgm_candidates/",
    "phase_5/bgm_mix_preview_*.mp3",
    "phase_6/sfx_applied_segments/",
)

# AC-2 backup classification.
OSS_ASYNC_ARCHIVE_PATHS: Tuple[str, ...] = ("phase_7a/verified_materials/",)
LOCAL_ONLY_PATHS: Tuple[str, ...] = (
    "phase_5/bgm_mix_preview_*.mp3",
    "phase_6/sfx_applied_segments/",
)


def _matches(rel_path: str, pattern: str) -> bool:
    """Match a POSIX-style ``rel_path`` against a whitelist/blacklist pattern.

    Directory patterns end with ``/`` and match any descendant.
    Glob patterns are fnmatch-style (``*`` matches within a path segment).
    """
    if pattern.endswith("/"):
        prefix = pattern  # "phase_5/bgm_candidates/"
        return rel_path == prefix.rstrip("/") or rel_path.startswith(prefix)
    return fnmatch.fnmatch(rel_path, pattern)


def classify_path(rel_path: str) -> str:
    """Classify a project-relative path.

    Returns ``"delete"`` when the path is in the archive blacklist,
    ``"keep"`` when it is in the whitelist, ``"unknown"`` otherwise.

    Archive callers treat ``"unknown"`` as keep-by-default so that v3.15
    phase artifacts (which predate the v3.17 rule set) survive archive.
    """
    rel = rel_path.replace("\\", "/").lstrip("/")
    for p in ARCHIVE_BLACKLIST_PATTERNS:
        if _matches(rel, p):
            return "delete"
    for p in ARCHIVE_WHITELIST_PATTERNS:
        if _matches(rel, p):
            return "keep"
    return "unknown"


def archive_project(project_root: Path) -> Dict[str, List[str]]:
    """Apply archive rules to ``project_root`` in place.

    Deletes every file whose relative path classifies as ``"delete"``;
    keeps everything else. Empty blacklist directories are removed so the
    post-archive tree does not advertise deleted artifacts.

    Returns a report: ``{"kept": [...], "deleted": [...]}`` with relative
    POSIX paths sorted lexicographically.
    """
    root = Path(project_root)
    kept: List[str] = []
    deleted: List[str] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if classify_path(rel) == "delete":
            path.unlink()
            deleted.append(rel)
        else:
            kept.append(rel)

    # Remove now-empty blacklist directory shells (e.g. phase_5/bgm_candidates/).
    for pattern in ARCHIVE_BLACKLIST_PATTERNS:
        if not pattern.endswith("/"):
            continue
        d = root / pattern.rstrip("/")
        if d.exists() and d.is_dir():
            shutil.rmtree(d)

    kept.sort()
    deleted.sort()
    return {"kept": kept, "deleted": deleted}
