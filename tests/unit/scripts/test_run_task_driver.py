"""Tests for scripts/run_task_driver.py.

Covers: loop termination conditions, stop-on-error behavior, max-tasks cap,
env var propagation, and CLI surface.

The driver dispatches `claude -p` subprocesses per task. Tests inject a fake
`dispatch` callable so no real `claude` binary is invoked.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "run_task_driver.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


# --- Unit tests on run_loop ---


def test_loop_empty_exits_immediately() -> None:
    import run_task_driver as m

    calls = []

    def pick_next():
        return None

    def dispatch(task_id):  # pragma: no cover - should not be called
        calls.append(task_id)
        return 0

    result = m.run_loop(
        pick_next=pick_next,
        dispatch=dispatch,
        max_tasks=10,
        stop_on_error=True,
        log=lambda _: None,
    )
    assert result["reason"] == "no_tasks_ready"
    assert result["iterations"] == 0
    assert calls == []


def test_loop_runs_tasks_in_sequence() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001", "SPEC-A-002", None]
    dispatched = []

    def pick_next():
        return queue.pop(0)

    def dispatch(task_id):
        dispatched.append(task_id)
        return 0

    result = m.run_loop(
        pick_next=pick_next,
        dispatch=dispatch,
        max_tasks=10,
        stop_on_error=True,
        log=lambda _: None,
    )
    assert dispatched == ["SPEC-A-001", "SPEC-A-002"]
    assert result["reason"] == "no_tasks_ready"
    assert result["iterations"] == 2


def test_loop_respects_max_tasks() -> None:
    import run_task_driver as m

    dispatched = []

    def pick_next():
        # never runs out
        return f"SPEC-A-{len(dispatched) + 1:03d}"

    def dispatch(task_id):
        dispatched.append(task_id)
        return 0

    result = m.run_loop(
        pick_next=pick_next,
        dispatch=dispatch,
        max_tasks=3,
        stop_on_error=True,
        log=lambda _: None,
    )
    assert len(dispatched) == 3
    assert result["reason"] == "max_tasks_reached"
    assert result["iterations"] == 3


def test_loop_stops_on_failure_by_default() -> None:
    import run_task_driver as m

    dispatched = []

    def pick_next():
        return f"SPEC-A-{len(dispatched) + 1:03d}"

    def dispatch(task_id):
        dispatched.append(task_id)
        return 42 if len(dispatched) == 1 else 0

    result = m.run_loop(
        pick_next=pick_next,
        dispatch=dispatch,
        max_tasks=10,
        stop_on_error=True,
        log=lambda _: None,
    )
    assert dispatched == ["SPEC-A-001"]
    assert result["reason"] == "task_failed"
    assert result["task_id"] == "SPEC-A-001"
    assert result["exit_code"] == 42
    assert result["iterations"] == 1


def test_loop_continues_on_failure_when_flag_clear() -> None:
    import run_task_driver as m

    dispatched = []
    queue = ["SPEC-A-001", "SPEC-A-002", None]

    def pick_next():
        return queue.pop(0)

    def dispatch(task_id):
        dispatched.append(task_id)
        return 42 if task_id == "SPEC-A-001" else 0

    result = m.run_loop(
        pick_next=pick_next,
        dispatch=dispatch,
        max_tasks=10,
        stop_on_error=False,
        log=lambda _: None,
    )
    assert dispatched == ["SPEC-A-001", "SPEC-A-002"]
    assert result["reason"] == "no_tasks_ready"
    assert result["iterations"] == 2


def test_log_callback_receives_events() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001", None]
    dispatched = []
    logs: list[str] = []

    def pick_next():
        return queue.pop(0)

    def dispatch(task_id):
        dispatched.append(task_id)
        return 0

    m.run_loop(
        pick_next=pick_next,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=logs.append,
    )
    joined = "\n".join(logs)
    assert "SPEC-A-001" in joined
    assert "dispatching" in joined.lower()


# --- build_dispatch_command ---


def test_build_dispatch_command_includes_flags() -> None:
    import run_task_driver as m

    cmd = m.build_dispatch_command(
        program="claude",
        task_id="SPEC-A-001",
        max_turns=80,
        prompt_template="do {task_id} now",
    )
    assert cmd[0] == "claude"
    assert "-p" in cmd
    assert "SPEC-A-001" in " ".join(cmd)
    assert "--max-turns" in cmd
    assert "80" in cmd


def test_make_dispatch_sets_env_and_runs_command(tmp_path: Path) -> None:
    """Verify dispatch subprocess receives AVS_CURRENT_TASK."""
    import run_task_driver as m

    marker = tmp_path / "env_dump.txt"

    def build(task_id: str) -> list[str]:
        code = (
            "import os, sys; "
            f"open(r'{marker}', 'w').write("
            "os.environ.get('AVS_CURRENT_TASK', 'MISSING'))"
        )
        return [sys.executable, "-c", code]

    dispatch = m.make_dispatch(build)
    rc = dispatch("SPEC-A-007")
    assert rc == 0
    assert marker.read_text() == "SPEC-A-007"


def test_make_dispatch_propagates_nonzero_exit(tmp_path: Path) -> None:
    import run_task_driver as m

    def build(task_id: str) -> list[str]:
        return [sys.executable, "-c", "import sys; sys.exit(7)"]

    dispatch = m.make_dispatch(build)
    assert dispatch("SPEC-A-001") == 7


# --- pick_next_from_script (subprocess wrapper) ---


def test_pick_next_from_script_returns_task(tmp_path: Path) -> None:
    import run_task_driver as m

    # Build a synthetic repo where pick_next_task.py would pick SPEC-A-001.
    (tmp_path / "tasks" / "SPEC-A").mkdir(parents=True)
    (tmp_path / "tasks" / "SPEC-A" / "A-001-x.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-001] Fake
            ## Metadata
            - **task_id**: SPEC-A-001
            - **depends_on**: []
            - **priority**: P0
            """
        )
    )
    (tmp_path / "PROGRESS.md").write_text("")
    # Copy pick_next_task.py next to our fake root so it can find tasks/.
    script = REPO_ROOT / "scripts" / "pick_next_task.py"
    picker = m.pick_next_from_script(script, tmp_path)
    assert picker() == "SPEC-A-001"


