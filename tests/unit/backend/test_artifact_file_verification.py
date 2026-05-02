"""[SPEC-C-011] Tests for artifact file existence verification.

After _generate_phase_artifact writes an artifact JSON, verify that all
path-like fields point to files that exist on disk.
"""

from __future__ import annotations

import json
import os
import sqlite3
from unittest import mock

import pytest

from src.backend.api.routes.projects import _verify_artifact_files


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create a temporary project directory with controlled files."""
    proj_dir = tmp_path / "data" / "projects" / "proj_test"
    os.makedirs(proj_dir, exist_ok=True)
    return proj_dir


# ---------------------------------------------------------------------------
# Tests — missing file detection
# ---------------------------------------------------------------------------


class TestVerifyArtifactFilesMissingDetection:
    def test_detects_single_missing_file(self, tmp_project_dir):
        """One declared path does not exist -> detected as missing."""
        # Create two real files
        (tmp_project_dir / "phase_8").mkdir(exist_ok=True)
        (tmp_project_dir / "phase_8" / "seg_01.mp4").write_text("fake mp4")

        artifact_path = tmp_project_dir / "rough_cut.json"
        artifact_data = {
            "rough_cut_path": "phase_10/rough_cut_v1.mp4",
            "video_url": "phase_8/seg_01.mp4",
            "subtitle_path": "phase_10/subtitle.srt",
        }
        artifact_path.write_text(json.dumps(artifact_data))

        status, missing = _verify_artifact_files(
            str(artifact_path), str(tmp_project_dir)
        )

        assert status == "missing"
        assert len(missing) == 2  # rough_cut_v1.mp4 and subtitle.srt
        assert any("phase_10/rough_cut_v1.mp4" in m for m in missing)
        assert any("phase_10/subtitle.srt" in m for m in missing)

    def test_all_files_exist_returns_ok(self, tmp_project_dir):
        """When all declared paths exist, status is 'ok'."""
        (tmp_project_dir / "phase_10").mkdir(exist_ok=True)
        (tmp_project_dir / "phase_10" / "rough_cut.mp4").write_text("fake")

        artifact_path = tmp_project_dir / "final.json"
        artifact_data = {"output_path": "phase_10/rough_cut.mp4"}
        artifact_path.write_text(json.dumps(artifact_data))

        status, missing = _verify_artifact_files(
            str(artifact_path), str(tmp_project_dir)
        )

        assert status == "ok"
        assert missing == []

    def test_nested_path_like_fields_found(self, tmp_project_dir):
        """Path-like fields in nested dicts and lists are verified."""
        (tmp_project_dir / "phase_11").mkdir(exist_ok=True)
        (tmp_project_dir / "phase_11" / "final_bilibili_1080p.mp4").write_text("fake")
        (tmp_project_dir / "phase_11" / "cover_character_dominant.png").write_text("fake")

        # cover_title_focused.png does NOT exist

        artifact_path = tmp_project_dir / "final.json"
        artifact_data = {
            "output_path": "phase_11/final_bilibili_1080p.mp4",
            "douyin_path": "phase_11/final_douyin_vertical.mp4",
            "cover_paths": [
                "phase_11/cover_character_dominant.png",
                "phase_11/cover_title_focused.png",
            ],
        }
        artifact_path.write_text(json.dumps(artifact_data))

        status, missing = _verify_artifact_files(
            str(artifact_path), str(tmp_project_dir)
        )

        assert status == "missing"
        assert len(missing) == 2  # douyin_path + cover_title_focused
        missing_basenames = [os.path.basename(m) for m in missing]
        assert "final_douyin_vertical.mp4" in missing_basenames
        assert "cover_title_focused.png" in missing_basenames

    def test_empty_artifact_returns_ok(self, tmp_project_dir):
        """An artifact with no path-like fields is trivially ok."""
        artifact_path = tmp_project_dir / "empty.json"
        artifact_data = {"phase": 10, "stub": True, "note": "no paths here"}
        artifact_path.write_text(json.dumps(artifact_data))

        status, missing = _verify_artifact_files(
            str(artifact_path), str(tmp_project_dir)
        )

        assert status == "ok"
        assert missing == []


# ---------------------------------------------------------------------------
# Tests — path resolution
# ---------------------------------------------------------------------------


class TestVerifyArtifactFilesPathResolution:
    def test_resolves_relative_paths_against_project_dir(self, tmp_project_dir):
        """Relative paths are resolved against the project directory."""
        (tmp_project_dir / "phase_10").mkdir(exist_ok=True)
        (tmp_project_dir / "phase_10" / "rough_cut_v1.mp4").write_text("fake")

        artifact_path = tmp_project_dir / "rough_cut.json"
        artifact_data = {"rough_cut_path": "phase_10/rough_cut_v1.mp4"}
        artifact_path.write_text(json.dumps(artifact_data))

        status, missing = _verify_artifact_files(
            str(artifact_path), str(tmp_project_dir)
        )

        assert status == "ok"
        assert missing == []

    def test_path_fields_with_url_pattern_are_skipped(self, tmp_project_dir):
        """Fields containing '/api/' URL patterns are skipped (not local files)."""
        artifact_path = tmp_project_dir / "artifact.json"
        artifact_data = {
            "video_url": "/api/projects/proj_001/files/phase_10/rough_cut.mp4",
            "download_urls": {
                "bilibili": "/api/projects/proj_001/files/phase_11/final_bilibili_1080p.mp4",
            },
            "render_path": "phase_10/actual_file.mp4",
        }
        # Only render_path doesn't exist - URLs should be skipped
        artifact_path.write_text(json.dumps(artifact_data))

        status, missing = _verify_artifact_files(
            str(artifact_path), str(tmp_project_dir)
        )

        # Only the non-URL local file path should be checked
        assert status == "missing"
        assert len(missing) == 1
        assert "phase_10/actual_file.mp4" in missing[0]

    def test_nonexistent_artifact_path_handled_gracefully(self, tmp_project_dir):
        """When the artifact file itself doesn't exist, return gracefully."""
        status, missing = _verify_artifact_files(
            str(tmp_project_dir / "nonexistent.json"), str(tmp_project_dir)
        )

        assert status == "missing"
        assert len(missing) == 1  # the artifact file itself
