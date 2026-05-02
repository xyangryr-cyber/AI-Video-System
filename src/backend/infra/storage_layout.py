"""Project-root directory layout pre-creation ([SPEC-B-014]).

Authority:
  docs/specs/SPEC-B-infra-deploy.md B-AUDP7A-2, §1.2 project dir tree.
  docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-2.

Creates phase_0..phase_11 (v3.15 existing) plus the v3.17 new-phase
sub-directories:
  phase_5/bgm_candidates/
  phase_6/sfx_applied_segments/
  phase_7a/
  phase_7a/verified_materials/
  phase_7a/chart_materials/

Idempotent: re-running on an existing project keeps files in place.
"""

from __future__ import annotations

from pathlib import Path

# v3.15 phase dirs — the 12 base phase folders.
V315_PHASE_DIRS: tuple[str, ...] = tuple(f"phase_{i}" for i in range(12))

# v3.17 additions. phase_7a is a whole new phase; the nested lists are the
# sub-directories that must be pre-created under each parent.
V317_NEW_PHASE_DIRS: tuple[str, ...] = ("phase_7a",)
V317_NEW_SUBDIRS: dict[str, tuple[str, ...]] = {
    "phase_5": ("bgm_candidates",),
    "phase_6": ("sfx_applied_segments",),
    "phase_7a": ("verified_materials", "chart_materials"),
}


def create_project_layout(project_root: Path) -> Path:
    """Create the full v3.17 project directory layout under ``project_root``.

    Returns the project root as a ``Path``. Creates missing directories and
    leaves existing ones (and their contents) untouched.
    """
    root = Path(project_root)
    root.mkdir(parents=True, exist_ok=True)

    for phase in V315_PHASE_DIRS:
        (root / phase).mkdir(parents=True, exist_ok=True)
    for phase in V317_NEW_PHASE_DIRS:
        (root / phase).mkdir(parents=True, exist_ok=True)
    for parent, subs in V317_NEW_SUBDIRS.items():
        for sub in subs:
            (root / parent / sub).mkdir(parents=True, exist_ok=True)
    return root