def test_pick_next_from_script_returns_none_when_nothing(
    tmp_path: Path,
) -> None:
    import run_task_driver as m

    (tmp_path / "tasks").mkdir()
    (tmp_path / "PROGRESS.md").write_text("")
    script = REPO_ROOT / "scripts" / "pick_next_task.py"
    picker = m.pick_next_from_script(script, tmp_path)
    assert picker() is None


# --- CLI integration ---


def test_cli_dry_run_lists_what_would_dispatch(tmp_path: Path) -> None:
    # Build synthetic project root with one ready task, no PROGRESS entries.
    (tmp_path / "tasks" / "SPEC-A").mkdir(parents=True)
    (tmp_path / "tasks" / "SPEC-A" / "A-001-x.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-001]
            ## Metadata
            - **task_id**: SPEC-A-001
            - **depends_on**: []
            - **priority**: P0
            """
        )
    )
    (tmp_path / "PROGRESS.md").write_text("")
    # Symlink or copy scripts/pick_next_task.py — driver uses an explicit path.
    (tmp_path / "scripts").mkdir()
    import shutil

    shutil.copy(
        REPO_ROOT / "scripts" / "pick_next_task.py",
        tmp_path / "scripts" / "pick_next_task.py",
    )
    shutil.copy(SCRIPT, tmp_path / "scripts" / "run_task_driver.py")
    res = subprocess.run(
        [
            sys.executable,
            str(tmp_path / "scripts" / "run_task_driver.py"),
            "--root",
            str(tmp_path),
            "--dry-run",
            "--max-tasks",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    assert "SPEC-A-001" in res.stdout
    assert "dry-run" in res.stdout.lower() or "DRY" in res.stdout


def test_cli_dry_run_task_id_override_targets_specific(tmp_path: Path) -> None:
    """--task-id on the driver bypasses picker ordering (targets SPEC-C-106)."""
    for tid, deps, prio in [
        ("SPEC-A-001", [], "P0"),
        ("SPEC-C-106", [], "P2"),
    ]:
        spec = tid.split("-")[1]
        d = tmp_path / "tasks" / f"SPEC-{spec}"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{'-'.join(tid.split('-')[1:])}-x.md").write_text(
            textwrap.dedent(
                f"""\
                # [{tid}]
                ## Metadata
                - **task_id**: {tid}
                - **depends_on**: {deps}
                - **priority**: {prio}
                """
            )
        )
    (tmp_path / "PROGRESS.md").write_text("")
    (tmp_path / "scripts").mkdir()
    import shutil

    shutil.copy(
        REPO_ROOT / "scripts" / "pick_next_task.py",
        tmp_path / "scripts" / "pick_next_task.py",
    )
    shutil.copy(SCRIPT, tmp_path / "scripts" / "run_task_driver.py")
    # Without --task-id, driver would pick SPEC-A-001 (P0 < P2). With it,
    # SPEC-C-106 must be the reported next task.
    res = subprocess.run(
        [
            sys.executable,
            str(tmp_path / "scripts" / "run_task_driver.py"),
            "--root",
            str(tmp_path),
            "--dry-run",
            "--max-tasks",
            "1",
            "--task-id",
            "SPEC-C-106",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    assert "SPEC-C-106" in res.stdout
    assert "SPEC-A-001" not in res.stdout


# --- Verify-fix loop (post-dispatch audit + auto-repair) ---


def test_loop_runs_verifier_after_successful_dispatch() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001", None]
    events: list[tuple] = []

    def pick():
        return queue.pop(0)

    def dispatch(tid):
        events.append(("dispatch", tid))
        return 0

    def verify(tid):
        events.append(("verify", tid))
        return ("pass", f".verify/{tid}.json")

    def fix(tid, rpt):  # pragma: no cover - should not be called
        events.append(("fix", tid, rpt))
        return 0

    m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        max_fix_rounds=3,
    )
    assert ("dispatch", "SPEC-A-001") in events
    assert ("verify", "SPEC-A-001") in events
    assert not any(e[0] == "fix" for e in events)


def test_loop_skips_verify_when_dispatch_fails() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001"]
    events: list[tuple] = []

    def pick():
        return queue.pop(0) if queue else None

    def dispatch(tid):
        return 1

    def verify(tid):  # pragma: no cover
        events.append(("verify", tid))
        return ("pass", "")

    def fix(tid, rpt):  # pragma: no cover
        events.append(("fix", tid, rpt))
        return 0

    result = m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        max_fix_rounds=3,
    )
    assert result["reason"] == "task_failed"
    assert events == []


def test_loop_fix_then_reverify_on_fail() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001", None]
    verify_results = [("fail", "r1"), ("pass", "r2")]
    events: list[tuple] = []

    def pick():
        return queue.pop(0)

    def dispatch(tid):
        events.append(("dispatch", tid))
        return 0

    def verify(tid):
        events.append(("verify", tid))
        return verify_results.pop(0)

    def fix(tid, rpt):
        events.append(("fix", tid, rpt))
        return 0

    m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        max_fix_rounds=3,
    )
    kinds = [e[0] for e in events]
    assert kinds == ["dispatch", "verify", "fix", "verify"]
    assert events[2] == ("fix", "SPEC-A-001", "r1")


def test_loop_exhausts_fix_rounds_and_stops() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001"]
    events: list[str] = []

    def pick():
        return queue.pop(0) if queue else None

    def dispatch(tid):
        return 0

    def verify(tid):
        events.append("v")
        return ("fail", "r")

    def fix(tid, rpt):
        events.append("f")
        return 0

    result = m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        max_fix_rounds=2,
    )
    # max_fix_rounds=2: verify (initial) -> fix#1 -> verify -> fix#2 -> verify -> stop
    assert events.count("v") == 3
    assert events.count("f") == 2
    assert result["reason"] == "verify_exhausted"
    assert result["task_id"] == "SPEC-A-001"
    assert result["fix_rounds_used"] == 2


def test_loop_stops_when_fixer_exits_nonzero() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001"]

    def pick():
        return queue.pop(0) if queue else None

    def dispatch(tid):
        return 0

    def verify(tid):
        return ("fail", "r")

    def fix(tid, rpt):
        return 7

    result = m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        max_fix_rounds=3,
    )
    assert result["reason"] == "fix_failed"
    assert result["exit_code"] == 7
    assert result["task_id"] == "SPEC-A-001"


def test_loop_backward_compat_without_verify_fix() -> None:
    """Legacy signature (no verify/fix) still works — single-agent mode."""
    import run_task_driver as m

    queue = ["SPEC-A-001", None]
    dispatched: list[str] = []

    def pick():
        return queue.pop(0)

    def dispatch(tid):
        dispatched.append(tid)
        return 0

    result = m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
    )
    assert dispatched == ["SPEC-A-001"]
    assert result["reason"] == "no_tasks_ready"


def test_loop_continue_on_verify_exhausted_when_flag_clear() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001", "SPEC-A-002", None]
    dispatched: list[str] = []

    def pick():
        return queue.pop(0)

    def dispatch(tid):
        dispatched.append(tid)
        return 0

    def verify(tid):
        if tid == "SPEC-A-001":
            return ("fail", "r")
        return ("pass", "r")

    def fix(tid, rpt):
        return 0

    result = m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=False,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        max_fix_rounds=1,
    )
    assert dispatched == ["SPEC-A-001", "SPEC-A-002"]
    assert result["reason"] == "no_tasks_ready"


# --- Verifier/fixer command builders ---


def test_build_verifier_command_structure() -> None:
    import run_task_driver as m

    cmd = m.build_verifier_command(
        program="claude",
        task_id="SPEC-A-001",
        max_turns=40,
        prompt_template="audit {task_id}",
    )
    assert cmd[0] == "claude"
    assert "-p" in cmd
    assert "SPEC-A-001" in " ".join(cmd)
    assert "--max-turns" in cmd
    assert "40" in cmd


def test_build_fixer_command_structure() -> None:
    import run_task_driver as m

    cmd = m.build_fixer_command(
        program="claude",
        task_id="SPEC-A-001",
        max_turns=60,
        prompt_template="fix {task_id}",
    )
    assert cmd[0] == "claude"
    assert "-p" in cmd
    assert "SPEC-A-001" in " ".join(cmd)
    assert "60" in cmd


# --- make_verify / make_fix subprocess wrappers ---


def test_make_verify_reads_report_json(tmp_path: Path) -> None:
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    report = verify_dir / "SPEC-A-001.json"

    def build(task_id: str) -> list[str]:
        code = (
            "import json, pathlib; "
            f"p = pathlib.Path({str(report)!r}); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            'p.write_text(json.dumps({"task_id": "SPEC-A-001", '
            '"status": "pass", "reasons": []}))'
        )
        return [sys.executable, "-c", code]

    verify = m.make_verify(build, verify_dir)
    status, path = verify("SPEC-A-001")
    assert status == "pass"
    assert path == str(report)


def test_make_verify_returns_fail_when_report_says_fail(tmp_path: Path) -> None:
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    report = verify_dir / "SPEC-A-001.json"

    def build(task_id: str) -> list[str]:
        code = (
            "import json, pathlib; "
            f"p = pathlib.Path({str(report)!r}); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            'p.write_text(json.dumps({"task_id": "SPEC-A-001", '
            '"status": "fail", "reasons": ["pytest exit=1"]}))'
        )
        return [sys.executable, "-c", code]

    verify = m.make_verify(build, verify_dir)
    status, _ = verify("SPEC-A-001")
    assert status == "fail"


def test_make_verify_returns_error_when_report_missing(tmp_path: Path) -> None:
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    verify_dir.mkdir()

    def build(task_id: str) -> list[str]:
        # Verifier subprocess exits 0 but never writes the report.
        return [sys.executable, "-c", "pass"]

    verify = m.make_verify(build, verify_dir)
    status, _ = verify("SPEC-A-001")
    assert status == "error"


def test_make_verify_clears_stale_report(tmp_path: Path) -> None:
    """A previous run's report must NOT be mistaken for a fresh pass."""
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    verify_dir.mkdir()
    stale = verify_dir / "SPEC-A-001.json"
    stale.write_text('{"task_id": "SPEC-A-001", "status": "pass"}')

    def build(task_id: str) -> list[str]:
        # Verifier doesn't write anything; fresh-miss must surface as error.
        return [sys.executable, "-c", "pass"]

    verify = m.make_verify(build, verify_dir)
    status, _ = verify("SPEC-A-001")
    assert status == "error"


def test_make_fix_sets_env_and_returns_exit_code(tmp_path: Path) -> None:
    import run_task_driver as m

    marker = tmp_path / "env_dump.txt"

    def build(task_id: str) -> list[str]:
        code = (
            "import os, sys; "
            f"open(r'{marker}', 'w').write("
            "os.environ.get('AVS_CURRENT_TASK', '') + '|' + "
            "os.environ.get('AVS_FIX_REPORT', '')); "
            "sys.exit(5)"
        )
        return [sys.executable, "-c", code]

    fix = m.make_fix(build)
    rc = fix("SPEC-A-007", "/tmp/.verify/SPEC-A-007.json")
    assert rc == 5
    assert marker.read_text() == "SPEC-A-007|/tmp/.verify/SPEC-A-007.json"


# --- Reviewer agent (P1.1): P0 findings trigger fixer ---


def test_loop_runs_reviewer_after_verify_pass() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001", None]
    events: list[tuple] = []

    def pick():
        return queue.pop(0)

    def dispatch(tid):
        events.append(("dispatch", tid))
        return 0

    def verify(tid):
        events.append(("verify", tid))
        return ("pass", f".verify/{tid}.json")

    def fix(tid, rpt):  # pragma: no cover
        events.append(("fix", tid, rpt))
        return 0

    def review(tid):
        events.append(("review", tid))
        return ("pass", f".verify/{tid}.review.json")

    m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        review=review,
        max_fix_rounds=3,
        max_review_rounds=3,
    )
    kinds = [e[0] for e in events]
    assert kinds == ["dispatch", "verify", "review"]


