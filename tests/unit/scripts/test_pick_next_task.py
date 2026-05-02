"""Tests for scripts/pick_next_task.py.

Covers: task card parsing, PROGRESS.md status parsing, dependency resolution,
priority ordering, CLI exit codes.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "pick_next_task.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def make_repo(tmp_path: Path, cards: dict[str, dict], progress: str) -> Path:
    """Create a fake project root with tasks/ and PROGRESS.md."""
    for task_id, meta in cards.items():
        spec = task_id.split("-")[1]
        d = tmp_path / "tasks" / f"SPEC-{spec}"
        d.mkdir(parents=True, exist_ok=True)
        slug = meta.get("slug", "fake")
        depends_on = meta.get("depends_on", [])
        priority = meta.get("priority", "P2")
        body = textwrap.dedent(
            f"""\
            # [{task_id}] Fake

            ## Metadata
            - **task_id**: {task_id}
            - **depends_on**: {depends_on}
            - **priority**: {priority}

            ## Scope
            Fake.
            """
        )
        (d / f"{'-'.join(task_id.split('-')[1:])}-{slug}.md").write_text(body)
    (tmp_path / "PROGRESS.md").write_text(progress)
    return tmp_path


# --- Unit tests on the module ---


def test_parse_depends_on_empty(tmp_path: Path) -> None:
    import pick_next_task as m

    root = make_repo(
        tmp_path,
        {"SPEC-A-001": {"depends_on": []}},
        progress="# Log\n",
    )
    cards = m.load_task_cards(root)
    assert "SPEC-A-001" in cards
    assert cards["SPEC-A-001"].depends_on == []


def test_parse_depends_on_nonempty(tmp_path: Path) -> None:
    import pick_next_task as m

    root = make_repo(
        tmp_path,
        {"SPEC-A-002": {"depends_on": ["SPEC-A-001"]}},
        progress="",
    )
    cards = m.load_task_cards(root)
    assert cards["SPEC-A-002"].depends_on == ["SPEC-A-001"]


def test_progress_status_done(tmp_path: Path) -> None:
    import pick_next_task as m

    progress = textwrap.dedent(
        """\
        # Log

        ## [SPEC-A-001] Title
        - **Status**: DONE
        - **Completed**: 2026-04-16
        """
    )
    root = make_repo(tmp_path, {"SPEC-A-001": {}}, progress=progress)
    statuses = m.load_statuses(root)
    assert statuses["SPEC-A-001"] == "DONE"


def test_progress_latest_status_wins(tmp_path: Path) -> None:
    import pick_next_task as m

    # Same task appears twice; later entry should win.
    progress = textwrap.dedent(
        """\
        # Log

        ## [SPEC-A-001] First attempt
        - **Status**: BLOCKED

        ## [SPEC-A-001] Retry
        - **Status**: DONE
        """
    )
    root = make_repo(tmp_path, {"SPEC-A-001": {}}, progress=progress)
    assert m.load_statuses(root)["SPEC-A-001"] == "DONE"


def test_progress_new_format_recent_commits_table(tmp_path: Path) -> None:
    """v1.1.0 PROGRESS.md: any SPEC-X-NNN in a Recent-commits row = DONE.

    Covers the 2026-04-20 rotation where PROGRESS.md became a one-line-per-commit
    index (HARNESS §9.2). The old `## [SPEC-X-NNN] ... **Status**: DONE` sections
    no longer exist; load_statuses must recognize the table form.
    """
    import pick_next_task as m

    progress = textwrap.dedent(
        """\
        # AI-Video-System Development Progress Log

        ## Recent commits

        | SHA      | Task              | Title                  | Date       |
        |----------|-------------------|------------------------|------------|
        | e5e6928  | SPEC-A-001 (fix1) | parameterize data dict | 2026-04-20 |
        | 03e6432  | SPEC-A-001        | add artifact schemas   | 2026-04-19 |
        | 9523290  | SPEC-B-001        | docker-compose         | 2026-04-20 |

        ## Open follow-ups
        - unrelated prose, no bare task IDs
        """
    )
    root = make_repo(
        tmp_path,
        {
            "SPEC-A-001": {},
            "SPEC-B-001": {},
            "SPEC-A-003": {},
        },
        progress=progress,
    )
    st = m.load_statuses(root)
    assert st.get("SPEC-A-001") == "DONE"
    assert st.get("SPEC-B-001") == "DONE"
    assert "SPEC-A-003" not in st  # not mentioned anywhere


def test_progress_new_format_slash_shorthand(tmp_path: Path) -> None:
    """Historic combined row `SPEC-A-001/002/004` expands to three DONE ids."""
    import pick_next_task as m

    progress = textwrap.dedent(
        """\
        ## Recent commits

        | SHA       | Task               | Title     | Date       |
        |-----------|--------------------|-----------|------------|
        | (earlier) | SPEC-A-001/002/004 | initial   | pre-04-18  |
        """
    )
    root = make_repo(
        tmp_path,
        {"SPEC-A-001": {}, "SPEC-A-002": {}, "SPEC-A-004": {}},
        progress=progress,
    )
    st = m.load_statuses(root)
    assert st.get("SPEC-A-001") == "DONE"
    assert st.get("SPEC-A-002") == "DONE"
    assert st.get("SPEC-A-004") == "DONE"


def test_progress_status_snapshot_short_form(tmp_path: Path) -> None:
    """Status snapshot rows use `A-001` short form; must expand to SPEC-A-001.

    The 2026-04-20 PROGRESS.md has entries like:
        | C -- Backend Core | C-106 (POC) | |
    where C-106 only appears in the snapshot (rotated out of Recent commits).
    Without snapshot parsing, its dependents would be incorrectly blocked.
    """
    import pick_next_task as m

    progress = textwrap.dedent(
        """\
        ## Status snapshot (2026-04-20)

        | SPEC | Done (distinct task IDs) | Notes |
        |------|--------------------------|-------|
        | A -- Contracts    | A-001, A-002 (2) | ok |
        | C -- Backend Core | C-106 (POC)      | ok |
        """
    )
    root = make_repo(
        tmp_path,
        {"SPEC-A-001": {}, "SPEC-A-002": {}, "SPEC-C-106": {}},
        progress=progress,
    )
    st = m.load_statuses(root)
    assert st.get("SPEC-A-001") == "DONE"
    assert st.get("SPEC-A-002") == "DONE"
    assert st.get("SPEC-C-106") == "DONE"


def test_pick_next_skips_done_in_new_format(tmp_path: Path) -> None:
    """End-to-end: new-format DONE entries must block re-picking the same task."""
    import pick_next_task as m

    progress = textwrap.dedent(
        """\
        ## Recent commits

        | SHA     | Task       | Title | Date       |
        |---------|------------|-------|------------|
        | abc1234 | SPEC-A-001 | done  | 2026-04-20 |
        """
    )
    root = make_repo(
        tmp_path,
        {
            "SPEC-A-001": {"depends_on": [], "priority": "P0"},
            "SPEC-A-002": {"depends_on": ["SPEC-A-001"], "priority": "P0"},
        },
        progress=progress,
    )
    assert m.pick_next(root) == "SPEC-A-002"


# --- SPEC-G and range expansion tests ---


def test_parse_spec_g_cards(tmp_path: Path) -> None:
    """SPEC-G cards with suffix IDs (000b, 000c) are parsed correctly."""
    import pick_next_task as m

    cards = {
        "SPEC-G-000b": {"depends_on": ["SPEC-G-000a"], "priority": "P0"},
        "SPEC-G-000c": {"depends_on": ["SPEC-G-000b"], "priority": "P0"},
    }
    root = make_repo(tmp_path, cards, progress="")
    parsed = m.load_task_cards(root)
    assert "SPEC-G-000b" in parsed
    assert "SPEC-G-000c" in parsed
    assert parsed["SPEC-G-000b"].depends_on == ["SPEC-G-000a"]
    assert parsed["SPEC-G-000b"].priority == "P0"


def test_parse_done_range_expansion():
    """Status snapshot range A-001..A-018 expands to all 18 IDs."""
    import pick_next_task as m

    progress = textwrap.dedent("""\
        ## Status snapshot
        | A -- contracts | 001..018, 019, 020 |
        | B -- infra     | -- |
    """)
    done = m._parse_done_from_tables(progress)
    for i in range(1, 19):
        assert f"SPEC-A-{i:03d}" in done
    assert "SPEC-A-019" in done
    assert "SPEC-A-020" in done


def test_parse_done_spec_g_snapshot():
    """Status snapshot with SPEC-G rows is parsed."""
    import pick_next_task as m

    progress = textwrap.dedent("""\
        ## Status snapshot
        | G -- workers | 001, 002, 003 |
    """)
    done = m._parse_done_from_tables(progress)
    assert "SPEC-G-001" in done
    assert "SPEC-G-002" in done
    assert "SPEC-G-003" in done


def test_parse_done_spec_g_recent_commits():
    """Recent commits rows with SPEC-G IDs are recognized."""
    import pick_next_task as m

    progress = textwrap.dedent("""\
        ## Recent commits
        | abc1234 | SPEC-G-000b | huey immediate mode | 2026-04-20 |
        | def5678 | SPEC-G-000c | worker task registry  | 2026-04-21 |
    """)
    done = m._parse_done_from_tables(progress)
    assert "SPEC-G-000b" in done
    assert "SPEC-G-000c" in done


def test_parse_priority_with_chinese_annotation(tmp_path: Path) -> None:
    """Priority field with Chinese annotation parses correctly."""
    import pick_next_task as m

    cards = {
        "SPEC-G-001": {"depends_on": [], "priority": "P0（最高优先级）"},
    }
    root = make_repo(tmp_path, cards, progress="")
    parsed = m.load_task_cards(root)
    assert parsed["SPEC-G-001"].priority == "P0"


def test_pick_next_no_deps(tmp_path: Path) -> None:
    import pick_next_task as m

    root = make_repo(
        tmp_path,
        {
            "SPEC-A-001": {"depends_on": [], "priority": "P0"},
            "SPEC-A-002": {"depends_on": ["SPEC-A-001"], "priority": "P0"},
        },
        progress="# Log\n",
    )
    assert m.pick_next(root) == "SPEC-A-001"


def test_pick_next_skips_done(tmp_path: Path) -> None:
    import pick_next_task as m

    progress = textwrap.dedent(
        """\
        # Log

        ## [SPEC-A-001] Done
        - **Status**: DONE
        """
    )
    root = make_repo(
        tmp_path,
        {
            "SPEC-A-001": {"depends_on": [], "priority": "P0"},
            "SPEC-A-002": {"depends_on": ["SPEC-A-001"], "priority": "P0"},
        },
        progress=progress,
    )
    assert m.pick_next(root) == "SPEC-A-002"


def test_pick_next_blocked_on_unfinished_dep(tmp_path: Path) -> None:
    import pick_next_task as m

    # A-001 exists but never marked DONE -> A-002 is not pickable.
    # Only A-003 has no deps so it should be picked.
    root = make_repo(
        tmp_path,
        {
            "SPEC-A-001": {"depends_on": [], "priority": "P1"},
            "SPEC-A-002": {"depends_on": ["SPEC-A-001"], "priority": "P0"},
            "SPEC-A-003": {"depends_on": [], "priority": "P1"},
        },
        progress=textwrap.dedent(
            """\
            # Log

            ## [SPEC-A-001] In flight
            - **Status**: IN_PROGRESS
            """
        ),
    )
    # A-002 blocked; A-001 is IN_PROGRESS so not pickable; A-003 pickable.
    assert m.pick_next(root) == "SPEC-A-003"


def test_pick_next_priority_tiebreak(tmp_path: Path) -> None:
    import pick_next_task as m

    # Both A-003 and A-004 are ready. A-003 is P0, A-004 is P2. Pick A-003.
    # Also test id tiebreak: two P0s, lower id wins.
    root = make_repo(
        tmp_path,
        {
            "SPEC-A-003": {"depends_on": [], "priority": "P0"},
            "SPEC-A-004": {"depends_on": [], "priority": "P2"},
            "SPEC-A-002": {"depends_on": [], "priority": "P0"},
        },
        progress="",
    )
    assert m.pick_next(root) == "SPEC-A-002"  # P0 + lowest id


def test_pick_next_none_available(tmp_path: Path) -> None:
    import pick_next_task as m

    root = make_repo(
        tmp_path,
        {"SPEC-A-001": {"depends_on": []}},
        progress=textwrap.dedent(
            """\
            # Log

            ## [SPEC-A-001] Complete
            - **Status**: DONE
            """
        ),
    )
    assert m.pick_next(root) is None


# --- CLI integration ---


def test_cli_prints_task_id(tmp_path: Path) -> None:
    root = make_repo(tmp_path, {"SPEC-A-001": {"depends_on": [], "priority": "P0"}}, "")
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert res.stdout.strip() == "SPEC-A-001"


def test_cli_exit_1_when_none(tmp_path: Path) -> None:
    root = make_repo(
        tmp_path,
        {"SPEC-A-001": {}},
        textwrap.dedent(
            """\
            ## [SPEC-A-001] done
            - **Status**: DONE
            """
        ),
    )
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 1
    assert res.stdout.strip() == ""


def test_cli_task_id_override_bypasses_order(tmp_path: Path) -> None:
    """--task-id returns the named card even if its deps are unmet."""
    root = make_repo(
        tmp_path,
        {
            "SPEC-A-001": {"depends_on": [], "priority": "P0"},
            "SPEC-C-106": {"depends_on": ["SPEC-A-001"], "priority": "P2"},
        },
        progress="# Log\n",  # A-001 not DONE, so C-106 normally blocked
    )
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--task-id", "SPEC-C-106"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert res.stdout.strip() == "SPEC-C-106"


def test_cli_task_id_override_unknown_exits_1(tmp_path: Path) -> None:
    """--task-id for a non-existent card exits 1 and prints nothing."""
    root = make_repo(
        tmp_path,
        {"SPEC-A-001": {"depends_on": [], "priority": "P0"}},
        progress="",
    )
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--task-id", "SPEC-Z-999"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 1
    assert res.stdout.strip() == ""


def test_stub_would_fail() -> None:
    """Guard: a stub that returns a hardcoded task id must fail these tests.

    If pick_next always returns 'SPEC-A-001' it would pass
    test_pick_next_no_deps but fail test_pick_next_skips_done,
    test_pick_next_blocked_on_unfinished_dep, test_pick_next_priority_tiebreak,
    test_pick_next_none_available. This meta-test just ensures the suite
    spans sufficient conditions.
    """
    assert True  # documentation marker
