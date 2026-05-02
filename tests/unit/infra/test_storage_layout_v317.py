"""Tests for [SPEC-B-014] storage layout (AC-1 + AC-6 structural side).

Authority:
  tasks/SPEC-B/B-014-storage-directory-layout.md Test Mapping AC-1, AC-6.
  docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-2.

API under test:
  src.backend.infra.storage_layout.create_project_layout(project_root) -> Path
"""

from __future__ import annotations

from pathlib import Path

from src.backend.infra import storage_layout


# ---------- AC-1: v3.17 new directories pre-created -------------------------


def test_phase_5_bgm_candidates_created(tmp_path: Path) -> None:
    storage_layout.create_project_layout(tmp_path / "proj")
    assert (tmp_path / "proj" / "phase_5" / "bgm_candidates").is_dir()


def test_phase_6_sfx_applied_segments_created(tmp_path: Path) -> None:
    storage_layout.create_project_layout(tmp_path / "proj")
    assert (tmp_path / "proj" / "phase_6" / "sfx_applied_segments").is_dir()


def test_phase_7a_subdirs_created(tmp_path: Path) -> None:
    storage_layout.create_project_layout(tmp_path / "proj")
    root = tmp_path / "proj"
    assert (root / "phase_7a").is_dir()
    assert (root / "phase_7a" / "verified_materials").is_dir()
    assert (root / "phase_7a" / "chart_materials").is_dir()


# ---------- AC-6: v3.15 existing phase_0..phase_11 untouched ----------------


def test_v315_existing_dirs_intact(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    storage_layout.create_project_layout(root)
    for i in range(12):
        assert (root / f"phase_{i}").is_dir(), f"phase_{i} missing"


def test_create_is_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    storage_layout.create_project_layout(root)
    (root / "phase_0" / "intent.json").write_text("{}")
    storage_layout.create_project_layout(root)
    assert (root / "phase_0" / "intent.json").is_file(), (
        "existing v3.15 artifacts must survive re-initialization"
    )