def test_loop_skips_reviewer_when_verify_fails_exhausted() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001"]
    events: list[str] = []

    def pick():
        return queue.pop(0) if queue else None

    def dispatch(tid):
        return 0

    def verify(tid):
        events.append("v")
        return ("fail", "r")

    def fix(tid, rpt):
        events.append("f")
        return 0

    def review(tid):  # pragma: no cover - must not be called
        events.append("R")
        return ("pass", "r")

    m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        review=review,
        max_fix_rounds=1,
        max_review_rounds=3,
    )
    assert "R" not in events


def test_loop_review_p0_triggers_fixer_then_rereview() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001", None]
    review_results = [("fail", "rv1"), ("pass", "rv2")]
    events: list[tuple] = []

    def pick():
        return queue.pop(0)

    def dispatch(tid):
        return 0

    def verify(tid):
        events.append(("verify", tid))
        return ("pass", "vr")

    def fix(tid, rpt):
        events.append(("fix", tid, rpt))
        return 0

    def review(tid):
        events.append(("review", tid))
        return review_results.pop(0)

    m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        review=review,
        max_fix_rounds=3,
        max_review_rounds=3,
    )
    kinds = [e[0] for e in events]
    assert kinds == ["verify", "review", "fix", "review"]
    assert events[2] == ("fix", "SPEC-A-001", "rv1")


