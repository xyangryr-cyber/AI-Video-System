"""Done-task skip-stub gate.

Scans the test files corresponding to tasks PROGRESS.md marks as Done and
reports any remaining `pytest.skip("NOT IMPLEMENTED ...")` stubs. Exits
non-zero if ANY stub remains, so CI and the executing AI can detect a
"Done task with fake-passing tests" regression.

Original purpose (2026-04-20): completion gate for
tasks/SPEC-A/REDO-real-tests-plan.md. Since then TARGET_FILES grows by one
line per `[SPEC-X-NNN]` commit -- append the task's test file(s) as part
of each GREEN commit. Do NOT delete: this gate now enforces a durable
invariant across the whole project.

Usage:
    .venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py

Exit codes:
    0 -- no skip stubs remain in any target file (gate passes)
    1 -- at least one stub remains (gate fails, work unfinished)
    2 -- a target file is missing (misconfiguration)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# One entry per Done task's test file(s). Append when a [SPEC-X-NNN] commit
# lands. Keep grouped by SPEC for readability.
TARGET_FILES = [
    # SPEC-A (contracts) -- REDO plan 2026-04-20 + backfills 2026-04-24
    "tests/unit/contracts/test_spec_a_001.py",
    "tests/unit/contracts/test_spec_a_002.py",
    "tests/unit/contracts/test_spec_a_003.py",
    "tests/unit/contracts/test_spec_a_004.py",
    "tests/unit/contracts/test_spec_a_005.py",
    "tests/unit/contracts/test_spec_a_006.py",
    "tests/unit/contracts/test_spec_a_007.py",
    "tests/unit/contracts/test_spec_a_008.py",
    "tests/unit/contracts/test_spec_a_009.py",
    "tests/unit/contracts/test_spec_a_010.py",
    "tests/unit/contracts/test_spec_a_011.py",
    "tests/unit/contracts/test_spec_a_012.py",
    "tests/unit/contracts/test_spec_a_013.py",
    "tests/unit/contracts/test_spec_a_014.py",
    "tests/unit/contracts/test_spec_a_015.py",
    "tests/unit/contracts/test_spec_a_016.py",
    "tests/unit/contracts/test_spec_a_017.py",
    "tests/unit/contracts/test_spec_a_018.py",
    "tests/unit/contracts/test_spec_a_100.py",
    "tests/unit/contracts/test_spec_a_101.py",
    "tests/unit/contracts/test_spec_a_102.py",
    "tests/unit/contracts/test_spec_a_103.py",
    "tests/unit/contracts/test_spec_a_104.py",
    "tests/unit/contracts/test_spec_a_106.py",
    "tests/unit/contracts/test_spec_a_107.py",
    "tests/unit/contracts/test_spec_a_108.py",
    "tests/unit/contracts/test_spec_a_109.py",
    "tests/unit/contracts/test_spec_a_110.py",
    "tests/unit/contracts/test_spec_a_111.py",
    "tests/unit/contracts/test_spec_a_112.py",
    "tests/unit/contracts/test_spec_a_113.py",
    "tests/unit/contracts/test_spec_a_114.py",
    "tests/unit/contracts/test_spec_a_115.py",
    # SPEC-B (infra)
    "tests/unit/infra/test_spec_b_001.py",
    "tests/unit/infra/test_spec_b_002.py",
    "tests/unit/infra/test_spec_b_003.py",
    "tests/unit/infra/test_spec_b_004.py",
    "tests/unit/infra/test_spec_b_005.py",
    "tests/unit/infra/test_spec_b_100.py",
    # SPEC-D pipeline (added per D-003 commit)
    "tests/unit/pipeline/test_spec_d_001.py",
    "tests/unit/pipeline/test_spec_d_002.py",
    "tests/unit/pipeline/test_spec_d_003.py",
    "tests/unit/pipeline/test_spec_d_004.py",
    "tests/unit/pipeline/test_spec_d_005.py",
    "tests/unit/pipeline/test_spec_d_006.py",
    "tests/unit/pipeline/test_spec_d_007.py",
    "tests/unit/pipeline/test_spec_d_008.py",
    "tests/unit/pipeline/test_spec_d_009.py",
    "tests/unit/pipeline/test_spec_d_010.py",
    "tests/unit/pipeline/test_spec_d_011.py",
    "tests/unit/pipeline/test_spec_d_012.py",
    "tests/unit/pipeline/test_spec_d_013.py",
    "tests/unit/pipeline/test_spec_d_014.py",
    "tests/unit/pipeline/test_spec_d_015.py",
    "tests/unit/pipeline/test_spec_d_100.py",
    "tests/unit/pipeline/test_spec_d_101.py",
    "tests/unit/pipeline/test_spec_d_102.py",
    "tests/unit/pipeline/test_spec_d_103.py",
    # SPEC-C (backend core) -- skip stubs replaced with re-exports 2026-04-25
    "tests/unit/backend-core/test_spec_c_001.py",
    "tests/unit/backend-core/test_spec_c_002.py",
    "tests/unit/backend-core/test_spec_c_003.py",
    "tests/unit/backend-core/test_spec_c_004.py",
    "tests/unit/backend-core/test_spec_c_005.py",
    "tests/unit/backend-core/test_spec_c_006.py",
    "tests/unit/backend-core/test_spec_c_007.py",
    "tests/unit/backend-core/test_spec_c_008.py",
    "tests/unit/backend-core/test_spec_c_009.py",
    "tests/unit/backend-core/test_spec_c_010.py",
    "tests/unit/backend-core/test_spec_c_011.py",
    "tests/unit/backend-core/test_spec_c_012.py",
    "tests/unit/backend-core/test_spec_c_013.py",
    "tests/unit/backend-core/test_spec_c_014.py",
    "tests/unit/backend-core/test_spec_c_015.py",
    "tests/unit/backend-core/test_spec_c_016.py",
    "tests/unit/backend-core/test_spec_c_017.py",
    "tests/unit/backend-core/test_spec_c_018.py",
    "tests/unit/backend-core/test_spec_c_019.py",
    "tests/unit/backend-core/test_spec_c_020.py",
    "tests/unit/backend-core/test_spec_c_021.py",
    "tests/unit/backend-core/test_spec_c_022.py",
    "tests/unit/backend-core/test_spec_c_100.py",
    "tests/unit/backend-core/test_spec_c_101.py",
    "tests/unit/backend-core/test_spec_c_102.py",
    "tests/unit/backend-core/test_spec_c_103.py",
    "tests/unit/backend-core/test_spec_c_104.py",
    "tests/unit/backend-core/test_spec_c_105.py",
    # SPEC-F (media render)
    "tests/unit/media-render/test_spec_f_007.py",
    "tests/unit/media-render/test_spec_f_009.py",
    "tests/unit/media-render/test_spec_f_014.py",
    "tests/unit/media-render/test_spec_f_010.py",
    "tests/unit/media-render/test_spec_f_012.py",
    "tests/unit/media-render/test_spec_f_011.py",
    # SPEC-E (frontend)
    "tests/unit/frontend/test_spec_e_011.py",
]

# Matches both `pytest.skip(...)` direct calls and decorator forms when the
# reason string contains "NOT IMPLEMENTED". A legitimate future skip (e.g.
# platform-gated) uses a different reason and so will not be flagged.
STUB_PATTERN = re.compile(r"pytest\.skip\s*\(\s*[\"']NOT IMPLEMENTED")


def count_stubs(path: Path) -> int:
    return len(STUB_PATTERN.findall(path.read_text(encoding="utf-8")))


def main() -> int:
    failures: list[tuple[str, int]] = []
    missing: list[str] = []

    for rel in TARGET_FILES:
        path = REPO_ROOT / rel
        if not path.is_file():
            missing.append(rel)
            continue
        n = count_stubs(path)
        status = "OK " if n == 0 else "BAD"
        print(f"[{status}] {n:3d} stub(s)  {rel}")
        if n > 0:
            failures.append((rel, n))

    print()
    if missing:
        print(f"ERROR: {len(missing)} target file(s) missing:")
        for m in missing:
            print(f"  - {m}")
        return 2

    if failures:
        total = sum(n for _, n in failures)
        print(f"GATE FAILED: {total} skip stub(s) remain across {len(failures)} file(s).")
        print("See tasks/SPEC-A/REDO-real-tests-plan.md for the execution plan.")
        return 1

    print(f"GATE PASSED: all {len(TARGET_FILES)} target files are stub-free.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
