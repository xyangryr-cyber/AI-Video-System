"""Tests for [SPEC-E-014] P7A Shot x Material 矩阵 + chart 确认卡."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
MATRIX_TEST = "../../tests/unit/frontend/phase7a/Phase7AMatrix.test.tsx"
DRAWER_TEST = "../../tests/unit/frontend/phase7a/MaterialDetailDrawer.test.tsx"
CHART_TEST = "../../tests/unit/frontend/phase7a/ChartMaterialConfirmCard.test.tsx"


def _vitest(file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: 矩阵渲染 shots x materials 网格 + 4 色状态"""

    def test_renders_grid_with_status_colors(self):
        r = _vitest(MATRIX_TEST, "AC-1")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2:
    """AC-2: missing 单元格 → MaterialDetailDrawer + 重抓按钮"""

    def test_missing_cell_opens_drawer_and_refetch(self):
        r1 = _vitest(MATRIX_TEST, "AC-2")
        r2 = _vitest(DRAWER_TEST, "AC-2")
        assert r1.returncode == 0, f"MATRIX stdout={r1.stdout}\nstderr={r1.stderr}"
        assert r2.returncode == 0, f"DRAWER stdout={r2.stdout}\nstderr={r2.stderr}"


class TestAC3:
    """AC-3: ChartMaterialConfirmCard 展示 axis_spec + 请求修改"""

    def test_renders_axis_spec_and_change_request(self):
        r = _vitest(CHART_TEST, "AC-3")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4:
    """AC-4: supplement_material API 调用"""

    def test_supplement_material_calls_api(self):
        r = _vitest(DRAWER_TEST, "AC-2")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5:
    """AC-5: a11y grid role + gridcell + aria-label"""

    def test_a11y_grid_role_and_cell_aria(self):
        r = _vitest(MATRIX_TEST, "AC-5")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6:
    """AC-6: anchor_text 在 shot 行显示"""

    def test_shows_anchor_text_per_shot_row(self):
        r = _vitest(MATRIX_TEST, "AC-6")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