def test_loop_review_exhausts_rounds_reports_review_exhausted() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001"]
    events: list[str] = []

    def pick():
        return queue.pop(0) if queue else None

    def dispatch(tid):
        return 0

    def verify(tid):
        events.append("v")
        return ("pass", "vr")

    def fix(tid, rpt):
        events.append("f")
        return 0

    def review(tid):
        events.append("R")
        return ("fail", "rr")

    result = m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        review=review,
        max_fix_rounds=3,
        max_review_rounds=2,
    )
    # v (initial pass) then R fail -> f -> R fail -> f -> R fail -> stop
    assert events.count("R") == 3
    assert events.count("f") == 2
    assert result["reason"] == "review_exhausted"
    assert result["task_id"] == "SPEC-A-001"
    assert result["review_rounds_used"] == 2


def test_loop_review_fixer_nonzero_stops() -> None:
    import run_task_driver as m

    queue = ["SPEC-A-001"]

    def pick():
        return queue.pop(0) if queue else None

    def dispatch(tid):
        return 0

    def verify(tid):
        return ("pass", "vr")

    def fix(tid, rpt):
        return 9

    def review(tid):
        return ("fail", "rr")

    result = m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        review=review,
        max_fix_rounds=3,
        max_review_rounds=3,
    )
    assert result["reason"] == "fix_failed"
    assert result["exit_code"] == 9


