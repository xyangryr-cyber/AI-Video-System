"""Tests for [SPEC-B-014] archive whitelist / blacklist / backup classification.

Authority:
  tasks/SPEC-B/B-014-storage-directory-layout.md Test Mapping AC-2..AC-6.
  docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-2.

APIs under test (src/backend/infra/cleanup_rules.py):
  - ARCHIVE_WHITELIST_PATTERNS
  - ARCHIVE_BLACKLIST_PATTERNS
  - OSS_ASYNC_ARCHIVE_PATHS
  - LOCAL_ONLY_PATHS
  - classify_path(rel_path: str) -> "keep" | "delete" | "unknown"
  - archive_project(project_root: Path) -> dict{"kept": [...], "deleted": [...]}
"""

from __future__ import annotations

from pathlib import Path

from src.backend.infra import cleanup_rules, storage_layout


# ---------- Fixture builder -------------------------------------------------


def _build_v317_project(root: Path) -> Path:
    """Build a project dir with v3.15 phase artifacts + v3.17 new artifacts."""
    storage_layout.create_project_layout(root)

    # v3.15 existing phase artifacts (regression guard)
    (root / "phase_0" / "intent.json").write_text("{}")
    (root / "phase_1" / "outline.json").write_text("{}")
    (root / "phase_2" / "script.json").write_text("{}")
    (root / "phase_3" / "storyboard.json").write_text("{}")
    (root / "phase_4" / "narration.json").write_text("{}")
    (root / "phase_11" / "render_manifest.json").write_text("{}")

    # v3.17 master audio files (AC-3 whitelist)
    (root / "phase_4" / "narration_master.mp3").write_bytes(b"mp3")
    (root / "phase_4" / "narration_master.json").write_text("{}")
    (root / "phase_5" / "bgm_mix_master.mp3").write_bytes(b"mp3")
    (root / "phase_5" / "bgm_mix_master.json").write_text("{}")
    (root / "phase_6" / "final_audio_with_bgm_sfx.mp3").write_bytes(b"mp3")
    (root / "phase_6" / "final_audio_with_bgm_sfx.json").write_text("{}")

    # phase_7a artifacts
    (root / "phase_7a" / "material_manifest.json").write_text("{}")
    (root / "phase_7a" / "chart_materials" / "chart_01.json").write_text("{}")
    (root / "phase_7a" / "chart_materials" / "chart_02.json").write_text("{}")
    (root / "phase_7a" / "verified_materials" / "mat_01.png").write_bytes(b"png")

    # AC-4 blacklist targets
    (root / "phase_5" / "bgm_candidates" / "cand_01.mp3").write_bytes(b"mp3")
    (root / "phase_5" / "bgm_candidates" / "cand_02.mp3").write_bytes(b"mp3")
    (root / "phase_5" / "bgm_mix_preview_01.mp3").write_bytes(b"mp3")
    (root / "phase_5" / "bgm_mix_preview_02.mp3").write_bytes(b"mp3")
    (root / "phase_6" / "sfx_applied_segments" / "seg_01.mp3").write_bytes(b"mp3")
    (root / "phase_6" / "sfx_applied_segments" / "seg_02.mp3").write_bytes(b"mp3")

    return root


# ---------- AC-2: backup classification -------------------------------------


def test_oss_archive_includes_verified_materials() -> None:
    assert any(
        p.rstrip("/") == "phase_7a/verified_materials"
        for p in cleanup_rules.OSS_ASYNC_ARCHIVE_PATHS
    ), "phase_7a/verified_materials must be in OSS_ASYNC_ARCHIVE_PATHS"


def test_local_only_includes_previews() -> None:
    local_only = set(cleanup_rules.LOCAL_ONLY_PATHS)
    assert "phase_5/bgm_mix_preview_*.mp3" in local_only
    assert any(p.rstrip("/") == "phase_6/sfx_applied_segments" for p in local_only), (
        "phase_6/sfx_applied_segments must be in LOCAL_ONLY_PATHS"
    )


def test_verified_materials_not_in_local_only() -> None:
    """phase_7a/verified_materials goes to OSS async archive, so it must NOT
    also be marked local-only (AC-2 mutually exclusive semantics)."""
    for p in cleanup_rules.LOCAL_ONLY_PATHS:
        assert "verified_materials" not in p, (
            "phase_7a/verified_materials belongs to OSS async archive, "
            "not LOCAL_ONLY_PATHS"
        )


# ---------- AC-3: whitelist (kept on archive) -------------------------------


def test_archive_keeps_master_audio_files(tmp_path: Path) -> None:
    root = _build_v317_project(tmp_path / "proj")
    cleanup_rules.archive_project(root)
    assert (root / "phase_4" / "narration_master.mp3").is_file()
    assert (root / "phase_4" / "narration_master.json").is_file()
    assert (root / "phase_5" / "bgm_mix_master.mp3").is_file()
    assert (root / "phase_5" / "bgm_mix_master.json").is_file()
    assert (root / "phase_6" / "final_audio_with_bgm_sfx.mp3").is_file()
    assert (root / "phase_6" / "final_audio_with_bgm_sfx.json").is_file()


