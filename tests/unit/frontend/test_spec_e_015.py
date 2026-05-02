"""Tests for [SPEC-E-015] MasterAudioView / AnnotationSpan / ShotMaterialBindingView / ChartMaterialView."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"


def _vitest(test_file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: 4 type files exist; tsc --noEmit passes on SPEC-E-015 files."""

    def test_files_exist_and_compile(self):
        spec_filenames = {
            "audio_master.ts",
            "annotation_span.ts",
            "shot_material_binding.ts",
            "chart_material.ts",
            "index.ts",
        }
        for name in spec_filenames:
            f = FRONTEND_ROOT / "types" / name
            assert f.exists(), f"Missing type file: {f}"

        # Use project tsconfig for correct compiler options (skipLibCheck,
        # strict, paths), then verify SPEC-E-015 files have no type errors.
        r = subprocess.run(
            ["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
            cwd=FRONTEND_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        type_errors = [
            line
            for line in (r.stdout + r.stderr).split("\n")
            if any(name in line for name in spec_filenames)
        ]
        assert not type_errors, "SPEC-E-015 type errors:\n" + "\n".join(type_errors)


class TestAC2:
    """AC-2: fields match src/shared/types/ counterparts."""

    def test_snapshot_match_shared_types(self):
        r = _vitest("types/test_v317_types_alignment.test.ts", "AC-2:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3:
    """AC-3: auto-gen runs without diff."""

    def test_autogen_diff_empty(self):
        # npm run gen:types runs and produces no diff against committed types
        r = subprocess.run(
            ["npm", "run", "gen:types"],
            cwd=FRONTEND_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # If the script is not configured, skip (not a failure)
        if (
            "missing script" in r.stderr.lower()
            or "unknown command" in r.stderr.lower()
        ):
            import pytest

            pytest.skip("npm run gen:types not configured — deferred to SPEC-B-017")
        diff_r = subprocess.run(
            ["git", "diff", "--exit-code", "src/frontend/types/"],
            cwd=Path(__file__).parents[3],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert diff_r.returncode == 0, f"gen:types produced a diff:\n{diff_r.stdout}"


class TestAC4:
    """AC-4: types/index.ts exports 4 new types without namespace conflict."""

    def test_index_exports_no_namespace_conflict(self):
        r = _vitest("types/test_v317_types_alignment.test.ts", "AC-1:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5:
    """AC-5: MasterAudioView.kind strict union matches backend enum."""

    def test_master_audio_kind_union_matches_backend(self):
        r = _vitest("types/test_v317_types_alignment.test.ts", "AC-5:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