def test_loop_review_skipped_when_callable_none() -> None:
    """Backward compat: review=None means no review stage."""
    import run_task_driver as m

    queue = ["SPEC-A-001", None]
    events: list[str] = []

    def pick():
        return queue.pop(0)

    def dispatch(tid):
        events.append("d")
        return 0

    def verify(tid):
        events.append("v")
        return ("pass", "vr")

    def fix(tid, rpt):
        return 0

    m.run_loop(
        pick_next=pick,
        dispatch=dispatch,
        max_tasks=5,
        stop_on_error=True,
        log=lambda _: None,
        verify=verify,
        fix=fix,
        max_fix_rounds=3,
    )
    assert events == ["d", "v"]


def test_build_reviewer_command_structure() -> None:
    import run_task_driver as m

    cmd = m.build_reviewer_command(
        program="claude",
        task_id="SPEC-A-001",
        max_turns=40,
        prompt_template="review {task_id}",
    )
    assert cmd[0] == "claude"
    assert "-p" in cmd
    assert "SPEC-A-001" in " ".join(cmd)
    assert "--max-turns" in cmd
    assert "40" in cmd


def test_make_review_reads_report_json(tmp_path: Path) -> None:
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    report = verify_dir / "SPEC-A-001.review.json"

    def build(task_id: str) -> list[str]:
        code = (
            "import json, pathlib; "
            f"p = pathlib.Path({str(report)!r}); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            'p.write_text(json.dumps({"task_id": "SPEC-A-001", '
            '"status": "pass", "findings": []}))'
        )
        return [sys.executable, "-c", code]

    review = m.make_review(build, verify_dir)
    status, path = review("SPEC-A-001")
    assert status == "pass"
    assert path == str(report)


