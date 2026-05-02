"""TDD test: verifier prompt includes `pytest -m "<tags>"` for BDD owners."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from scripts.run_task_driver import (
    VERIFIER_PROMPT_TEMPLATE,
    build_verifier_command,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_verifier_prompt_injects_bdd_tags():
    cmd = build_verifier_command(
        program="claude",
        task_id="SPEC-C-106",
        max_turns=10,
        prompt_template=VERIFIER_PROMPT_TEMPLATE,
        bdd_tag_expr="router",  # pytest marker expr; no @ prefix
    )
    # prompt is argv[2]; assert BDD line baked in
    prompt = cmd[2]
    assert "pytest tests/integration/bdd/" in prompt
    assert '-m "router"' in prompt or '-m \\"router\\"' in prompt


def test_verifier_prompt_omits_bdd_when_no_tags():
    cmd = build_verifier_command(
        program="claude",
        task_id="SPEC-D-001",
        max_turns=10,
        prompt_template=VERIFIER_PROMPT_TEMPLATE,
        bdd_tag_expr="",
    )
    prompt = cmd[2]
    # When there are no BDD tags, the BDD invocation line must not appear.
    assert "tests/integration/bdd/" not in prompt


def test_build_verifier_command_passes_bdd_tag_expr():
    cmd = build_verifier_command(
        program="claude",
        task_id="SPEC-C-106",
        max_turns=10,
        prompt_template=VERIFIER_PROMPT_TEMPLATE,
        bdd_tag_expr="router",
    )
    # assert BDD line baked into the prompt argument
    assert any("tests/integration/bdd/" in s for s in cmd)


def test_lookup_bdd_tag_expr_works_when_driver_run_as_script(tmp_path: Path):
    """Repro for the regression seen in live driver smoke (bk9aoe550):
    `python3 scripts/run_task_driver.py` puts scripts/ on sys.path but NOT
    the repo root, so `from scripts.pick_next_task import ...` blows up.
    This test invokes the function in a subprocess whose sys.path matches
    what running the driver as a script produces.
    """
    # Build a minimal fake repo with one task card that has bdd_tags.
    spec_dir = tmp_path / "tasks" / "SPEC-C"
    spec_dir.mkdir(parents=True)
    (spec_dir / "C-106-x.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-C-106]
            ## Metadata
            - **task_id**: SPEC-C-106
            - **depends_on**: []
            - **priority**: P2
            - **bdd_tags**: [@router]
            """
        )
    )
    # Emulate `python3 scripts/run_task_driver.py`: only scripts/ on sys.path,
    # not the repo root. `-I` (isolated mode) strips cwd + user site-packages
    # so we faithfully reproduce the live-driver import environment.
    scripts_dir = REPO_ROOT / "scripts"
    res = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            (
                "import sys; "
                f"sys.path.insert(0, {str(scripts_dir)!r}); "
                "from run_task_driver import _lookup_bdd_tag_expr; "
                "from pathlib import Path; "
                f"print(_lookup_bdd_tag_expr(Path({str(tmp_path)!r}), 'SPEC-C-106'))"
            ),
        ],
        cwd=str(tmp_path),  # cwd outside repo: no accidental `scripts` pkg
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"crashed: stderr={res.stderr!r} stdout={res.stdout!r}"
    assert res.stdout.strip() == "router"
