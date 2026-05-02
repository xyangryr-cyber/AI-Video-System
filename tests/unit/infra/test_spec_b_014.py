"""Tests for [SPEC-B-014] Storage directory layout (phase_5/6/7a additions)."""

from pathlib import Path

from src.backend.infra.storage_layout import (
    create_project_layout,
)
from src.backend.infra.cleanup_rules import (
    OSS_ASYNC_ARCHIVE_PATHS,
    LOCAL_ONLY_PATHS,
    classify_path,
    archive_project,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _touch(root: Path, rel: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("")
    return p


def _make_v317_project(tmp_path: Path) -> Path:
    """Create a full project layout and return the root."""
    root = tmp_path / "proj_v317"
    create_project_layout(root)
    return root


# ---------------------------------------------------------------------------
# AC-1: Directory pre-creation
# ---------------------------------------------------------------------------


class TestAC1:
    """AC-1: Project init pre-creates phase_5/bgm_candidates,
    phase_6/sfx_applied_segments, phase_7a/ and subdirs."""

    def test_phase_5_bgm_candidates_created(self, tmp_path):
        root = _make_v317_project(tmp_path)
        d = root / "phase_5" / "bgm_candidates"
        assert d.exists() and d.is_dir(), f"expected {d} to exist"

    def test_phase_6_sfx_applied_segments_created(self, tmp_path):
        root = _make_v317_project(tmp_path)
        d = root / "phase_6" / "sfx_applied_segments"
        assert d.exists() and d.is_dir(), f"expected {d} to exist"

    def test_phase_7a_subdirs_created(self, tmp_path):
        root = _make_v317_project(tmp_path)
        phase_7a = root / "phase_7a"
        assert phase_7a.exists() and phase_7a.is_dir()
        for sub in ("verified_materials", "chart_materials"):
            d = phase_7a / sub
            assert d.exists() and d.is_dir(), f"expected {d} to exist"


# ---------------------------------------------------------------------------
# AC-2: Backup classification
# ---------------------------------------------------------------------------


class TestAC2:
    """AC-2: OSS archive covers verified_materials; previews are local-only."""

    def test_oss_archive_includes_verified_materials(self):
        assert "phase_7a/verified_materials/" in OSS_ASYNC_ARCHIVE_PATHS

    def test_local_only_includes_previews(self):
        assert "phase_5/bgm_mix_preview_*.mp3" in LOCAL_ONLY_PATHS
        assert "phase_6/sfx_applied_segments/" in LOCAL_ONLY_PATHS


# ---------------------------------------------------------------------------
# AC-3: Whitelist (kept on archive)
# ---------------------------------------------------------------------------


class TestAC3:
    """AC-3: Archive keeps master audio files + chart_materials."""

    _KEPT = [
        "phase_4/narration_master.mp3",
        "phase_4/narration_master.json",
        "phase_5/bgm_mix_master.mp3",
        "phase_5/bgm_mix_master.json",
        "phase_6/final_audio_with_bgm_sfx.mp3",
        "phase_6/final_audio_with_bgm_sfx.json",
    ]

    def test_archive_keeps_master_audio_files(self):
        for p in self._KEPT:
            assert classify_path(p) == "keep", f"{p} must be keep"

    def test_archive_keeps_chart_materials(self):
        assert classify_path("phase_7a/chart_materials/chart_01.png") == "keep"
        assert classify_path("phase_7a/chart_materials/subdir/file.json") == "keep"


# ---------------------------------------------------------------------------
# AC-4: Blacklist (removed on archive)
# ---------------------------------------------------------------------------


class TestAC4:
    """AC-4: Archive removes bgm_candidates, preview mp3s, sfx_applied_segments."""

    def test_archive_removes_bgm_candidates(self):
        assert classify_path("phase_5/bgm_candidates/track1.mp3") == "delete"
        assert classify_path("phase_5/bgm_candidates") == "delete"

    def test_archive_removes_sfx_applied_segments(self):
        assert classify_path("phase_6/sfx_applied_segments/seg1.json") == "delete"
        assert classify_path("phase_6/sfx_applied_segments") == "delete"

    def test_bgm_mix_preview_deleted(self):
        assert classify_path("phase_5/bgm_mix_preview_v1.mp3") == "delete"
        assert classify_path("phase_5/bgm_mix_preview_2026-04-25.mp3") == "delete"


# ---------------------------------------------------------------------------
# AC-5: End-to-end archive
# ---------------------------------------------------------------------------


class TestAC5:
    """AC-5: End-to-end archive classification on fixture project."""

    def test_archive_classification_end_to_end(self, tmp_path):
        root = tmp_path / "proj_e2e"
        create_project_layout(root)

        # Files that should be kept
        _touch(root, "phase_4/narration_master.mp3")
        _touch(root, "phase_4/narration_master.json")
        _touch(root, "phase_5/bgm_mix_master.mp3")
        _touch(root, "phase_7a/chart_materials/chart01.png")

        # Files that should be deleted
        _touch(root, "phase_5/bgm_candidates/track1.mp3")
        _touch(root, "phase_5/bgm_mix_preview_v1.mp3")
        _touch(root, "phase_6/sfx_applied_segments/seg1.json")

        # A v3.15 "unknown" file — should be kept by default
        _touch(root, "phase_0/outline.json")

        report = archive_project(root)

        assert "phase_4/narration_master.mp3" in report["kept"]
        assert "phase_7a/chart_materials/chart01.png" in report["kept"]
        assert "phase_0/outline.json" in report["kept"]

        assert "phase_5/bgm_candidates/track1.mp3" in report["deleted"]
        assert "phase_5/bgm_mix_preview_v1.mp3" in report["deleted"]
        assert "phase_6/sfx_applied_segments/seg1.json" in report["deleted"]

        # Blacklist directories should be removed
        assert not (root / "phase_5" / "bgm_candidates").exists()
        assert not (root / "phase_6" / "sfx_applied_segments").exists()

        # Whitelist directories and v3.15 dirs should still exist
        assert (root / "phase_7a" / "chart_materials").exists()
        assert (root / "phase_0").exists()


# ---------------------------------------------------------------------------
# AC-6: v3.15 existing dirs regression
# ---------------------------------------------------------------------------


class TestAC6:
    """AC-6: v3.15 directories (phase_0..phase_11) survive archive."""

    def test_v315_existing_dirs_intact(self, tmp_path):
        root = tmp_path / "proj_v315_regression"
        create_project_layout(root)

        # Place known files in each v3.15 phase dir
        for i in range(12):
            _touch(root, f"phase_{i}/artifact_{i}.json")

        # Also place a blacklisted file to ensure archive does something
        _touch(root, "phase_5/bgm_candidates/extra.mp3")

        report = archive_project(root)

        # All v3.15 phase files must be kept
        for i in range(12):
            assert f"phase_{i}/artifact_{i}.json" in report["kept"], (
                f"v3.15 phase_{i}/artifact_{i}.json should be kept"
            )

        # Blacklisted file removed
        assert "phase_5/bgm_candidates/extra.mp3" in report["deleted"]

        # All v3.15 directories still exist
        for i in range(12):
            assert (root / f"phase_{i}").exists(), (
                f"v3.15 phase_{i} must still exist after archive"
            )