def test_make_review_fail_when_p0_finding_present(tmp_path: Path) -> None:
    """P0 findings must flip status to fail even if reviewer wrote pass."""
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    report = verify_dir / "SPEC-A-001.review.json"

    def build(task_id: str) -> list[str]:
        code = (
            "import json, pathlib; "
            f"p = pathlib.Path({str(report)!r}); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            'p.write_text(json.dumps({"task_id": "SPEC-A-001", '
            '"status": "pass", '
            '"findings": [{"severity": "P0", "message": "circular import"}]}))'
        )
        return [sys.executable, "-c", code]

    review = m.make_review(build, verify_dir)
    status, _ = review("SPEC-A-001")
    assert status == "fail"


def test_make_review_pass_when_only_p1_p2_findings(tmp_path: Path) -> None:
    """P1/P2 findings are advisory; overall status stays pass."""
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    report = verify_dir / "SPEC-A-001.review.json"

    def build(task_id: str) -> list[str]:
        code = (
            "import json, pathlib; "
            f"p = pathlib.Path({str(report)!r}); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            'p.write_text(json.dumps({"task_id": "SPEC-A-001", '
            '"status": "pass", '
            '"findings": ['
            '{"severity": "P1", "message": "long function"},'
            '{"severity": "P2", "message": "naming nit"}'
            "]}))"
        )
        return [sys.executable, "-c", code]

    review = m.make_review(build, verify_dir)
    status, _ = review("SPEC-A-001")
    assert status == "pass"


def test_make_review_clears_stale_report(tmp_path: Path) -> None:
    import run_task_driver as m

    verify_dir = tmp_path / ".verify"
    verify_dir.mkdir()
    stale = verify_dir / "SPEC-A-001.review.json"
    stale.write_text('{"task_id": "SPEC-A-001", "status": "pass", "findings": []}')

    def build(task_id: str) -> list[str]:
        return [sys.executable, "-c", "pass"]

    review = m.make_review(build, verify_dir)
    status, _ = review("SPEC-A-001")
    assert status == "error"


# --- Parallel batch picking (P1.3) ---


def test_pick_next_batch_independent_tasks(tmp_path: Path) -> None:
    """pick_next_batch returns up to N ready tasks with disjoint allowed_files."""
    import pick_next_task as p

    (tmp_path / "tasks" / "SPEC-A").mkdir(parents=True)
    (tmp_path / "tasks" / "SPEC-A" / "A-001-x.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-001]
            ## Metadata
            - **task_id**: SPEC-A-001
            - **depends_on**: []
            - **priority**: P0
            - **allowed_files**: [src/shared/a.py, tests/test_a.py]
            """
        )
    )
    (tmp_path / "tasks" / "SPEC-A" / "A-002-y.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-002]
            ## Metadata
            - **task_id**: SPEC-A-002
            - **depends_on**: []
            - **priority**: P0
            - **allowed_files**: [src/shared/b.py, tests/test_b.py]
            """
        )
    )
    (tmp_path / "PROGRESS.md").write_text("")
    batch = p.pick_next_batch(tmp_path, limit=2)
    assert set(batch) == {"SPEC-A-001", "SPEC-A-002"}