def test_archive_keeps_chart_materials(tmp_path: Path) -> None:
    root = _build_v317_project(tmp_path / "proj")
    cleanup_rules.archive_project(root)
    chart_dir = root / "phase_7a" / "chart_materials"
    assert chart_dir.is_dir()
    assert (chart_dir / "chart_01.json").is_file()
    assert (chart_dir / "chart_02.json").is_file()


# ---------- AC-4: blacklist (removed on archive) ----------------------------


def test_archive_removes_bgm_candidates(tmp_path: Path) -> None:
    root = _build_v317_project(tmp_path / "proj")
    cleanup_rules.archive_project(root)
    cand_dir = root / "phase_5" / "bgm_candidates"
    assert not cand_dir.exists() or not any(cand_dir.iterdir()), (
        "phase_5/bgm_candidates/ contents must be removed on archive"
    )
    assert not (root / "phase_5" / "bgm_mix_preview_01.mp3").exists()
    assert not (root / "phase_5" / "bgm_mix_preview_02.mp3").exists()


def test_archive_removes_sfx_applied_segments(tmp_path: Path) -> None:
    root = _build_v317_project(tmp_path / "proj")
    cleanup_rules.archive_project(root)
    seg_dir = root / "phase_6" / "sfx_applied_segments"
    assert not seg_dir.exists() or not any(seg_dir.iterdir()), (
        "phase_6/sfx_applied_segments/ contents must be removed on archive"
    )


# ---------- AC-5: end-to-end classification matches expected sets ----------


def test_archive_classification_end_to_end(tmp_path: Path) -> None:
    root = _build_v317_project(tmp_path / "proj")
    report = cleanup_rules.archive_project(root)

    kept = set(report["kept"])
    deleted = set(report["deleted"])

    expected_kept = {
        "phase_0/intent.json",
        "phase_1/outline.json",
        "phase_2/script.json",
        "phase_3/storyboard.json",
        "phase_4/narration.json",
        "phase_4/narration_master.mp3",
        "phase_4/narration_master.json",
        "phase_5/bgm_mix_master.mp3",
        "phase_5/bgm_mix_master.json",
        "phase_6/final_audio_with_bgm_sfx.mp3",
        "phase_6/final_audio_with_bgm_sfx.json",
        "phase_7a/material_manifest.json",
        "phase_7a/chart_materials/chart_01.json",
        "phase_7a/chart_materials/chart_02.json",
        "phase_7a/verified_materials/mat_01.png",
        "phase_11/render_manifest.json",
    }
    expected_deleted = {
        "phase_5/bgm_candidates/cand_01.mp3",
        "phase_5/bgm_candidates/cand_02.mp3",
        "phase_5/bgm_mix_preview_01.mp3",
        "phase_5/bgm_mix_preview_02.mp3",
        "phase_6/sfx_applied_segments/seg_01.mp3",
        "phase_6/sfx_applied_segments/seg_02.mp3",
    }

    assert kept == expected_kept, (
        f"kept mismatch\n  missing: {expected_kept - kept}\n"
        f"  extra:   {kept - expected_kept}"
    )
    assert deleted == expected_deleted, (
        f"deleted mismatch\n  missing: {expected_deleted - deleted}\n"
        f"  extra:   {deleted - expected_deleted}"
    )
    assert kept.isdisjoint(deleted)


def test_classify_path_unit() -> None:
    assert cleanup_rules.classify_path("phase_5/bgm_candidates/cand_01.mp3") == "delete"
    assert cleanup_rules.classify_path("phase_5/bgm_mix_preview_07.mp3") == "delete"
    assert (
        cleanup_rules.classify_path("phase_6/sfx_applied_segments/seg_01.mp3")
        == "delete"
    )
    assert cleanup_rules.classify_path("phase_5/bgm_mix_master.mp3") == "keep"
    assert cleanup_rules.classify_path("phase_4/narration_master.json") == "keep"
    assert (
        cleanup_rules.classify_path("phase_7a/chart_materials/chart_01.json") == "keep"
    )


# ---------- AC-6: v3.15 regression on archive -------------------------------


def test_v315_existing_artifacts_survive_archive(tmp_path: Path) -> None:
    root = _build_v317_project(tmp_path / "proj")
    cleanup_rules.archive_project(root)
    assert (root / "phase_0" / "intent.json").is_file()
    assert (root / "phase_1" / "outline.json").is_file()
    assert (root / "phase_2" / "script.json").is_file()
    assert (root / "phase_3" / "storyboard.json").is_file()
    assert (root / "phase_4" / "narration.json").is_file()
    assert (root / "phase_11" / "render_manifest.json").is_file()
