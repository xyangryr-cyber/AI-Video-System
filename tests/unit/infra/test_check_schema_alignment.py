"""SPEC-B follow-up: check_schema_alignment.py CLI verifies Pydantic<->TS parity.

Closes PROGRESS.md open follow-up: "scripts/contracts/check_schema_alignment.py missing".

Contract: for each <name>, every Pydantic BaseModel defined in
src/shared/schemas/<name>.py must have its model_fields equal the field set of
the same-named TypeScript interface in src/shared/types/<name>.ts (with
`extends` inheritance flattened).
"""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest
from pydantic import BaseModel

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "contracts" / "check_schema_alignment.py"

# scripts/ is a namespace package; ensure REPO is importable.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


class TestCLI:
    """End-to-end: invoke the real script against known-aligned bundles."""

    @pytest.mark.parametrize(
        "names",
        [
            ("chart_material",),
            ("audio_master",),  # exercises TS `extends MasterAudioCommon`
            ("sfx_layout_plan", "sfx_mix_segments"),
            ("material_manifest", "shot_material_bindings"),
            ("api_master_audio",),
        ],
        ids=lambda x: "+".join(x),
    )
    def test_aligned_bundles_exit_zero(self, names):
        result = _run(*names)
        assert result.returncode == 0, (
            f"expected exit 0 for aligned bundle {names}, got {result.returncode}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_unknown_name_exits_nonzero(self):
        result = _run("definitely_not_a_real_schema_zzz")
        assert result.returncode != 0, "unknown schema name must cause non-zero exit"
        combined = result.stdout + result.stderr
        assert "definitely_not_a_real_schema_zzz" in combined

    def test_no_args_exits_nonzero(self):
        result = _run()
        assert result.returncode != 0, "missing arguments must cause non-zero exit"


# ---------------------------------------------------------------------------
# Unit-level: exercise the internal API with a synthetic (mismatched) fixture.
# ---------------------------------------------------------------------------


class TestInternalAPI:
    def test_aligned_synthetic_returns_no_errors(self, tmp_path):
        from scripts.contracts.check_schema_alignment import check_alignment

        class Foo(BaseModel):
            a: int
            b: str

        mod = types.ModuleType("synthetic_aligned")
        mod.Foo = Foo
        Foo.__module__ = mod.__name__

        ts = tmp_path / "synthetic_aligned.ts"
        ts.write_text("export interface Foo { a: number; b: string }\n")

        errors = check_alignment("synthetic_aligned", ts, mod)
        assert errors == [], f"expected no errors, got {errors}"

    def test_missing_field_on_ts_side_reported(self, tmp_path):
        from scripts.contracts.check_schema_alignment import check_alignment

        class Foo(BaseModel):
            a: int
            b: str
            c: float  # pydantic-only

        mod = types.ModuleType("synthetic_py_only")
        mod.Foo = Foo
        Foo.__module__ = mod.__name__

        ts = tmp_path / "synthetic_py_only.ts"
        ts.write_text("export interface Foo { a: number; b: string }\n")

        errors = check_alignment("synthetic_py_only", ts, mod)
        assert len(errors) == 1
        assert "Foo" in errors[0]
        assert "c" in errors[0]  # the pydantic-only field must be called out

    def test_missing_field_on_py_side_reported(self, tmp_path):
        from scripts.contracts.check_schema_alignment import check_alignment

        class Foo(BaseModel):
            a: int

        mod = types.ModuleType("synthetic_ts_only")
        mod.Foo = Foo
        Foo.__module__ = mod.__name__

        ts = tmp_path / "synthetic_ts_only.ts"
        ts.write_text("export interface Foo { a: number; b: string; c: boolean }\n")

        errors = check_alignment("synthetic_ts_only", ts, mod)
        assert len(errors) == 1
        assert "Foo" in errors[0]
        # at least one TS-only field should be named
        assert "b" in errors[0] or "c" in errors[0]

    def test_pydantic_class_without_ts_interface_reported(self, tmp_path):
        from scripts.contracts.check_schema_alignment import check_alignment

        class OrphanModel(BaseModel):
            x: int

        mod = types.ModuleType("synthetic_orphan")
        mod.OrphanModel = OrphanModel
        OrphanModel.__module__ = mod.__name__

        ts = tmp_path / "synthetic_orphan.ts"
        ts.write_text("export interface SomethingElse { x: number }\n")

        errors = check_alignment("synthetic_orphan", ts, mod)
        assert any("OrphanModel" in e for e in errors)

    def test_extends_resolution_flattens_parent_fields(self, tmp_path):
        """TS `interface Child extends Parent { ... }` must inherit Parent fields."""
        from scripts.contracts.check_schema_alignment import check_alignment

        class Child(BaseModel):
            inherited: str
            own: int

        mod = types.ModuleType("synthetic_extends")
        mod.Child = Child
        Child.__module__ = mod.__name__

        ts = tmp_path / "synthetic_extends.ts"
        ts.write_text(
            "interface Parent { inherited: string }\n"
            "export interface Child extends Parent { own: number }\n"
        )

        errors = check_alignment("synthetic_extends", ts, mod)
        assert errors == [], f"extends must be flattened, got {errors}"


class TestTSParser:
    def test_parse_handles_multiline_fields(self, tmp_path):
        from scripts.contracts.check_schema_alignment import parse_ts_interfaces

        ts = tmp_path / "x.ts"
        ts.write_text(
            "export interface Foo {\n"
            "  a: string;\n"
            "  b?: number | null;\n"
            "  // a comment with {braces} inside\n"
            "  c: { nested: string };\n"
            "}\n"
        )
        result = parse_ts_interfaces(ts)
        assert result["Foo"] == {"a", "b", "c"}

    def test_parse_ignores_type_aliases_only_reads_interfaces(self, tmp_path):
        from scripts.contracts.check_schema_alignment import parse_ts_interfaces

        ts = tmp_path / "x.ts"
        ts.write_text(
            'export type Kind = "a" | "b";\nexport interface Foo { x: Kind }\n'
        )
        result = parse_ts_interfaces(ts)
        assert "Foo" in result
        assert result["Foo"] == {"x"}
        assert "Kind" not in result