def test_pick_next_batch_skips_overlapping_files(tmp_path: Path) -> None:
    """Two tasks that both touch the same file must not share a batch."""
    import pick_next_task as p

    (tmp_path / "tasks" / "SPEC-A").mkdir(parents=True)
    (tmp_path / "tasks" / "SPEC-A" / "A-001-x.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-001]
            ## Metadata
            - **task_id**: SPEC-A-001
            - **depends_on**: []
            - **priority**: P0
            - **allowed_files**: [src/shared/a.py]
            """
        )
    )
    (tmp_path / "tasks" / "SPEC-A" / "A-002-y.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-002]
            ## Metadata
            - **task_id**: SPEC-A-002
            - **depends_on**: []
            - **priority**: P0
            - **allowed_files**: [src/shared/a.py, src/shared/b.py]
            """
        )
    )
    (tmp_path / "PROGRESS.md").write_text("")
    batch = p.pick_next_batch(tmp_path, limit=2)
    assert batch == ["SPEC-A-001"]


def test_pick_next_batch_respects_dependencies(tmp_path: Path) -> None:
    import pick_next_task as p

    (tmp_path / "tasks" / "SPEC-A").mkdir(parents=True)
    (tmp_path / "tasks" / "SPEC-A" / "A-001-x.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-001]
            ## Metadata
            - **task_id**: SPEC-A-001
            - **depends_on**: []
            - **priority**: P0
            - **allowed_files**: [src/shared/a.py]
            """
        )
    )
    (tmp_path / "tasks" / "SPEC-A" / "A-002-y.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-002]
            ## Metadata
            - **task_id**: SPEC-A-002
            - **depends_on**: [SPEC-A-001]
            - **priority**: P0
            - **allowed_files**: [src/shared/b.py]
            """
        )
    )
    (tmp_path / "PROGRESS.md").write_text("")
    batch = p.pick_next_batch(tmp_path, limit=2)
    assert batch == ["SPEC-A-001"]


def test_pick_next_batch_limit_one_matches_pick_next(tmp_path: Path) -> None:
    """limit=1 must return same single id as pick_next."""
    import pick_next_task as p

    (tmp_path / "tasks" / "SPEC-A").mkdir(parents=True)
    (tmp_path / "tasks" / "SPEC-A" / "A-001-x.md").write_text(
        textwrap.dedent(
            """\
            # [SPEC-A-001]
            ## Metadata
            - **task_id**: SPEC-A-001
            - **depends_on**: []
            - **priority**: P0
            """
        )
    )
    (tmp_path / "PROGRESS.md").write_text("")
    one = p.pick_next(tmp_path)
    batch = p.pick_next_batch(tmp_path, limit=1)
    assert batch == [one]


# --- Parallel run loop (P1.3) ---


def test_run_parallel_loop_dispatches_batch_concurrently() -> None:
    import run_task_driver as m

    # Picker returns batches: first [A,B], then [] to stop.
    queue = [["SPEC-A-001", "SPEC-A-002"], []]
    dispatched: list[str] = []

    def pick_batch(limit):
        return queue.pop(0) if queue else []

    def dispatch(tid):
        dispatched.append(tid)
        return 0

    def verify(tid):
        return ("pass", f".verify/{tid}.json")

    result = m.run_parallel_loop(
        pick_batch=pick_batch,
        dispatch=dispatch,
        verify=verify,
        fix=lambda t, r: 0,
        review=None,
        max_tasks=5,
        parallel=2,
        stop_on_error=True,
        log=lambda _: None,
        max_fix_rounds=3,
        max_review_rounds=3,
    )
    assert set(dispatched) == {"SPEC-A-001", "SPEC-A-002"}
    assert result["reason"] == "no_tasks_ready"
    assert result["iterations"] == 2


def test_run_parallel_loop_respects_max_tasks() -> None:
    import run_task_driver as m

    queue = [
        ["SPEC-A-001", "SPEC-A-002", "SPEC-A-003"],
        ["SPEC-A-004"],
    ]
    dispatched: list[str] = []

    def pick_batch(limit):
        return queue.pop(0) if queue else []

    def dispatch(tid):
        dispatched.append(tid)
        return 0

    def verify(tid):
        return ("pass", "r")

    result = m.run_parallel_loop(
        pick_batch=pick_batch,
        dispatch=dispatch,
        verify=verify,
        fix=lambda t, r: 0,
        review=None,
        max_tasks=2,
        parallel=3,
        stop_on_error=True,
        log=lambda _: None,
        max_fix_rounds=3,
        max_review_rounds=3,
    )
    # Only 2 tasks should run despite batch of 3.
    assert len(dispatched) == 2
    assert result["reason"] == "max_tasks_reached"
